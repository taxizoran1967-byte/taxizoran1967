"""
Taksi App - licna aplikacija za taksistu
Kalkulator cene, evidencija voznji, dnevni/mesecni izvestaj zarade.
"""

import os
import sys
import re
import json
import math
import threading
import traceback
import urllib.request
import urllib.parse
import webbrowser
import ssl

try:
    import certifi
    SSL_KONTEKST = ssl.create_default_context(cafile=certifi.where())
except Exception:
    # Ako certifi nije instaliran, koristimo podrazumevani kontekst
    # (moze i dalje da baci istu gresku, ali app nece pući ovde).
    SSL_KONTEKST = ssl.create_default_context()

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.properties import StringProperty, BooleanProperty
from datetime import datetime, timedelta

import database as db

try:
    from plyer import gps
except Exception:
    gps = None

# ========================
# TARIFE (iste kao u Telegram botu) - podrazumevane vrednosti
# Stvarne, trenutno vazece cene se cuvaju u cene.json i mogu
# se menjati direktno u aplikaciji (Podesavanja -> Cene / Tarife).
# ========================
DEFAULT_TARIFE = {
    "Osnovna (07-22h)": 80,
    "Nocna (22-07h)": 100,
    "Vikend": 90,
    "Aerodromski transfer": 120,
}
DEFAULT_START_FEE = 200


class CenePodesavanja:
    """Drzi trenutno vazece cene tarifa, start taksu i status nocne
    tarife, cuva ih u cene.json unutar interne memorije aplikacije."""

    def __init__(self):
        self.tarife = dict(DEFAULT_TARIFE)
        self.start_fee = DEFAULT_START_FEE
        self.nocna_aktivna = False

    def _putanja(self, user_data_dir):
        return os.path.join(user_data_dir, "cene.json")

    def ucitaj(self, user_data_dir):
        putanja = self._putanja(user_data_dir)
        try:
            with open(putanja, "r", encoding="utf-8") as f:
                podaci = json.load(f)
            ucitane_tarife = podaci.get("tarife", {})
            for naziv in self.tarife:
                if naziv in ucitane_tarife:
                    self.tarife[naziv] = float(ucitane_tarife[naziv])
            self.start_fee = float(podaci.get("start_fee", DEFAULT_START_FEE))
            self.nocna_aktivna = bool(podaci.get("nocna_aktivna", False))
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            pass

    def sacuvaj(self, user_data_dir):
        putanja = self._putanja(user_data_dir)
        podaci = {
            "tarife": self.tarife,
            "start_fee": self.start_fee,
            "nocna_aktivna": self.nocna_aktivna,
        }
        with open(putanja, "w", encoding="utf-8") as f:
            json.dump(podaci, f, ensure_ascii=False, indent=2)


class JsonLog:
    """Jednostavna lista stavki (npr. unosi goriva ili servisa) koja
    se cuva u sopstvenom .json fajlu - odvojeno od baze i od cena,
    tako da ne moze doci u sukob sa ostalim delovima aplikacije."""

    def __init__(self, filename):
        self.filename = filename
        self.stavke = []

    def _putanja(self, user_data_dir):
        return os.path.join(user_data_dir, self.filename)

    def ucitaj(self, user_data_dir):
        try:
            with open(self._putanja(user_data_dir), "r", encoding="utf-8") as f:
                self.stavke = json.load(f)
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            self.stavke = []

    def sacuvaj(self, user_data_dir):
        with open(self._putanja(user_data_dir), "w", encoding="utf-8") as f:
            json.dump(self.stavke, f, ensure_ascii=False, indent=2)

    def dodaj(self, user_data_dir, stavka):
        novi_id = max((s["id"] for s in self.stavke), default=0) + 1
        stavka["id"] = novi_id
        self.stavke.insert(0, stavka)
        self.sacuvaj(user_data_dir)
        return novi_id

    def azuriraj(self, user_data_dir, stavka_id, nova_stavka):
        nova_stavka["id"] = stavka_id
        for i, s in enumerate(self.stavke):
            if s["id"] == stavka_id:
                self.stavke[i] = nova_stavka
                break
        self.sacuvaj(user_data_dir)

    def nadji(self, stavka_id):
        for s in self.stavke:
            if s["id"] == stavka_id:
                return s
        return None

    def obrisi(self, user_data_dir, stavka_id):
        self.stavke = [s for s in self.stavke if s["id"] != stavka_id]
        self.sacuvaj(user_data_dir)


CENE = CenePodesavanja()
GORIVO = JsonLog("gorivo.json")
SERVIS = JsonLog("servis.json")


class ApiPodesavanja:
    """Cuva Google Geocoding API kljuc, unet direktno u aplikaciji
    (Podesavanja -> Google API), bez potrebe za build-om da bi se
    izmenio ili dodao."""

    def __init__(self):
        self.google_kljuc = ""

    def _putanja(self, user_data_dir):
        return os.path.join(user_data_dir, "api.json")

    def ucitaj(self, user_data_dir):
        try:
            with open(self._putanja(user_data_dir), "r", encoding="utf-8") as f:
                podaci = json.load(f)
            self.google_kljuc = podaci.get("google_kljuc", "")
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            pass

    def sacuvaj(self, user_data_dir):
        podaci = {"google_kljuc": self.google_kljuc}
        with open(self._putanja(user_data_dir), "w", encoding="utf-8") as f:
            json.dump(podaci, f, ensure_ascii=False, indent=2)


API = ApiPodesavanja()


class VozacPodesavanja:
    """Cuva podatke o vozacu - ime, telefon, broj licence, registarske
    tablice i vozilo. Koristi se za prikaz u app-u i u zaglavlju PDF
    mesecnog izvestaja."""

    def __init__(self):
        self.ime_prezime = ""
        self.telefon = ""
        self.broj_licence = ""
        self.tablice = ""
        self.vozilo = ""

    def _putanja(self, user_data_dir):
        return os.path.join(user_data_dir, "vozac.json")

    def ucitaj(self, user_data_dir):
        try:
            with open(self._putanja(user_data_dir), "r", encoding="utf-8") as f:
                podaci = json.load(f)
            self.ime_prezime = podaci.get("ime_prezime", "")
            self.telefon = podaci.get("telefon", "")
            self.broj_licence = podaci.get("broj_licence", "")
            self.tablice = podaci.get("tablice", "")
            self.vozilo = podaci.get("vozilo", "")
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            pass

    def sacuvaj(self, user_data_dir):
        podaci = {
            "ime_prezime": self.ime_prezime,
            "telefon": self.telefon,
            "broj_licence": self.broj_licence,
            "tablice": self.tablice,
            "vozilo": self.vozilo,
        }
        with open(self._putanja(user_data_dir), "w", encoding="utf-8") as f:
            json.dump(podaci, f, ensure_ascii=False, indent=2)


VOZAC = VozacPodesavanja()


class KursPodesavanja:
    """Drzi izabranu valutu za prikaz (RSD ili EUR) i poslednji
    povuceni kurs evro->dinar. Kurs se povlaci sa besplatnog,
    javnog servisa (exchangerate-api.com, open pristup, bez
    kljuca) najvise jednom dnevno - ne zove se internet svaki put
    kad se otvori ekran, nego samo ako je poslednji kurs stariji
    od danas.
    """

    KURS_URL = "https://open.er-api.com/v6/latest/EUR"

    def __init__(self):
        self.valuta = "RSD"          # "RSD" ili "EUR"
        self.kurs_eur_rsd = None     # koliko dinara je 1 evro
        self.datum_kursa = ""        # kad je kurs poslednji put povucen

    def _putanja(self, user_data_dir):
        return os.path.join(user_data_dir, "kurs.json")

    def ucitaj(self, user_data_dir):
        try:
            with open(self._putanja(user_data_dir), "r", encoding="utf-8") as f:
                podaci = json.load(f)
            self.valuta = podaci.get("valuta", "RSD")
            self.kurs_eur_rsd = podaci.get("kurs_eur_rsd")
            self.datum_kursa = podaci.get("datum_kursa", "")
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            pass

    def sacuvaj(self, user_data_dir):
        podaci = {
            "valuta": self.valuta,
            "kurs_eur_rsd": self.kurs_eur_rsd,
            "datum_kursa": self.datum_kursa,
        }
        with open(self._putanja(user_data_dir), "w", encoding="utf-8") as f:
            json.dump(podaci, f, ensure_ascii=False, indent=2)

    def osvezi_ako_treba(self, user_data_dir, prinudno=False):
        """Povlaci svez kurs sa interneta samo ako danas jos nije
        povucen (ili ako je prinudno=True, npr. korisnik rucno
        klikne 'Osvezi kurs'). Ako internet ne radi, tiho zadrzava
        stari kurs i ne baca gresku dalje.
        Vraca (uspeh: bool, poruka_greske ili None).
        """
        danas = datetime.now().strftime("%Y-%m-%d")
        if not prinudno and self.datum_kursa == danas and self.kurs_eur_rsd:
            return True, None

        try:
            req = urllib.request.Request(
                self.KURS_URL,
                headers={"User-Agent": "TaksiApp/1.0"},
            )
            with urllib.request.urlopen(req, timeout=8, context=SSL_KONTEKST) as resp:
                podaci = json.loads(resp.read().decode("utf-8"))
            novi_kurs = podaci.get("rates", {}).get("RSD")
            if not novi_kurs:
                return False, "Kurs RSD nije pronadjen u odgovoru servisa."
            self.kurs_eur_rsd = float(novi_kurs)
            self.datum_kursa = danas
            self.sacuvaj(user_data_dir)
            return True, None
        except Exception as e:
            return False, str(e)


KURS = KursPodesavanja()


def formatiraj_cenu(iznos_rsd):
    """Pretvara iznos (koji se u bazi/racunici uvek drzi u dinarima)
    u tekst za prikaz - u dinarima ili u evrima, zavisno od toga sta
    je korisnik izabrao u Podesavanja -> Valuta.
    """
    try:
        if KURS.valuta == "EUR" and KURS.kurs_eur_rsd:
            eur = iznos_rsd / KURS.kurs_eur_rsd
            return f"{eur:.2f} EUR"
    except Exception:
        pass
    return f"{iznos_rsd:.0f} RSD"


# ============================================================
# BACKUP - trajno cuvanje voznji van aplikacije (prezivi
# deinstalaciju i promenu telefona)
# ============================================================

BACKUP_FOLDER_NAZIV = "TaksiApp"
BACKUP_FAJL_NAZIV = "backup_taksi.json"


def _putanja_backup_foldera():
    """Vraca putanju do JAVNOG foldera 'Preuzimanja/TaksiApp' na
    telefonu - to je fiksno, uvek isto mesto, van same aplikacije,
    pa ostaje na telefonu i posle deinstalacije app-a.
    Van Android-a (npr. ovde na racunaru radi testiranja) vraca
    obican lokalni folder.
    """
    try:
        from jnius import autoclass
        Environment = autoclass("android.os.Environment")
        javni_download = Environment.getExternalStoragePublicDirectory(
            Environment.DIRECTORY_DOWNLOADS
        ).getAbsolutePath()
        return os.path.join(javni_download, BACKUP_FOLDER_NAZIV)
    except Exception:
        return os.path.join(os.path.expanduser("~"), BACKUP_FOLDER_NAZIV)


def _ima_dozvolu_svi_fajlovi():
    """Proverava da li app ima Android-ovu dozvolu 'pristup svim
    fajlovima' (potrebno da bi se pisalo van app-a, u Preuzimanja)."""
    try:
        from jnius import autoclass
        Environment = autoclass("android.os.Environment")
        return bool(Environment.isExternalStorageManager())
    except Exception:
        return True  # nije Android (desktop test) - ne blokiraj


def _zatrazi_dozvolu_svi_fajlovi():
    """Otvara Android-ovo sistemsko podesavanje gde korisnik rucno
    ukljuci 'Dozvoli pristup svim fajlovima' za ovu app - ovo Android
    trazi da bude rucno uradjeno u Podesavanjima, ne moze se
    automatski odobriti kao obicna dozvola."""
    try:
        from jnius import autoclass
        from android import mActivity
        Intent = autoclass("android.content.Intent")
        Settings = autoclass("android.provider.Settings")
        Uri = autoclass("android.net.Uri")
        intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
        uri = Uri.parse("package:" + mActivity.getPackageName())
        intent.setData(uri)
        mActivity.startActivity(intent)
    except Exception:
        pass


# ============================================================
# PDF IZVESTAJ - mesecni izvestaj sa svim voznjama, tabelarno
# ============================================================

_PDF_FONT_REGISTROVAN = False


def _registruj_font_za_pdf():
    """DejaVuSans font ima sva nasa slova (c c s d z), za razliku od
    podrazumevanih PDF fontova koji ne prikazuju kvacice ispravno.
    Registruje se samo jednom po pokretanju app-a."""
    global _PDF_FONT_REGISTROVAN
    if _PDF_FONT_REGISTROVAN:
        return
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont("DejaVuSans", "assets/fonts/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", "assets/fonts/DejaVuSans-Bold.ttf"))
    _PDF_FONT_REGISTROVAN = True


def generisi_mesecni_pdf(godina_mesec_str, putanja_fajla):
    """Pravi PDF tabelu sa svim voznjama za dati mesec (format
    'GGGG-MM'): redni broj, datum, vreme polaska/dolaska, adrese,
    cena - i na kraju ukupan broj voznji i ukupnu zaradu.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import ParagraphStyle

    _registruj_font_za_pdf()

    voznje = db.voznje_za_mesec(godina_mesec_str)
    broj, prihod, km = db.zbir_voznji(voznje)

    doc = SimpleDocTemplate(
        putanja_fajla,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"Izvestaj {godina_mesec_str}",
    )

    stil_celija = ParagraphStyle(
        "celija", fontName="DejaVuSans", fontSize=8.5, leading=11,
    )
    stil_naslov = ParagraphStyle(
        "naslov", fontName="DejaVuSans-Bold", fontSize=16, leading=20,
    )
    stil_zaglavlje = ParagraphStyle(
        "zaglavlje", fontName="DejaVuSans-Bold", fontSize=8.5, leading=11,
        textColor=colors.white,
    )
    stil_zbir = ParagraphStyle(
        "zbir", fontName="DejaVuSans-Bold", fontSize=12, leading=16,
    )
    stil_vozac = ParagraphStyle(
        "vozac", fontName="DejaVuSans", fontSize=10, leading=14,
    )

    elementi = []
    elementi.append(Paragraph(f"Mesecni izvestaj - {godina_mesec_str}", stil_naslov))

    linije_vozaca = []
    if VOZAC.ime_prezime:
        linije_vozaca.append(f"Vozac: {VOZAC.ime_prezime}")
    if VOZAC.telefon:
        linije_vozaca.append(f"Telefon: {VOZAC.telefon}")
    if VOZAC.broj_licence:
        linije_vozaca.append(f"Licenca: {VOZAC.broj_licence}")
    if VOZAC.vozilo:
        linije_vozaca.append(f"Vozilo: {VOZAC.vozilo}")
    if VOZAC.tablice:
        linije_vozaca.append(f"Tablice: {VOZAC.tablice}")

    if linije_vozaca:
        elementi.append(Spacer(1, 3 * mm))
        elementi.append(Paragraph(" &nbsp;|&nbsp; ".join(linije_vozaca), stil_vozac))

    elementi.append(Spacer(1, 8 * mm))

    zaglavlje = [
        Paragraph("R.br.", stil_zaglavlje),
        Paragraph("Datum", stil_zaglavlje),
        Paragraph("Pocetak", stil_zaglavlje),
        Paragraph("Kraj", stil_zaglavlje),
        Paragraph("Adresa polaska", stil_zaglavlje),
        Paragraph("Adresa dolaska", stil_zaglavlje),
        Paragraph("Cena", stil_zaglavlje),
    ]
    podaci_tabele = [zaglavlje]

    for i, v in enumerate(voznje, start=1):
        vreme_pocetka = v["vreme_pocetka"] if ("vreme_pocetka" in v.keys() and v["vreme_pocetka"]) else "-"
        red = [
            Paragraph(str(i), stil_celija),
            Paragraph(v["datum"], stil_celija),
            Paragraph(vreme_pocetka, stil_celija),
            Paragraph(v["vreme"], stil_celija),
            Paragraph(v["od_adresa"] or "-", stil_celija),
            Paragraph(v["do_adresa"] or "-", stil_celija),
            Paragraph(formatiraj_cenu(v["ukupna_cena"]), stil_celija),
        ]
        podaci_tabele.append(red)

    # sirine kolona u mm - A4 sirina 210mm, minus margine 2x15mm = 180mm dostupno
    sirine = [13 * mm, 23 * mm, 17 * mm, 15 * mm, 42 * mm, 42 * mm, 21 * mm]

    tabela = Table(podaci_tabele, colWidths=sirine, repeatRows=1)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3a3560")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f5")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementi.append(tabela)
    elementi.append(Spacer(1, 8 * mm))

    elementi.append(Paragraph(f"Ukupan broj voznji: {broj}", stil_zbir))
    elementi.append(Paragraph(f"Ukupno predjeno: {km:.1f} km", stil_zbir))
    elementi.append(Paragraph(f"Ukupna zarada za mesec: {formatiraj_cenu(prihod)}", stil_zbir))

    doc.build(elementi)





# Kad korisnik klikne "Izmeni" na voznji u Evidenciji, podaci te
# voznje se privremeno stave ovde da bi ih Kalkulator ekran
# pokupio i popunio formu za ispravku.
EDIT_VOZNJA = None


# ========================
# GPS VOZNJA - pomocne funkcije i cuvanje stanja aktivne voznje
# ========================

def haversine_km(lat1, lon1, lat2, lon2):
    """Udaljenost izmedju dve GPS tacke u km (haversine formula)."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def reverse_geocode(lat, lon, callback, dijagnoza_callback=None):
    """Pretvara GPS koordinate u adresu. Ako je unet Google API kljuc
    (Podesavanja -> Google API), koristi Google Geocoding (tacnije).
    Ako kljuca nema, ili Google poziv ne uspe, koristi besplatan
    OpenStreetMap Nominatim kao rezervu. Radi u pozadinskoj niti da
    ne blokira interfejs; rezultat vraca preko callback-a na glavnoj
    niti. Ako je prosledjen dijagnoza_callback, saljepravi razlog
    google/osm neuspeha (za prikaz na ekranu, radi resavanja problema)."""

    def _osm_pokusaj(dnevnik):
        try:
            url = (
                "https://nominatim.openstreetmap.org/reverse?format=json"
                f"&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
            )
            req = urllib.request.Request(
                url, headers={"User-Agent": "TaksiApp/1.0"}
            )
            with urllib.request.urlopen(req, timeout=8, context=SSL_KONTEKST) as resp:
                podaci = json.loads(resp.read().decode("utf-8"))
            if podaci.get("display_name"):
                return podaci["display_name"]
            dnevnik.append(f"OSM: nema display_name u odgovoru ({podaci})")
        except Exception as e:
            dnevnik.append(f"OSM greska: {e}")
        return None

    def _google_pokusaj(kljuc, dnevnik):
        try:
            url = (
                "https://maps.googleapis.com/maps/api/geocode/json"
                f"?latlng={lat},{lon}&key={kljuc}&language=sr"
            )
            with urllib.request.urlopen(url, timeout=8, context=SSL_KONTEKST) as resp:
                podaci = json.loads(resp.read().decode("utf-8"))
            if podaci.get("status") == "OK" and podaci.get("results"):
                return podaci["results"][0]["formatted_address"]
            dnevnik.append(
                f"Google status: {podaci.get('status')} - "
                f"{podaci.get('error_message', '(bez poruke)')}"
            )
        except Exception as e:
            dnevnik.append(f"Google greska: {e}")
        return None

    def posao():
        dnevnik = []
        adresa = None
        kljuc = API.google_kljuc.strip()
        if kljuc:
            adresa = _google_pokusaj(kljuc, dnevnik)
        if not adresa:
            adresa = _osm_pokusaj(dnevnik)
        if not adresa:
            adresa = "Adresa nije dostupna"
        Clock.schedule_once(lambda dt: callback(adresa))
        if dijagnoza_callback and dnevnik:
            tekst = "\n".join(dnevnik)
            Clock.schedule_once(lambda dt: dijagnoza_callback(tekst))

    threading.Thread(target=posao, daemon=True).start()


class AktivnaVoznjaState:
    """Cuva stanje trenutno aktivne GPS voznje u fajl, da se ne
    izgubi ako korisnik zatvori i ponovo otvori aplikaciju."""

    def __init__(self):
        self.aktivna = False
        self.pocetak_vreme = None
        self.pocetak_lat = None
        self.pocetak_lon = None
        self.pocetak_adresa = ""
        self.zadnja_lat = None
        self.zadnja_lon = None
        self.km = 0.0

    def _putanja(self, user_data_dir):
        return os.path.join(user_data_dir, "aktivna_voznja.json")

    def ucitaj(self, user_data_dir):
        try:
            with open(self._putanja(user_data_dir), "r", encoding="utf-8") as f:
                podaci = json.load(f)
            self.aktivna = podaci.get("aktivna", False)
            self.pocetak_vreme = podaci.get("pocetak_vreme")
            self.pocetak_lat = podaci.get("pocetak_lat")
            self.pocetak_lon = podaci.get("pocetak_lon")
            self.pocetak_adresa = podaci.get("pocetak_adresa", "")
            self.zadnja_lat = podaci.get("zadnja_lat")
            self.zadnja_lon = podaci.get("zadnja_lon")
            self.km = podaci.get("km", 0.0)
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            pass

    def sacuvaj(self, user_data_dir):
        podaci = {
            "aktivna": self.aktivna,
            "pocetak_vreme": self.pocetak_vreme,
            "pocetak_lat": self.pocetak_lat,
            "pocetak_lon": self.pocetak_lon,
            "pocetak_adresa": self.pocetak_adresa,
            "zadnja_lat": self.zadnja_lat,
            "zadnja_lon": self.zadnja_lon,
            "km": self.km,
        }
        with open(self._putanja(user_data_dir), "w", encoding="utf-8") as f:
            json.dump(podaci, f, ensure_ascii=False, indent=2)

    def resetuj(self, user_data_dir):
        self.__init__()
        self.sacuvaj(user_data_dir)


AKTIVNA_VOZNJA = AktivnaVoznjaState()


def napravi_red_liste(opis_markup, tint, boja_teksta, dugmad):
    """Pravi jedan red u listi (vožnja/gorivo/servis) sa tekstom koji
    se PRAVILNO prelama u svom prostoru (ne prelazi preko dugmadi) i
    karticom koja se sama proširi po visini ako je tekst duzi.

    dugmad: lista (label_text, tint, text_color, callback) torki.
    """
    from kivy.factory import Factory
    from kivy.metrics import dp
    from kivy.uix.boxlayout import BoxLayout as _BoxLayout

    red = Factory.PastelCard(
        orientation="horizontal",
        size_hint_y=None,
        padding=dp(12),
        spacing=dp(10),
        tint=tint,
    )

    labela = Label(
        text=opis_markup,
        markup=True,
        halign="left",
        valign="top",
        color=boja_teksta,
        size_hint_x=1,
        size_hint_y=None,
    )

    def _osvezi_velicinu(*_a):
        labela.text_size = (labela.width, None)
        labela.height = labela.texture_size[1]
        red.height = max(labela.height + dp(24), dp(64))

    labela.bind(width=_osvezi_velicinu, texture_size=_osvezi_velicinu)
    red.add_widget(labela)

    dugmad_kolona = _BoxLayout(
        orientation="vertical",
        size_hint_x=None,
        width=dp(84),
        spacing=dp(6),
    )
    for label_text, dtint, dtext_color, callback in dugmad:
        dugme = Factory.RoundButton(
            label_text=label_text,
            tint=dtint,
            text_color=dtext_color,
            size_hint_y=None,
            height=dp(38),
        )
        dugme.bind(on_release=callback)
        dugmad_kolona.add_widget(dugme)

    red.add_widget(dugmad_kolona)
    return red



BACKGROUND_IMG = "assets/backgrounds/background.png"

KV = """
#:import dp kivy.metrics.dp

ScreenManager:
    HomeScreen:
    KalkulatorScreen:
    EvidencijaScreen:
    IzvestajScreen:
    PodesavanjaScreen:
    CenovnikScreen:
    NocnaTarifaScreen:
    GorivoScreen:
    ServisScreen:
    GpsVoznjaScreen:
    NavigacijaScreen:
    GoogleApiScreen:
    ProfilScreen:
    ValutaScreen:
    BackupScreen:
    IzvozPdfScreen:
    PlaceholderScreen:
        name: "grafik"
        naslov: "Grafik zarade"
    PlaceholderScreen:
        name: "poziv"
        naslov: "Poziv / Dispecer"

# ============================================================
# ZAJEDNICKI STIL - pastelne kartice, zaobljeni uglovi, tipografija
# ============================================================

<ScreenRoot@BoxLayout>:
    orientation: "vertical"
    padding: dp(18)
    spacing: dp(16)
    canvas.before:
        Rectangle:
            source: app.background_img
            pos: self.pos
            size: self.size
        Color:
            rgba: 0.04, 0.03, 0.09, 0.35
        Rectangle:
            pos: self.pos
            size: self.size

<TitleLabel@Label>:
    size_hint_y: None
    height: dp(42)
    font_size: '24sp'
    bold: True
    color: 1, 1, 1, 1
    halign: "left"
    text_size: self.size
    valign: "middle"

<FieldLabel@Label>:
    size_hint_y: None
    height: max(self.texture_size[1] + dp(6), dp(22))
    halign: "left"
    valign: "middle"
    text_size: self.width, None
    font_size: '14sp'
    color: 0.85, 0.85, 0.95, 1

<PastelCard@BoxLayout>:
    tint: (0.40, 0.38, 0.52, 0.92)
    canvas.before:
        Color:
            rgba: 0, 0, 0, 0.14
        RoundedRectangle:
            pos: self.x, self.y - dp(3)
            size: self.size
            radius: [dp(20)]
        Color:
            rgba: root.tint
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(20)]

<RoundButton@ButtonBehavior+BoxLayout>:
    tint: (0.36, 0.46, 0.64, 1)
    text_color: 0.95, 0.96, 1, 1
    label_text: ""
    font_size: '15sp'
    opacity: 0.4 if self.disabled else 1
    canvas.before:
        Color:
            rgba: root.tint
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(16)]
    Label:
        text: root.label_text
        color: root.text_color
        bold: True
        font_size: root.font_size
        text_size: self.width - dp(4), self.height
        halign: 'center'
        valign: 'middle'

<NavBar@BoxLayout>:
    size_hint_y: None
    height: dp(46)
    spacing: dp(10)

<MenuButton>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(72)
    spacing: dp(16)
    padding: dp(12)
    canvas.before:
        Color:
            rgba: 0, 0, 0, 0.16
        RoundedRectangle:
            pos: self.x, self.y - dp(3)
            size: self.size
            radius: [dp(22)]
        Color:
            rgba: 0.40, 0.38, 0.52, 0.90
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(22)]
    BoxLayout:
        size_hint_x: None
        width: dp(48)
        canvas.before:
            StencilPush
            Ellipse:
                pos: self.pos
                size: self.size
            StencilUse
        canvas.after:
            StencilUnUse
            Ellipse:
                pos: self.pos
                size: self.size
            StencilPop
        Image:
            source: root.icon_src
            allow_stretch: True
            keep_ratio: False
    Label:
        text: root.tekst
        font_size: '17sp'
        bold: True
        color: 0.94, 0.93, 0.98, 1
        halign: "left"
        valign: "middle"
        text_size: self.size

<PastelTextInput@TextInput>:
    background_color: 0.80, 0.79, 0.88, 0.95
    foreground_color: 0.12, 0.12, 0.22, 1
    hint_text_color: 0.55, 0.55, 0.65, 1
    cursor_color: 0.3, 0.3, 0.7, 1
    padding: dp(14), dp(12)
    size_hint_y: None
    height: dp(48)
    multiline: False

# ============================================================
# POCETNI EKRAN
# ============================================================

<HomeScreen>:
    name: "home"
    ScreenRoot:

        TitleLabel:
            text: "Taksi App"
            font_size: '28sp'
            height: dp(48)

        ScrollView:
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(14)
                padding: dp(2), dp(4)

                MenuButton:
                    icon_src: "assets/icons/start_ride.png"
                    tekst: "GPS voznja (auto)"
                    on_release: app.root.current = "gps_voznja"

                MenuButton:
                    icon_src: "assets/icons/end_ride.png"
                    tekst: "Pocetak voznje (rucno)"
                    on_release: app.root.current = "kalkulator"

                MenuButton:
                    icon_src: "assets/icons/history.png"
                    tekst: "Istorija voznji"
                    on_release: app.root.current = "evidencija"

                MenuButton:
                    icon_src: "assets/icons/daily_report.png"
                    tekst: "Izvestaj"
                    on_release: app.root.current = "izvestaj"

                MenuButton:
                    icon_src: "assets/icons/profil.png"
                    tekst: "Profil vozaca"
                    on_release: app.root.current = "profil"

                MenuButton:
                    icon_src: "assets/icons/settings.png"
                    tekst: "Podesavanja"
                    on_release: app.root.current = "podesavanja"

# ============================================================
# KALKULATOR
# ============================================================

<KalkulatorScreen>:
    name: "kalkulator"
    ScreenRoot:

        TitleLabel:
            text: "Kalkulator voznje"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                font_size: '13sp'
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Evidencija"
                tint: 0.36, 0.46, 0.64, 1
                font_size: '13sp'
                on_release: root.manager.current = "evidencija"
            RoundButton:
                label_text: "Izvestaj"
                tint: 0.36, 0.46, 0.64, 1
                font_size: '13sp'
                on_release: root.manager.current = "izvestaj"

        ScrollView:
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: dp(4)

                FieldLabel:
                    text: "Tarifa"

                Spinner:
                    id: spinner_tarifa
                    text: root.tarife_lista[0]
                    values: root.tarife_lista
                    size_hint_y: None
                    height: dp(48)
                    background_color: 0.78, 0.80, 0.90, 1
                    color: 0.12, 0.12, 0.24, 1
                    on_text: root.izracunaj()

                FieldLabel:
                    text: "Kilometraza (km)"

                PastelTextInput:
                    id: input_km
                    hint_text: "npr. 8.5"
                    input_filter: "float"
                    on_text: root.izracunaj()

                FieldLabel:
                    text: "Od (opciono)"

                PastelTextInput:
                    id: input_od
                    hint_text: "adresa polazista"

                FieldLabel:
                    text: "Do (opciono)"

                PastelTextInput:
                    id: input_do
                    hint_text: "adresa odredista"

                FieldLabel:
                    text: "Napomena (opciono)"

                PastelTextInput:
                    id: input_napomena
                    hint_text: "npr. cekanje, prtljag..."

                PastelCard:
                    tint: 0.28, 0.48, 0.34, 0.92
                    size_hint_y: None
                    height: dp(96)
                    padding: dp(14)
                    Label:
                        id: label_cena
                        text: root.tekst_cene
                        font_size: '20sp'
                        bold: True
                        color: 0.90, 1, 0.92, 1
                        halign: "center"
                        valign: "middle"
                        text_size: self.size

                RoundButton:
                    label_text: root.dugme_tekst
                    tint: 0.30, 0.52, 0.36, 1
                    text_color: 0.92, 1, 0.94, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.sacuvaj_voznju()

# ============================================================
# EVIDENCIJA
# ============================================================

<EvidencijaScreen>:
    name: "evidencija"
    ScreenRoot:

        TitleLabel:
            text: "Evidencija voznji"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                font_size: '13sp'
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Kalkulator"
                tint: 0.36, 0.46, 0.64, 1
                font_size: '13sp'
                on_release: root.manager.current = "kalkulator"
            RoundButton:
                label_text: "Izvestaj"
                tint: 0.36, 0.46, 0.64, 1
                font_size: '13sp'
                on_release: root.manager.current = "izvestaj"

        ScrollView:
            BoxLayout:
                id: lista_voznji
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(10)
                padding: dp(4)

# ============================================================
# IZVESTAJ
# ============================================================

<IzvestajScreen>:
    name: "izvestaj"
    ScreenRoot:

        TitleLabel:
            text: "Izvestaj zarade"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                font_size: '11sp'
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Kalkulator"
                tint: 0.36, 0.46, 0.64, 1
                font_size: '11sp'
                on_release: root.manager.current = "kalkulator"
            RoundButton:
                label_text: "Evidencija"
                tint: 0.36, 0.46, 0.64, 1
                font_size: '11sp'
                on_release: root.manager.current = "evidencija"
            RoundButton:
                label_text: "Izvoz PDF"
                tint: 0.55, 0.38, 0.26, 1
                font_size: '11sp'
                on_release: root.manager.current = "izvoz_pdf"

        ScrollView:
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(10)
                padding: dp(2), dp(4)

                PastelCard:
                    orientation: "vertical"
                    tint: 0.55, 0.38, 0.26, 0.92
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(14)
                    Label:
                        id: label_danas
                        text: root.tekst_danas
                        font_size: '16sp'
                        halign: "left"
                        valign: "top"
                        size_hint_y: None
                        text_size: self.width, None
                        height: self.texture_size[1]
                        color: 1, 0.90, 0.80, 1

                FieldLabel:
                    text: "Voznje danas (pocetak - kraj, cena):"
                    size_hint_y: None
                    height: dp(28)

                BoxLayout:
                    id: lista_danas_voznje
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(8)

                PastelCard:
                    orientation: "vertical"
                    tint: 0.26, 0.48, 0.44, 0.92
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(14)
                    Label:
                        id: label_nedelja
                        text: root.tekst_nedelja
                        font_size: '16sp'
                        halign: "left"
                        valign: "top"
                        size_hint_y: None
                        text_size: self.width, None
                        height: self.texture_size[1]
                        color: 0.86, 1, 0.96, 1

                PastelCard:
                    orientation: "vertical"
                    tint: 0.38, 0.32, 0.52, 0.92
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(14)
                    Label:
                        id: label_mesec
                        text: root.tekst_mesec
                        font_size: '16sp'
                        halign: "left"
                        valign: "top"
                        size_hint_y: None
                        text_size: self.width, None
                        height: self.texture_size[1]
                        color: 0.92, 0.88, 1, 1

# ============================================================
# PODESAVANJA
# ============================================================

<PodesavanjaScreen>:
    name: "podesavanja"
    ScreenRoot:

        TitleLabel:
            text: "Podesavanja"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"

        ScrollView:
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(14)
                padding: dp(2), dp(4)

                MenuButton:
                    icon_src: "assets/icons/earnings_chart.png"
                    tekst: "Grafik zarade"
                    on_release: app.root.current = "grafik"

                MenuButton:
                    icon_src: "assets/icons/navigation.png"
                    tekst: "Navigacija"
                    on_release: app.root.current = "navigacija"

                MenuButton:
                    icon_src: "assets/icons/night_tariff.png"
                    tekst: "Nocna tarifa"
                    on_release: app.root.current = "nocna_tarifa"

                MenuButton:
                    icon_src: "assets/icons/service.png"
                    tekst: "Servis vozila"
                    on_release: app.root.current = "servis"

                MenuButton:
                    icon_src: "assets/icons/fuel.png"
                    tekst: "Gorivo"
                    on_release: app.root.current = "gorivo"

                MenuButton:
                    icon_src: "assets/icons/weekly_report.png"
                    tekst: "Nedeljni izvestaj"
                    on_release: app.root.current = "izvestaj"

                MenuButton:
                    icon_src: "assets/icons/monthly_report.png"
                    tekst: "Mesecni izvestaj"
                    on_release: app.root.current = "izvestaj"

                MenuButton:
                    icon_src: "assets/icons/calculator.png"
                    tekst: "Kalkulator"
                    on_release: app.root.current = "kalkulator"

                MenuButton:
                    icon_src: "assets/icons/profil.png"
                    tekst: "Profil vozaca"
                    on_release: app.root.current = "profil"

                MenuButton:
                    icon_src: "assets/icons/poziv.png"
                    tekst: "Poziv / Dispecer"
                    on_release: app.root.current = "poziv"

                MenuButton:
                    icon_src: "assets/icons/settings.png"
                    tekst: "Cene / Tarife"
                    on_release: app.root.current = "cene"

                MenuButton:
                    icon_src: "assets/icons/settings.png"
                    tekst: "Google API"
                    on_release: app.root.current = "google_api"

                MenuButton:
                    icon_src: "assets/icons/settings.png"
                    tekst: "Valuta"
                    on_release: app.root.current = "valuta"

                MenuButton:
                    icon_src: "assets/icons/settings.png"
                    tekst: "Backup podataka"
                    on_release: app.root.current = "backup"

# ============================================================
# CENOVNIK - izmena cena tarifa i start takse
# ============================================================

<CenovnikScreen>:
    name: "cene"
    ScreenRoot:

        TitleLabel:
            text: "Cene / Tarife"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Podesavanja"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "podesavanja"

        ScrollView:
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: dp(4)

                FieldLabel:
                    text: "Start taksa (RSD)"

                PastelTextInput:
                    id: input_start
                    input_filter: "float"

                FieldLabel:
                    text: "Osnovna (07-22h) - cena po km"

                PastelTextInput:
                    id: input_osnovna
                    input_filter: "float"

                FieldLabel:
                    text: "Nocna (22-07h) - cena po km"

                PastelTextInput:
                    id: input_nocna
                    input_filter: "float"

                FieldLabel:
                    text: "Vikend - cena po km"

                PastelTextInput:
                    id: input_vikend
                    input_filter: "float"

                FieldLabel:
                    text: "Aerodromski transfer - cena po km"

                PastelTextInput:
                    id: input_aerodromski
                    input_filter: "float"

                RoundButton:
                    label_text: "Sacuvaj cene"
                    tint: 0.30, 0.52, 0.36, 1
                    text_color: 0.92, 1, 0.94, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.sacuvaj_cene()

# ============================================================
# NOCNA TARIFA - prekidac
# ============================================================

<NocnaTarifaScreen>:
    name: "nocna_tarifa"
    ScreenRoot:

        TitleLabel:
            text: "Nocna tarifa"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Podesavanja"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "podesavanja"

        PastelCard:
            tint: 0.38, 0.32, 0.52, 0.92
            size_hint_y: None
            height: dp(74)
            padding: dp(14)
            Label:
                id: label_status
                text: root.tekst_status
                font_size: '18sp'
                bold: True
                color: 0.92, 0.88, 1, 1

        RoundButton:
            id: dugme_toggle
            label_text: root.tekst_dugme
            tint: root.tint_dugme
            text_color: 0.1, 0.1, 0.1, 1
            size_hint_y: None
            height: dp(52)
            on_release: root.promeni()

        FieldLabel:
            text: "Kada je ukljucena, kalkulator ce pri otvaranju automatski predloziti nocnu tarifu (i dalje mozes rucno da promenis tarifu za konkretnu voznju)."
            size_hint_y: None
            height: dp(60)
            text_size: self.width, None

        Widget:

# ============================================================
# GORIVO
# ============================================================

<GorivoScreen>:
    name: "gorivo"
    ScreenRoot:

        TitleLabel:
            text: "Gorivo"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Podesavanja"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "podesavanja"

        ScrollView:
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: dp(4)

                PastelCard:
                    tint: 0.55, 0.38, 0.26, 0.92
                    size_hint_y: None
                    height: dp(72)
                    padding: dp(12)
                    Label:
                        id: label_ukupno_gorivo
                        text: root.tekst_ukupno
                        font_size: '14sp'
                        bold: True
                        color: 1, 0.90, 0.80, 1

                FieldLabel:
                    text: "Vrsta goriva"

                Spinner:
                    id: spinner_tip_goriva
                    text: "Benzin"
                    values: ["Benzin", "TNG"]
                    size_hint_y: None
                    height: dp(48)
                    background_color: 0.78, 0.80, 0.90, 1
                    color: 0.12, 0.12, 0.24, 1

                FieldLabel:
                    text: "Kolicina (litara)"

                PastelTextInput:
                    id: input_litara
                    hint_text: "npr. 30"
                    input_filter: "float"

                FieldLabel:
                    text: "Cena (RSD)"

                PastelTextInput:
                    id: input_cena_goriva
                    hint_text: "npr. 3200"
                    input_filter: "float"

                FieldLabel:
                    text: "Napomena (opciono)"

                PastelTextInput:
                    id: input_napomena_gorivo
                    hint_text: "npr. NIS pumpa"

                RoundButton:
                    label_text: root.dugme_tekst
                    tint: 0.30, 0.52, 0.36, 1
                    text_color: 0.92, 1, 0.94, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.sacuvaj_gorivo()

                BoxLayout:
                    id: lista_gorivo
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(10)
                    padding: dp(4), dp(10)

# ============================================================
# SERVIS VOZILA
# ============================================================

<ServisScreen>:
    name: "servis"
    ScreenRoot:

        TitleLabel:
            text: "Servis vozila"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Podesavanja"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "podesavanja"

        ScrollView:
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: dp(4)

                PastelCard:
                    tint: 0.38, 0.32, 0.52, 0.92
                    size_hint_y: None
                    height: dp(56)
                    padding: dp(12)
                    Label:
                        id: label_ukupno_servis
                        text: root.tekst_ukupno
                        font_size: '15sp'
                        bold: True
                        color: 0.92, 0.88, 1, 1

                FieldLabel:
                    text: "Vrsta servisa"

                PastelTextInput:
                    id: input_vrsta
                    hint_text: "npr. zamena ulja"

                FieldLabel:
                    text: "Cena (RSD)"

                PastelTextInput:
                    id: input_cena_servisa
                    hint_text: "npr. 4500"
                    input_filter: "float"

                FieldLabel:
                    text: "Kilometraza (opciono)"

                PastelTextInput:
                    id: input_km_servis
                    hint_text: "npr. 152340"
                    input_filter: "float"

                FieldLabel:
                    text: "Napomena (opciono)"

                PastelTextInput:
                    id: input_napomena_servis
                    hint_text: "npr. ime servisa"

                RoundButton:
                    label_text: root.dugme_tekst
                    tint: 0.30, 0.52, 0.36, 1
                    text_color: 0.92, 1, 0.94, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.sacuvaj_servis()

                BoxLayout:
                    id: lista_servis
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(10)
                    padding: dp(4), dp(10)

# ============================================================
# GPS VOZNJA - automatsko pracenje
# ============================================================

<GpsVoznjaScreen>:
    name: "gps_voznja"
    ScreenRoot:

        TitleLabel:
            text: "GPS voznja"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Istorija"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "evidencija"

        ScrollView:
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: dp(4)

                PastelCard:
                    orientation: "vertical"
                    tint: 0.38, 0.32, 0.52, 0.92
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(14)
                    spacing: dp(4)
                    Label:
                        text: "POLAZAK"
                        font_size: '13sp'
                        bold: True
                        color: 0.78, 0.74, 0.92, 1
                        size_hint_y: None
                        height: dp(20)
                        halign: "left"
                        text_size: self.size
                    Label:
                        text: root.tekst_polazak
                        font_size: '15sp'
                        color: 0.94, 0.91, 1, 1
                        halign: "left"
                        valign: "top"
                        size_hint_y: None
                        text_size: self.width, None
                        height: self.texture_size[1]

                FieldLabel:
                    text: "Krajnja adresa (opciono - unesi je PRE 'Pocni voznju' da odmah krene Google navigacija)"

                PastelTextInput:
                    id: input_dolazak_rucno
                    hint_text: "npr. Nemanjina 4, Beograd"

                FieldLabel:
                    text: "Ostavi prazno da sve radi kao do sad - GPS sam nalazi i polaznu i krajnju adresu."
                    size_hint_y: None
                    height: dp(34)
                    text_size: self.width, None

                PastelCard:
                    tint: 0.28, 0.48, 0.34, 0.92
                    size_hint_y: None
                    height: dp(64)
                    padding: dp(14)
                    Label:
                        text: root.tekst_km
                        font_size: '20sp'
                        bold: True
                        color: 0.90, 1, 0.92, 1

                PastelCard:
                    tint: 0.55, 0.38, 0.26, 0.92
                    size_hint_y: None
                    height: dp(56)
                    padding: dp(14)
                    Label:
                        text: root.tekst_trajanje
                        font_size: '16sp'
                        bold: True
                        color: 1, 0.90, 0.80, 1

                PastelCard:
                    tint: 0.26, 0.40, 0.58, 0.92
                    size_hint_y: None
                    height: dp(64)
                    padding: dp(14)
                    Label:
                        text: root.tekst_cena
                        font_size: '20sp'
                        bold: True
                        color: 0.85, 0.92, 1, 1

                Label:
                    text: root.tekst_gps_status
                    size_hint_y: None
                    height: self.texture_size[1] + dp(10)
                    font_size: '13sp'
                    color: 0.85, 0.85, 0.95, 1
                    text_size: self.width, None

                Label:
                    text: root.tekst_dijagnoza
                    size_hint_y: None
                    height: self.texture_size[1] + dp(10)
                    font_size: '12sp'
                    color: 0.65, 0.85, 1, 1
                    text_size: self.width, None

                RoundButton:
                    id: dugme_start
                    label_text: "POCNI VOZNJU"
                    tint: 0.30, 0.52, 0.36, 1
                    text_color: 0.92, 1, 0.94, 1
                    size_hint_y: None
                    height: dp(56)
                    disabled: root.voznja_aktivna
                    on_release: root.pocni_voznju()

                RoundButton:
                    id: dugme_zavrsi
                    label_text: "ZAVRSI VOZNJU"
                    tint: 0.74, 0.28, 0.32, 1
                    text_color: 1, 1, 1, 1
                    size_hint_y: None
                    height: dp(56)
                    disabled: not root.voznja_aktivna
                    on_release: root.zavrsi_voznju()

# ============================================================
# NAVIGACIJA
# ============================================================

<NavigacijaScreen>:
    name: "navigacija"
    ScreenRoot:

        TitleLabel:
            text: "Navigacija"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Podesavanja"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "podesavanja"

        FieldLabel:
            text: "Odrediste (adresa ili naziv mesta)"

        PastelTextInput:
            id: input_odrediste
            hint_text: "npr. Terazije 5, Beograd"

        RoundButton:
            label_text: "Otvori navigaciju"
            tint: 0.36, 0.46, 0.64, 1
            text_color: 0.95, 0.96, 1, 1
            size_hint_y: None
            height: dp(52)
            on_release: root.otvori_navigaciju()

        FieldLabel:
            text: "Otvorice se Google Maps i navigacija ce automatski krenuti korak-po-korak ka unetoj adresi (nije potrebno rucno kliktati 'Kreni'). Polazna tacka je uvek trenutna GPS pozicija telefona u tom trenutku."
            size_hint_y: None
            height: dp(60)
            text_size: self.width, None

        Widget:

# ============================================================
# GOOGLE API - unos kljuca za tacnije adrese
# ============================================================

<GoogleApiScreen>:
    name: "google_api"
    ScreenRoot:

        TitleLabel:
            text: "Google API"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Podesavanja"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "podesavanja"

        FieldLabel:
            text: "Google Geocoding API kljuc (opciono - ako je prazno, koristi se besplatan OpenStreetMap)"

        PastelTextInput:
            id: input_google_kljuc
            hint_text: "npr. AIzaSy..."

        RoundButton:
            label_text: "Sacuvaj kljuc"
            tint: 0.30, 0.52, 0.36, 1
            text_color: 0.92, 1, 0.94, 1
            size_hint_y: None
            height: dp(52)
            on_release: root.sacuvaj_kljuc()

        FieldLabel:
            text: "Kljuc pravis na console.cloud.google.com -> APIs & Services -> Credentials, i ukljucuje se Geocoding API. Ako ostavis prazno, adrese se i dalje racunaju preko besplatnog OpenStreetMap servisa."
            size_hint_y: None
            height: dp(70)
            text_size: self.width, None

        Widget:

# ============================================================
# PROFIL VOZACA
# ============================================================

<ProfilScreen>:
    name: "profil"
    ScreenRoot:

        TitleLabel:
            text: "Profil vozaca"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"

        ScrollView:
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(8)
                padding: dp(2), dp(4)

                FieldLabel:
                    text: "Ime i prezime"

                PastelTextInput:
                    id: input_ime
                    hint_text: "npr. Petar Petrovic"

                FieldLabel:
                    text: "Telefon"

                PastelTextInput:
                    id: input_telefon
                    hint_text: "npr. 065 123 4567"

                FieldLabel:
                    text: "Broj licence / dozvole za taksi"

                PastelTextInput:
                    id: input_licenca
                    hint_text: "npr. TX-00123"

                FieldLabel:
                    text: "Registarske tablice"

                PastelTextInput:
                    id: input_tablice
                    hint_text: "npr. BG-1234-AB"

                FieldLabel:
                    text: "Vozilo (marka i model)"

                PastelTextInput:
                    id: input_vozilo
                    hint_text: "npr. Skoda Octavia"

                RoundButton:
                    label_text: "Sacuvaj profil"
                    tint: 0.30, 0.52, 0.36, 1
                    text_color: 1, 1, 1, 1
                    size_hint_y: None
                    height: dp(56)
                    on_release: root.sacuvaj_profil()

                FieldLabel:
                    text: "Ovi podaci se prikazuju u zaglavlju PDF mesecnog izvestaja (Izvestaj -> Izvoz PDF)."
                    size_hint_y: None
                    height: dp(60)
                    text_size: self.width, None

        Widget:

# ============================================================
# VALUTA - izbor prikaza cena (RSD ili EUR) i kurs
# ============================================================

<ValutaScreen>:
    name: "valuta"
    ScreenRoot:

        TitleLabel:
            text: "Valuta"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Podesavanja"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "podesavanja"

        FieldLabel:
            text: "Cene se u aplikaciji uvek racunaju i cuvaju u dinarima. Ovde bira se samo u kojoj valuti da se PRIKAZUJU."

        BoxLayout:
            size_hint_y: None
            height: dp(80)
            padding: dp(10)
            canvas.before:
                Color:
                    rgba: 0.30, 0.29, 0.42, 0.85
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(14)]
            Label:
                text: root.tekst_kurs
                color: 1, 1, 1, 1
                halign: "center"
                valign: "middle"
                text_size: self.size

        BoxLayout:
            size_hint_y: None
            height: dp(56)
            spacing: dp(10)

            RoundButton:
                label_text: "Prikazuj u RSD"
                tint: (0.30, 0.52, 0.36, 1) if root.valuta_izbor == "RSD" else (0.36, 0.35, 0.48, 1)
                text_color: 0.95, 1, 0.96, 1
                on_release: root.izaberi_valutu("RSD")

            RoundButton:
                label_text: "Prikazuj u EUR"
                tint: (0.30, 0.52, 0.36, 1) if root.valuta_izbor == "EUR" else (0.36, 0.35, 0.48, 1)
                text_color: 0.95, 1, 0.96, 1
                on_release: root.izaberi_valutu("EUR")

        RoundButton:
            label_text: "Osvezi kurs sada"
            tint: 0.36, 0.46, 0.64, 1
            text_color: 1, 1, 1, 1
            size_hint_y: None
            height: dp(52)
            on_release: root.osvezi_kurs_rucno()

        FieldLabel:
            text: "Kurs se automatski osvezava jednom dnevno (kad prvi put otvoris app tog dana). Ovde mozes rucno da ga povuces ponovo, npr. ako juce nije bilo interneta."
            size_hint_y: None
            height: dp(70)
            text_size: self.width, None

        Widget:

# ============================================================
# BACKUP - trajno cuvanje/vracanje voznji
# ============================================================

<BackupScreen>:
    name: "backup"
    ScreenRoot:

        TitleLabel:
            text: "Backup podataka"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Podesavanja"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "podesavanja"

        FieldLabel:
            text: "Cuva sve voznje (km, cene, adrese) u jedan fajl van aplikacije, da ne nestanu ako obrises app ili promenis telefon."

        PastelCard:
            orientation: "vertical"
            tint: 0.30, 0.29, 0.42, 0.92
            size_hint_y: None
            height: self.minimum_height
            padding: dp(14)
            Label:
                text: root.tekst_status
                color: 1, 1, 1, 1
                halign: "left"
                valign: "top"
                size_hint_y: None
                text_size: self.width, None
                height: self.texture_size[1]

        RoundButton:
            label_text: "Odobri pristup fajlovima"
            tint: 0.36, 0.46, 0.64, 1
            text_color: 1, 1, 1, 1
            size_hint_y: None
            height: dp(52)
            on_release: root.zatrazi_dozvolu()

        RoundButton:
            label_text: "Sacuvaj backup sada"
            tint: 0.30, 0.52, 0.36, 1
            text_color: 1, 1, 1, 1
            size_hint_y: None
            height: dp(56)
            on_release: root.sacuvaj_backup()

        RoundButton:
            label_text: "Vrati podatke iz backupa"
            tint: 0.55, 0.38, 0.26, 1
            text_color: 1, 1, 1, 1
            size_hint_y: None
            height: dp(56)
            on_release: root.ucitaj_backup()

        FieldLabel:
            text: "Ako menjas telefon: napravi backup na starom, prebaci fajl (WhatsApp/Drive/USB) u isti folder na novom, instaliraj app, pa klikni 'Vrati podatke'."
            size_hint_y: None
            height: dp(90)
            text_size: self.width, None

        Widget:

# ============================================================
# IZVOZ PDF - mesecni izvestaj kao PDF fajl
# ============================================================

<IzvozPdfScreen>:
    name: "izvoz_pdf"
    ScreenRoot:

        TitleLabel:
            text: "Izvoz PDF izvestaja"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Izvestaj"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "izvestaj"

        FieldLabel:
            text: "Pravi PDF sa svim voznjama za izabrani mesec (redni broj, vreme polaska/dolaska, adrese, cena) i ukupnim zbirom na kraju."

        FieldLabel:
            text: "Mesec (format GGGG-MM):"

        PastelTextInput:
            id: input_mesec
            hint_text: "npr. 2026-09"

        PastelCard:
            orientation: "vertical"
            tint: 0.30, 0.29, 0.42, 0.92
            size_hint_y: None
            height: self.minimum_height
            padding: dp(14)
            Label:
                text: root.tekst_status
                color: 1, 1, 1, 1
                halign: "left"
                valign: "top"
                size_hint_y: None
                text_size: self.width, None
                height: self.texture_size[1]

        RoundButton:
            label_text: "Izvezi PDF"
            tint: 0.30, 0.52, 0.36, 1
            text_color: 1, 1, 1, 1
            size_hint_y: None
            height: dp(56)
            on_release: root.izvezi_pdf()

        FieldLabel:
            text: "PDF se cuva u isti folder kao i backup: Preuzimanja/TaksiApp."
            size_hint_y: None
            height: dp(48)
            text_size: self.width, None

        Widget:

# ============================================================
# PLACEHOLDER ("Uskoro")
# ============================================================

<PlaceholderScreen>:
    naslov: ""
    ScreenRoot:

        TitleLabel:
            text: root.naslov

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Podesavanja"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "podesavanja"

        PastelCard:
            tint: 0.40, 0.38, 0.52, 0.9
            size_hint_y: None
            height: dp(70)
            padding: dp(14)
            Label:
                text: "Uskoro..."
                font_size: '17sp'
                bold: True
                color: 0.92, 0.92, 0.98, 1

        Widget:
"""


class MenuButton(ButtonBehavior, BoxLayout):
    icon_src = StringProperty("")
    tekst = StringProperty("")


class HomeScreen(Screen):
    pass


class PodesavanjaScreen(Screen):
    pass


class PlaceholderScreen(Screen):
    naslov = StringProperty("")


class CenovnikScreen(Screen):
    def on_pre_enter(self, *args):
        self.ids.input_start.text = f"{CENE.start_fee:g}"
        self.ids.input_osnovna.text = f"{CENE.tarife['Osnovna (07-22h)']:g}"
        self.ids.input_nocna.text = f"{CENE.tarife['Nocna (22-07h)']:g}"
        self.ids.input_vikend.text = f"{CENE.tarife['Vikend']:g}"
        self.ids.input_aerodromski.text = f"{CENE.tarife['Aerodromski transfer']:g}"

    def sacuvaj_cene(self):
        try:
            start = float(self.ids.input_start.text.replace(",", "."))
            osnovna = float(self.ids.input_osnovna.text.replace(",", "."))
            nocna = float(self.ids.input_nocna.text.replace(",", "."))
            vikend = float(self.ids.input_vikend.text.replace(",", "."))
            aerodromski = float(self.ids.input_aerodromski.text.replace(",", "."))
        except (ValueError, AttributeError):
            self._poruka("Unesi ispravne brojeve za sve cene.")
            return

        CENE.start_fee = start
        CENE.tarife["Osnovna (07-22h)"] = osnovna
        CENE.tarife["Nocna (22-07h)"] = nocna
        CENE.tarife["Vikend"] = vikend
        CENE.tarife["Aerodromski transfer"] = aerodromski

        app = App.get_running_app()
        CENE.sacuvaj(app.user_data_dir)

        self._poruka("Cene su sacuvane.")

    def _poruka(self, tekst):
        _prikazi_popup_poruku("Info", tekst, size_hint=(0.8, 0.3))


class NocnaTarifaScreen(Screen):
    tekst_status = StringProperty("")
    tekst_dugme = StringProperty("")
    tint_dugme = (0.7, 0.9, 0.72, 1)

    def on_pre_enter(self, *args):
        self._osvezi()

    def _osvezi(self):
        if CENE.nocna_aktivna:
            self.tekst_status = "Nocna tarifa: UKLJUCENA"
            self.tekst_dugme = "Iskljuci nocnu tarifu"
            self.tint_dugme = (0.66, 0.30, 0.34, 1)
        else:
            self.tekst_status = "Nocna tarifa: ISKLJUCENA"
            self.tekst_dugme = "Ukljuci nocnu tarifu"
            self.tint_dugme = (0.30, 0.52, 0.36, 1)

    def promeni(self):
        CENE.nocna_aktivna = not CENE.nocna_aktivna
        app = App.get_running_app()
        CENE.sacuvaj(app.user_data_dir)
        self._osvezi()


class GorivoScreen(Screen):
    tekst_ukupno = StringProperty("Ukupno potroseno: 0 RSD")
    dugme_tekst = StringProperty("Sacuvaj unos")
    izmena_id = None

    def on_pre_enter(self, *args):
        self.ucitaj_gorivo()

    def ucitaj_gorivo(self):
        kontejner = self.ids.lista_gorivo
        kontejner.clear_widgets()

        ukupno = sum(s.get("cena", 0) for s in GORIVO.stavke)
        ukupno_benzin = sum(
            s.get("cena", 0) for s in GORIVO.stavke if s.get("tip") == "Benzin"
        )
        ukupno_tng = sum(
            s.get("cena", 0) for s in GORIVO.stavke if s.get("tip") == "TNG"
        )
        self.tekst_ukupno = (
            f"Ukupno: {formatiraj_cenu(ukupno)}\n"
            f"Benzin: {formatiraj_cenu(ukupno_benzin)}   |   TNG: {formatiraj_cenu(ukupno_tng)}"
        )

        if not GORIVO.stavke:
            kontejner.add_widget(Label(
                text="Jos uvek nema unosa goriva.",
                size_hint_y=None, height=40,
                color=(1, 1, 1, 1),
            ))
            return

        for s in GORIVO.stavke:
            kontejner.add_widget(self._napravi_red(s))

    def _napravi_red(self, s):
        napomena = s.get("napomena") or "-"
        tip = s.get("tip", "Benzin")
        opis = (
            f"[b]{s.get('datum', '-')}[/b]\n"
            f"{tip}  |  {s.get('litara', 0):g} l\n"
            f"{napomena}\n"
            f"[color=6b3d0d][b]{formatiraj_cenu(s.get('cena', 0))}[/b][/color]"
        )
        return napravi_red_liste(
            opis,
            tint=(0.55, 0.38, 0.26, 0.92),
            boja_teksta=(1, 0.92, 0.85, 1),
            dugmad=[
                ("Izmeni", (0.36, 0.46, 0.64, 1), (0.95, 0.96, 1, 1),
                 lambda inst, sid=s["id"]: self._izmeni(sid)),
                ("Obrisi", (0.66, 0.30, 0.34, 1), (1, 0.95, 0.95, 1),
                 lambda inst, sid=s["id"]: self._obrisi(sid)),
            ],
        )

    def _izmeni(self, stavka_id):
        s = GORIVO.nadji(stavka_id)
        if not s:
            return
        self.izmena_id = stavka_id
        self.ids.input_litara.text = f"{s.get('litara', 0):g}"
        self.ids.input_cena_goriva.text = f"{s.get('cena', 0):g}"
        self.ids.input_napomena_gorivo.text = s.get("napomena") or ""
        tip = s.get("tip", "Benzin")
        if tip in self.ids.spinner_tip_goriva.values:
            self.ids.spinner_tip_goriva.text = tip
        self.dugme_tekst = "Sacuvaj izmenu"

    def sacuvaj_gorivo(self):
        try:
            litara = float(self.ids.input_litara.text.replace(",", "."))
            cena = float(self.ids.input_cena_goriva.text.replace(",", "."))
        except (ValueError, AttributeError):
            self._poruka("Unesi ispravne brojeve za kolicinu i cenu.")
            return

        app = App.get_running_app()
        stavka = {
            "datum": datetime.now().strftime("%Y-%m-%d"),
            "tip": self.ids.spinner_tip_goriva.text,
            "litara": litara,
            "cena": cena,
            "napomena": self.ids.input_napomena_gorivo.text.strip(),
        }

        if self.izmena_id is not None:
            GORIVO.azuriraj(app.user_data_dir, self.izmena_id, stavka)
            self.izmena_id = None
            self.dugme_tekst = "Sacuvaj unos"
            self._poruka("Izmena sacuvana.")
        else:
            GORIVO.dodaj(app.user_data_dir, stavka)
            self._poruka("Unos sacuvan.")

        self.ids.input_litara.text = ""
        self.ids.input_cena_goriva.text = ""
        self.ids.input_napomena_gorivo.text = ""
        self.ids.spinner_tip_goriva.text = "Benzin"

        self.ucitaj_gorivo()

    def _obrisi(self, stavka_id):
        app = App.get_running_app()
        GORIVO.obrisi(app.user_data_dir, stavka_id)
        if self.izmena_id == stavka_id:
            self.izmena_id = None
            self.dugme_tekst = "Sacuvaj unos"
        self.ucitaj_gorivo()

    def _poruka(self, tekst):
        _prikazi_popup_poruku("Info", tekst, size_hint=(0.8, 0.3))


class ServisScreen(Screen):
    tekst_ukupno = StringProperty("Ukupno na servisima: 0 RSD")
    dugme_tekst = StringProperty("Sacuvaj servis")
    izmena_id = None

    def on_pre_enter(self, *args):
        self.ucitaj_servis()

    def ucitaj_servis(self):
        kontejner = self.ids.lista_servis
        kontejner.clear_widgets()

        ukupno = sum(s.get("cena", 0) for s in SERVIS.stavke)
        self.tekst_ukupno = f"Ukupno na servisima: {formatiraj_cenu(ukupno)}"

        if not SERVIS.stavke:
            kontejner.add_widget(Label(
                text="Jos uvek nema unosa servisa.",
                size_hint_y=None, height=40,
                color=(1, 1, 1, 1),
            ))
            return

        for s in SERVIS.stavke:
            kontejner.add_widget(self._napravi_red(s))

    def _napravi_red(self, s):
        km = s.get("km")
        km_deo = f"  |  {km:g} km" if km else ""
        napomena = s.get("napomena") or "-"
        opis = (
            f"[b]{s.get('datum', '-')}[/b]\n"
            f"{s.get('vrsta', '-')}{km_deo}\n"
            f"{napomena}\n"
            f"[color=3a2570][b]{formatiraj_cenu(s.get('cena', 0))}[/b][/color]"
        )
        return napravi_red_liste(
            opis,
            tint=(0.38, 0.32, 0.52, 0.92),
            boja_teksta=(0.93, 0.90, 1, 1),
            dugmad=[
                ("Izmeni", (0.36, 0.46, 0.64, 1), (0.95, 0.96, 1, 1),
                 lambda inst, sid=s["id"]: self._izmeni(sid)),
                ("Obrisi", (0.66, 0.30, 0.34, 1), (1, 0.95, 0.95, 1),
                 lambda inst, sid=s["id"]: self._obrisi(sid)),
            ],
        )

    def _izmeni(self, stavka_id):
        s = SERVIS.nadji(stavka_id)
        if not s:
            return
        self.izmena_id = stavka_id
        self.ids.input_vrsta.text = s.get("vrsta") or ""
        self.ids.input_cena_servisa.text = f"{s.get('cena', 0):g}"
        km = s.get("km")
        self.ids.input_km_servis.text = f"{km:g}" if km else ""
        self.ids.input_napomena_servis.text = s.get("napomena") or ""
        self.dugme_tekst = "Sacuvaj izmenu"

    def sacuvaj_servis(self):
        vrsta = self.ids.input_vrsta.text.strip()
        if not vrsta:
            self._poruka("Unesi vrstu servisa.")
            return
        try:
            cena = float(self.ids.input_cena_servisa.text.replace(",", "."))
        except (ValueError, AttributeError):
            self._poruka("Unesi ispravnu cenu servisa.")
            return

        km_tekst = self.ids.input_km_servis.text.strip()
        km = None
        if km_tekst:
            try:
                km = float(km_tekst.replace(",", "."))
            except ValueError:
                self._poruka("Kilometraza mora biti broj (ili ostavi prazno).")
                return

        app = App.get_running_app()
        stavka = {
            "datum": datetime.now().strftime("%Y-%m-%d"),
            "vrsta": vrsta,
            "cena": cena,
            "km": km,
            "napomena": self.ids.input_napomena_servis.text.strip(),
        }

        if self.izmena_id is not None:
            SERVIS.azuriraj(app.user_data_dir, self.izmena_id, stavka)
            self.izmena_id = None
            self.dugme_tekst = "Sacuvaj servis"
            self._poruka("Izmena sacuvana.")
        else:
            SERVIS.dodaj(app.user_data_dir, stavka)
            self._poruka("Servis sacuvan.")

        self.ids.input_vrsta.text = ""
        self.ids.input_cena_servisa.text = ""
        self.ids.input_km_servis.text = ""
        self.ids.input_napomena_servis.text = ""

        self.ucitaj_servis()

    def _obrisi(self, stavka_id):
        app = App.get_running_app()
        SERVIS.obrisi(app.user_data_dir, stavka_id)
        if self.izmena_id == stavka_id:
            self.izmena_id = None
            self.dugme_tekst = "Sacuvaj servis"
        self.ucitaj_servis()

    def _poruka(self, tekst):
        _prikazi_popup_poruku("Info", tekst, size_hint=(0.8, 0.3))


class GpsVoznjaScreen(Screen):
    tekst_polazak = StringProperty("Nije zapoceta")
    tekst_km = StringProperty("Predjeno: 0.00 km")
    tekst_trajanje = StringProperty("Trajanje: 00:00:00")
    tekst_cena = StringProperty("Cena: 0 RSD")
    tekst_gps_status = StringProperty("")
    tekst_dijagnoza = StringProperty("")
    voznja_aktivna = BooleanProperty(False)

    MIN_TACNOST_M = 50       # ignorisi GPS tacke losije preciznosti od ovoga (metri)
    MIN_POMERAJ_KM = 0.01    # ignorisi mikro-skokove manje od 10m (GPS sum)
    MAX_BRZINA_KMH = 180     # ignorisi nerealne skokove (losa GPS tacka)

    def on_pre_enter(self, *args):
        self._tajmer = None
        self._brojac_signala = None
        self._brojac_poll = None
        self._sekundi_bez_signala = 0
        self._zadnje_vreme_lok = None
        if AKTIVNA_VOZNJA.aktivna:
            self.voznja_aktivna = True
            self.tekst_polazak = AKTIVNA_VOZNJA.pocetak_adresa or "Adresa nije dostupna"
            self._osvezi_prikaz()
            self._pokreni_tajmer()
            self._android_gps_start()  # ponovo zakaci listener + omoguci poll
            self._brojac_poll = Clock.schedule_interval(self._pull_lokaciju, 2)
        else:
            self.voznja_aktivna = False
            self.tekst_polazak = "Nije zapoceta"
            self.tekst_km = "Predjeno: 0.00 km"
            self.tekst_trajanje = "Trajanje: 00:00:00"
            self.tekst_cena = "Cena: 0 RSD"

    def on_leave(self, *args):
        if self._tajmer:
            self._tajmer.cancel()
            self._tajmer = None
        if getattr(self, "_brojac_signala", None):
            self._brojac_signala.cancel()
            self._brojac_signala = None
        if getattr(self, "_brojac_poll", None):
            self._brojac_poll.cancel()
            self._brojac_poll = None

    # ---------------- POCETAK VOZNJE ----------------

    def _dijagnostika_lokacije(self):
        """Vraca tekst sa stvarnim stanjem dozvola i GPS-a na uredjaju,
        da se tacno vidi gde je problem umesto nagadjanja."""
        redovi = []
        try:
            from android.permissions import check_permission, Permission
            fine = check_permission(Permission.ACCESS_FINE_LOCATION)
            coarse = check_permission(Permission.ACCESS_COARSE_LOCATION)
            redovi.append(f"Dozvola FINE_LOCATION: {'DA' if fine else 'NE'}")
            redovi.append(f"Dozvola COARSE_LOCATION: {'DA' if coarse else 'NE'}")
        except Exception as e:
            redovi.append(f"Ne mogu da proverim dozvole: {e}")

        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Context = autoclass("android.content.Context")
            activity = PythonActivity.mActivity
            lm = activity.getSystemService(Context.LOCATION_SERVICE)
            gps_on = lm.isProviderEnabled("gps")
            mreza_on = lm.isProviderEnabled("network")
            redovi.append(f"GPS provajder ukljucen: {'DA' if gps_on else 'NE'}")
            redovi.append(f"Mrezni provajder ukljucen: {'DA' if mreza_on else 'NE'}")
        except Exception as e:
            redovi.append(f"Ne mogu da proverim GPS status: {e}")

        return "\n".join(redovi)

    def pocni_voznju(self):
        try:
            from android.permissions import (
                request_permissions, check_permission, Permission,
            )
            potrebne = [
                Permission.ACCESS_FINE_LOCATION,
                Permission.ACCESS_COARSE_LOCATION,
            ]
            if not all(check_permission(p) for p in potrebne):
                self.tekst_gps_status = "Trazim dozvolu za lokaciju..."

                def na_odgovor(dozvole, rezultati):
                    if all(rezultati):
                        Clock.schedule_once(lambda dt: self._stvarno_pokreni_gps())
                    else:
                        self.tekst_gps_status = (
                            "Dozvola za lokaciju NIJE odobrena. Idi u "
                            "Podesavanja telefona -> Aplikacije -> Taksi App "
                            "-> Dozvole -> Lokacija -> Dozvoli."
                        )

                request_permissions(potrebne, na_odgovor)
                return
        except Exception:
            pass  # nije Android (desktop test) ili modul nije dostupan

        self._stvarno_pokreni_gps()

    def _stvarno_pokreni_gps(self):
        dijagnoza = self._dijagnostika_lokacije()
        self.tekst_dijagnoza = dijagnoza

        pokrenuto = self._android_gps_start()
        if not pokrenuto:
            self.tekst_gps_status = "Greska pri pokretanju GPS-a."
            return

        self.voznja_aktivna = True
        self.tekst_gps_status = "Trazim GPS signal..."
        self._sekundi_bez_signala = 0
        self._zadnje_vreme_lok = None
        self._brojac_signala = Clock.schedule_interval(self._proveri_signal, 1)
        self._brojac_poll = Clock.schedule_interval(self._pull_lokaciju, 2)
        AKTIVNA_VOZNJA.aktivna = True
        AKTIVNA_VOZNJA.pocetak_vreme = datetime.now().isoformat()
        AKTIVNA_VOZNJA.pocetak_lat = None
        AKTIVNA_VOZNJA.pocetak_lon = None
        AKTIVNA_VOZNJA.pocetak_adresa = "Trazim lokaciju..."
        AKTIVNA_VOZNJA.zadnja_lat = None
        AKTIVNA_VOZNJA.zadnja_lon = None
        AKTIVNA_VOZNJA.km = 0.0

        app = App.get_running_app()
        AKTIVNA_VOZNJA.sacuvaj(app.user_data_dir)

        # Ako je krajnja adresa unesena PRE klika na "Pocni voznju",
        # odmah otvaramo Google navigaciju ka njoj. GPS voznja (merenje
        # km i cene) je vec pokrenuta iznad i nastavlja da radi u
        # pozadini - otvaranje Google Maps-a ne gasi ovu app, Android
        # je samo stavlja u pozadinu (a on_pause/on_resume u app.py
        # vec vodi racuna da GPS nastavi da meri kad se vratis).
        self._pokreni_navigaciju_ako_ima_adrese()

    def _pokreni_navigaciju_ako_ima_adrese(self):
        dolazak = self.ids.input_dolazak_rucno.text.strip()
        if not dolazak:
            return

        destinacija = urllib.parse.quote(dolazak)
        url_navigacija = f"google.navigation:q={destinacija}&mode=d"
        url_rezervni = f"https://www.google.com/maps/dir/?api=1&destination={destinacija}&travelmode=driving"
        try:
            webbrowser.open(url_navigacija)
        except Exception:
            try:
                webbrowser.open(url_rezervni)
            except Exception:
                _prikazi_popup_poruku(
                    "Greska",
                    "Ne mogu da otvorim navigaciju, ali GPS voznja je pokrenuta normalno.",
                    size_hint=(0.8, 0.3),
                )

    def _pull_lokaciju(self, dt):
        """Umesto da cekamo da Android sam posalje novu tacku (push,
        sto se pokazalo nepouzdano - verovatno MIUI blokira stalno
        slanje u pozadini), aktivno pitamo za trenutnu poslednju
        poznatu lokaciju na svake 2 sekunde (pull). Isti trik koji je
        upalio za pocetnu tacku vožnje."""
        try:
            from jnius import autoclass

            LocationManager = autoclass("android.location.LocationManager")
            lm = getattr(self, "_android_lm", None)
            if lm is None:
                return

            najbolja = None
            for provider in (LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER):
                try:
                    if lm.isProviderEnabled(provider):
                        tacka = lm.getLastKnownLocation(provider)
                        if tacka is not None:
                            if najbolja is None or tacka.getTime() > najbolja.getTime():
                                najbolja = tacka
                except Exception:
                    pass

            if najbolja is None:
                return

            vreme = najbolja.getTime()
            if self._zadnje_vreme_lok is not None and vreme <= self._zadnje_vreme_lok:
                return  # ista tacka kao pre, nista novo

            self._zadnje_vreme_lok = vreme
            self._obradi_lokaciju({
                "lat": najbolja.getLatitude(),
                "lon": najbolja.getLongitude(),
                "accuracy": najbolja.getAccuracy(),
            })
        except Exception:
            pass

    def _android_gps_start(self):
        """Direktno preko Android sistema trazi lokaciju - i GPS i
        mrezni provajder istovremeno (sta god prvo javi signal), jer
        plyer sam po sebi koristi samo GPS provajder sto se pokazalo
        nepouzdano na nekim uredjajima/podesavanjima."""
        try:
            from jnius import autoclass, PythonJavaClass, java_method

            LocationManager = autoclass("android.location.LocationManager")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Context = autoclass("android.content.Context")
            Looper = autoclass("android.os.Looper")

            activity = PythonActivity.mActivity
            lm = activity.getSystemService(Context.LOCATION_SERVICE)
            glavni_looper = Looper.getMainLooper()

            ekran = self

            class _Listener(PythonJavaClass):
                __javainterfaces__ = ["android/location/LocationListener"]
                __javacontext__ = "app"

                @java_method("(Landroid/location/Location;)V")
                def onLocationChanged(self, location):
                    Clock.schedule_once(lambda dt: ekran._obradi_lokaciju({
                        "lat": location.getLatitude(),
                        "lon": location.getLongitude(),
                        "accuracy": location.getAccuracy(),
                    }))

                @java_method("(Ljava/lang/String;)V")
                def onProviderEnabled(self, provider):
                    pass

                @java_method("(Ljava/lang/String;)V")
                def onProviderDisabled(self, provider):
                    pass

                @java_method("(Ljava/lang/String;ILandroid/os/Bundle;)V")
                def onStatusChanged(self, provider, status, extras):
                    pass

            listener = _Listener()
            self._android_listener = listener
            self._android_lm = lm

            pokrenut_bar_jedan = False
            greske = []
            for provider in (LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER):
                try:
                    if lm.isProviderEnabled(provider):
                        lm.requestLocationUpdates(
                            provider, 1000, 3.0, listener, glavni_looper
                        )
                        pokrenut_bar_jedan = True
                except Exception as pe:
                    greske.append(f"{provider}: {pe}")

            if not pokrenut_bar_jedan and greske:
                self.tekst_dijagnoza += "\n" + "\n".join(greske)

            # Odmah probaj i poslednju poznatu (keširanu) lokaciju -
            # ne cekaj obavezno novi "zivi" signal. Google Maps i
            # slicne app takodje prvo koriste ovo, zato deluju trenutno.
            najbolja = None
            for provider in (LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER):
                try:
                    if lm.isProviderEnabled(provider):
                        poslednja = lm.getLastKnownLocation(provider)
                        if poslednja is not None:
                            if najbolja is None or poslednja.getTime() > najbolja.getTime():
                                najbolja = poslednja
                except Exception:
                    pass

            if najbolja is not None:
                self.tekst_dijagnoza += "\nPronadjena keširana lokacija - koristim je."
                Clock.schedule_once(lambda dt: self._obradi_lokaciju({
                    "lat": najbolja.getLatitude(),
                    "lon": najbolja.getLongitude(),
                    "accuracy": najbolja.getAccuracy(),
                }))
            else:
                self.tekst_dijagnoza += "\nNema keširane lokacije, cekam zivi signal."

            return pokrenut_bar_jedan
        except Exception as e:
            self.tekst_gps_status = f"Greska pri pokretanju GPS-a: {e}"
            return False

    def _android_gps_stop(self):
        try:
            lm = getattr(self, "_android_lm", None)
            listener = getattr(self, "_android_listener", None)
            if lm is not None and listener is not None:
                lm.removeUpdates(listener)
        except Exception:
            pass

    def _proveri_signal(self, dt):
        if AKTIVNA_VOZNJA.pocetak_lat is not None:
            if self._brojac_signala:
                self._brojac_signala.cancel()
                self._brojac_signala = None
            return
        self._sekundi_bez_signala += 1
        if self._sekundi_bez_signala == 15:
            self.tekst_gps_status = (
                "Jos uvek nema GPS signala. Voznja je pokrenuta i ceka "
                "prvi signal - km i cena ce poceti da se racunaju cim "
                "GPS uhvati poziciju."
            )
        elif self._sekundi_bez_signala > 15 and self._sekundi_bez_signala % 10 == 0:
            self.tekst_gps_status = f"Jos uvek tražim signal... ({self._sekundi_bez_signala}s)"

        self.tekst_polazak = "Trazim lokaciju..."
        self._pokreni_tajmer()

    # ---------------- TOKOM VOZNJE ----------------

    def _obradi_lokaciju(self, podaci):
        lat = podaci.get("lat")
        lon = podaci.get("lon")
        tacnost = podaci.get("accuracy", 0) or 0
        if lat is None or lon is None:
            return

        app = App.get_running_app()

        if AKTIVNA_VOZNJA.pocetak_lat is None:
            # ovo je prva validna tacka - pocetak voznje.
            # Ne filtriramo je po preciznosti (kesirane/mrezne lokacije
            # su cesto manje precizne od 50m, ali su i dalje mnogo
            # bolje nego nista za pocetnu adresu i orijentaciju).
            AKTIVNA_VOZNJA.pocetak_lat = lat
            AKTIVNA_VOZNJA.pocetak_lon = lon
            AKTIVNA_VOZNJA.zadnja_lat = lat
            AKTIVNA_VOZNJA.zadnja_lon = lon
            AKTIVNA_VOZNJA.sacuvaj(app.user_data_dir)
            self.tekst_gps_status = "GPS aktivan, pratim voznju."
            reverse_geocode(
                lat, lon, self._postavi_pocetnu_adresu,
                dijagnoza_callback=self._geokod_dijagnoza,
            )
            return

        # od druge tacke nadalje, filtriramo lose precizne skokove
        # (bitno za tacnost kilometraze tokom stvarne voznje)
        if tacnost and tacnost > self.MIN_TACNOST_M:
            self.tekst_gps_status = f"Slab GPS signal (+/-{tacnost:.0f}m), cekam bolji..."
            return

        # racunaj pomeraj od poslednje tacke
        udaljenost = haversine_km(
            AKTIVNA_VOZNJA.zadnja_lat, AKTIVNA_VOZNJA.zadnja_lon, lat, lon
        )

        if udaljenost < self.MIN_POMERAJ_KM:
            return  # mikro-sum, ignorisi

        # provera nerealnog skoka (losa GPS tacka)
        brzina_kmh = udaljenost / (3.0 / 3600.0)  # priblizno, min interval ~3s
        if brzina_kmh > self.MAX_BRZINA_KMH:
            return  # verovatno GPS greska, ignorisi tacku

        AKTIVNA_VOZNJA.km += udaljenost
        AKTIVNA_VOZNJA.zadnja_lat = lat
        AKTIVNA_VOZNJA.zadnja_lon = lon
        AKTIVNA_VOZNJA.sacuvaj(app.user_data_dir)
        self._osvezi_prikaz()

    def _postavi_pocetnu_adresu(self, adresa):
        AKTIVNA_VOZNJA.pocetak_adresa = adresa
        app = App.get_running_app()
        AKTIVNA_VOZNJA.sacuvaj(app.user_data_dir)
        self.tekst_polazak = adresa

    def _geokod_dijagnoza(self, tekst):
        self.tekst_dijagnoza += "\n[Adresa] " + tekst

    def _pokreni_tajmer(self):
        if self._tajmer is None:
            self._tajmer = Clock.schedule_interval(lambda dt: self._osvezi_prikaz(), 1)

    def _osvezi_prikaz(self):
        self.tekst_km = f"Predjeno: {AKTIVNA_VOZNJA.km:.2f} km"

        if AKTIVNA_VOZNJA.pocetak_vreme:
            pocetak = datetime.fromisoformat(AKTIVNA_VOZNJA.pocetak_vreme)
            trajanje = datetime.now() - pocetak
            ukupno_sec = int(trajanje.total_seconds())
            h, ostatak = divmod(ukupno_sec, 3600)
            m, s = divmod(ostatak, 60)
            self.tekst_trajanje = f"Trajanje: {h:02d}:{m:02d}:{s:02d}"

        cena_po_km = CENE.tarife.get(
            "Nocna (22-07h)" if CENE.nocna_aktivna else "Osnovna (07-22h)",
            CENE.tarife["Osnovna (07-22h)"],
        )
        cena = CENE.start_fee + AKTIVNA_VOZNJA.km * cena_po_km
        self.tekst_cena = f"Cena: {formatiraj_cenu(cena)}"

        if AKTIVNA_VOZNJA.pocetak_adresa and AKTIVNA_VOZNJA.pocetak_adresa != "Trazim lokaciju...":
            self.tekst_polazak = AKTIVNA_VOZNJA.pocetak_adresa

    # ---------------- KRAJ VOZNJE ----------------

    def zavrsi_voznju(self):
        if not AKTIVNA_VOZNJA.aktivna:
            return

        self._android_gps_stop()

        if self._tajmer:
            self._tajmer.cancel()
            self._tajmer = None
        if getattr(self, "_brojac_signala", None):
            self._brojac_signala.cancel()
            self._brojac_signala = None
        if getattr(self, "_brojac_poll", None):
            self._brojac_poll.cancel()
            self._brojac_poll = None

        self.voznja_aktivna = False
        self.tekst_gps_status = "Trazim krajnju adresu..."

        # ako GPS nije uspeo da izmeri km, koristi rucni unos (ako postoji polje)
        km = AKTIVNA_VOZNJA.km
        if km <= 0:
            polje_km = self.ids.get("input_km_rucno")
            rucni_km_tekst = polje_km.text.strip() if polje_km else ""
            if rucni_km_tekst:
                try:
                    km = float(rucni_km_tekst.replace(",", "."))
                except ValueError:
                    km = 0.0

        cena_po_km = CENE.tarife.get(
            "Nocna (22-07h)" if CENE.nocna_aktivna else "Osnovna (07-22h)",
            CENE.tarife["Osnovna (07-22h)"],
        )
        ukupno = CENE.start_fee + km * cena_po_km
        tarifa_naziv = "Nocna (22-07h)" if CENE.nocna_aktivna else "Osnovna (07-22h)"

        polazak_adresa = AKTIVNA_VOZNJA.pocetak_adresa or "Adresa nije dostupna"
        if polazak_adresa == "Trazim lokaciju...":
            polazak_adresa = "Adresa nije dostupna"

        rucni_dolazak = self.ids.input_dolazak_rucno.text.strip()

        if rucni_dolazak:
            self._sacuvaj_zavrsenu_voznju(
                km, cena_po_km, ukupno, tarifa_naziv, polazak_adresa, rucni_dolazak
            )
        elif AKTIVNA_VOZNJA.zadnja_lat is not None:
            reverse_geocode(
                AKTIVNA_VOZNJA.zadnja_lat,
                AKTIVNA_VOZNJA.zadnja_lon,
                lambda adresa: self._sacuvaj_zavrsenu_voznju(
                    km, cena_po_km, ukupno, tarifa_naziv, polazak_adresa, adresa
                ),
                dijagnoza_callback=self._geokod_dijagnoza,
            )
        else:
            self._sacuvaj_zavrsenu_voznju(
                km, cena_po_km, ukupno, tarifa_naziv, polazak_adresa,
                "Adresa nije dostupna",
            )

    def _sacuvaj_zavrsenu_voznju(self, km, cena_po_km, ukupno, tarifa_naziv,
                                   polazak_adresa, dolazak_adresa):
        vreme_pocetka_txt = None
        if AKTIVNA_VOZNJA.pocetak_vreme:
            try:
                vreme_pocetka_txt = datetime.fromisoformat(
                    AKTIVNA_VOZNJA.pocetak_vreme
                ).strftime("%H:%M")
            except Exception:
                vreme_pocetka_txt = None

        db.dodaj_voznju(
            od_adresa=polazak_adresa,
            do_adresa=dolazak_adresa,
            km=round(km, 2),
            tarifa_naziv=tarifa_naziv,
            cena_po_km=cena_po_km,
            start_taksa=CENE.start_fee,
            ukupna_cena=ukupno,
            napomena="GPS voznja (automatski unos)",
            vreme_pocetka=vreme_pocetka_txt,
        )

        app = App.get_running_app()
        AKTIVNA_VOZNJA.resetuj(app.user_data_dir)

        self.tekst_gps_status = ""
        self.tekst_dijagnoza = ""
        self.tekst_polazak = "Nije zapoceta"
        self.tekst_km = "Predjeno: 0.00 km"
        self.tekst_trajanje = "Trajanje: 00:00:00"
        self.tekst_cena = f"Cena: {formatiraj_cenu(0)}"
        self.ids.input_dolazak_rucno.text = ""

        self._poruka(
            f"Voznja sacuvana!\n{polazak_adresa}\n-> {dolazak_adresa}\n"
            f"{km:.2f} km, {formatiraj_cenu(ukupno)}"
        )

    def _poruka(self, tekst):
        _prikazi_popup_poruku("Voznja zavrsena", tekst, size_hint=(0.85, 0.4))


class NavigacijaScreen(Screen):
    def otvori_navigaciju(self):
        odrediste = self.ids.input_odrediste.text.strip()
        if not odrediste:
            _prikazi_popup_poruku("Info", "Unesi odrediste pre otvaranja navigacije.", size_hint=(0.8, 0.3))
            return

        destinacija = urllib.parse.quote(odrediste)

        # "google.navigation" je poseban link koji Google Maps na
        # Androidu prepoznaje i odmah pokrece navigaciju korak-po-korak
        # (bez ekrana za pregled rute na kome bi inace trebalo rucno
        # kliknuti "Kreni"). Polazna tacka je uvek TRENUTNA GPS pozicija
        # telefona u tom trenutku - ovaj format ne dozvoljava da se
        # zada neka druga/starija polazna tacka.
        url_navigacija = f"google.navigation:q={destinacija}&mode=d"

        # Rezervni link, ako iz nekog razloga google.navigation ne
        # uspe da se otvori (npr. Google Maps app nije instaliran) -
        # ovaj samo prikazuje rutu, bez automatskog starta.
        url_rezervni = f"https://www.google.com/maps/dir/?api=1&destination={destinacija}&travelmode=driving"

        try:
            webbrowser.open(url_navigacija)
        except Exception:
            try:
                webbrowser.open(url_rezervni)
            except Exception:
                _prikazi_popup_poruku("Greska", "Ne mogu da otvorim navigaciju na ovom uredjaju.", size_hint=(0.8, 0.3))


class GoogleApiScreen(Screen):
    def on_pre_enter(self, *args):
        self.ids.input_google_kljuc.text = API.google_kljuc

    def sacuvaj_kljuc(self):
        API.google_kljuc = self.ids.input_google_kljuc.text.strip()
        app = App.get_running_app()
        API.sacuvaj(app.user_data_dir)

        _prikazi_popup_poruku("Info", "Google API kljuc sacuvan.", size_hint=(0.8, 0.3))


class ProfilScreen(Screen):
    def on_pre_enter(self, *args):
        self.ids.input_ime.text = VOZAC.ime_prezime
        self.ids.input_telefon.text = VOZAC.telefon
        self.ids.input_licenca.text = VOZAC.broj_licence
        self.ids.input_tablice.text = VOZAC.tablice
        self.ids.input_vozilo.text = VOZAC.vozilo

    def sacuvaj_profil(self):
        VOZAC.ime_prezime = self.ids.input_ime.text.strip()
        VOZAC.telefon = self.ids.input_telefon.text.strip()
        VOZAC.broj_licence = self.ids.input_licenca.text.strip()
        VOZAC.tablice = self.ids.input_tablice.text.strip()
        VOZAC.vozilo = self.ids.input_vozilo.text.strip()

        app = App.get_running_app()
        VOZAC.sacuvaj(app.user_data_dir)

        _prikazi_popup_poruku("Info", "Profil vozaca je sacuvan.", size_hint=(0.8, 0.3))


class ValutaScreen(Screen):
    tekst_kurs = StringProperty("")
    valuta_izbor = StringProperty("RSD")

    def on_pre_enter(self, *args):
        self.valuta_izbor = KURS.valuta
        self._osvezi_tekst()

    def _osvezi_tekst(self):
        if KURS.kurs_eur_rsd:
            self.tekst_kurs = (
                f"1 EUR = {KURS.kurs_eur_rsd:.2f} RSD\n"
                f"(kurs od {KURS.datum_kursa or 'nepoznatog datuma'})"
            )
        else:
            self.tekst_kurs = "Kurs jos nije povucen sa interneta."

    def izaberi_valutu(self, valuta):
        self.valuta_izbor = valuta
        KURS.valuta = valuta
        app = App.get_running_app()
        KURS.sacuvaj(app.user_data_dir)

    def osvezi_kurs_rucno(self):
        app = App.get_running_app()

        def posao():
            uspeh, greska = KURS.osvezi_ako_treba(app.user_data_dir, prinudno=True)
            Clock.schedule_once(lambda dt: self._posle_osvezavanja(uspeh, greska))

        threading.Thread(target=posao, daemon=True).start()

    def _posle_osvezavanja(self, uspeh, greska):
        self._osvezi_tekst()
        if uspeh:
            _prikazi_popup_poruku("Info", "Kurs je osvezen.", size_hint=(0.8, 0.3))
        else:
            _prikazi_popup_poruku(
                "Greska",
                f"Nije uspelo povlacenje kursa:\n{greska}",
                size_hint=(0.85, 0.4),
            )


class BackupScreen(Screen):
    tekst_status = StringProperty("")

    def on_pre_enter(self, *args):
        self._osvezi_status()

    def _osvezi_status(self):
        putanja = os.path.join(_putanja_backup_foldera(), BACKUP_FAJL_NAZIV)
        if _ima_dozvolu_svi_fajlovi():
            dozvola_txt = "Dozvola za fajlove: DA"
        else:
            dozvola_txt = "Dozvola za fajlove: NE (klikni dugme ispod)"

        try:
            broj = db.broj_voznji()
        except Exception:
            broj = "?"

        self.tekst_status = (
            f"{dozvola_txt}\n\n"
            f"Backup fajl se cuva ovde:\n{putanja}\n\n"
            f"Voznji trenutno u bazi: {broj}"
        )

    def zatrazi_dozvolu(self):
        _zatrazi_dozvolu_svi_fajlovi()
        Clock.schedule_once(lambda dt: self._osvezi_status(), 1)

    def sacuvaj_backup(self):
        if not _ima_dozvolu_svi_fajlovi():
            _prikazi_popup_poruku(
                "Nedostaje dozvola",
                "Prvo klikni 'Odobri pristup fajlovima', potvrdi na sledecem "
                "ekranu, pa se vrati ovde i probaj ponovo.",
                size_hint=(0.88, 0.4),
            )
            return
        try:
            voznje = db.sve_voznje_za_izvoz()
            podaci = [dict(v) for v in voznje]
            folder = _putanja_backup_foldera()
            os.makedirs(folder, exist_ok=True)
            putanja = os.path.join(folder, BACKUP_FAJL_NAZIV)
            with open(putanja, "w", encoding="utf-8") as f:
                json.dump(podaci, f, ensure_ascii=False, indent=2)
            _prikazi_popup_poruku(
                "Sacuvano",
                f"Sacuvano {len(podaci)} voznji u:\n{putanja}",
                size_hint=(0.88, 0.45),
            )
        except Exception as e:
            _prikazi_popup_poruku(
                "Greska", f"Backup nije uspeo:\n{e}", size_hint=(0.88, 0.4)
            )
        self._osvezi_status()

    def ucitaj_backup(self):
        if not _ima_dozvolu_svi_fajlovi():
            _prikazi_popup_poruku(
                "Nedostaje dozvola",
                "Prvo klikni 'Odobri pristup fajlovima', potvrdi na sledecem "
                "ekranu, pa se vrati ovde i probaj ponovo.",
                size_hint=(0.88, 0.4),
            )
            return

        putanja = os.path.join(_putanja_backup_foldera(), BACKUP_FAJL_NAZIV)
        try:
            with open(putanja, "r", encoding="utf-8") as f:
                podaci = json.load(f)
        except FileNotFoundError:
            _prikazi_popup_poruku(
                "Nema backup fajla",
                f"Nije pronadjen fajl:\n{putanja}\n\n"
                f"Prvo napravi backup na starom telefonu, pa taj fajl "
                f"prebaci u isti folder na ovom telefonu.",
                size_hint=(0.88, 0.5),
            )
            return
        except Exception as e:
            _prikazi_popup_poruku(
                "Greska", f"Ne mogu da procitam backup:\n{e}", size_hint=(0.88, 0.4)
            )
            return

        dodato = 0
        preskoceno = 0
        for v in podaci:
            try:
                if db.voznja_postoji(
                    v.get("datum"), v.get("vreme"), v.get("km"), v.get("ukupna_cena")
                ):
                    preskoceno += 1
                    continue
                db.uvezi_voznju_sirovo(v)
                dodato += 1
            except Exception:
                preskoceno += 1

        _prikazi_popup_poruku(
            "Vraceno iz backupa",
            f"Dodato: {dodato} voznji\nPreskoceno (vec postoje): {preskoceno}",
            size_hint=(0.85, 0.4),
        )
        self._osvezi_status()


class IzvozPdfScreen(Screen):
    tekst_status = StringProperty("")

    def on_pre_enter(self, *args):
        if not self.ids.input_mesec.text:
            self.ids.input_mesec.text = datetime.now().strftime("%Y-%m")
        self._osvezi_status()

    def _osvezi_status(self):
        if _ima_dozvolu_svi_fajlovi():
            self.tekst_status = "Dozvola za fajlove: DA"
        else:
            self.tekst_status = (
                "Dozvola za fajlove: NE\n"
                "Idi u Podesavanja -> Backup podataka i klikni "
                "'Odobri pristup fajlovima', pa se vrati ovde."
            )

    def izvezi_pdf(self):
        mesec = self.ids.input_mesec.text.strip()
        if not re.match(r"^\d{4}-\d{2}$", mesec):
            _prikazi_popup_poruku(
                "Greska",
                "Unesi mesec u formatu GGGG-MM, npr. 2026-09",
                size_hint=(0.85, 0.35),
            )
            return

        if not _ima_dozvolu_svi_fajlovi():
            _prikazi_popup_poruku(
                "Nedostaje dozvola",
                "Idi u Podesavanja -> Backup podataka i klikni "
                "'Odobri pristup fajlovima', pa se vrati ovde.",
                size_hint=(0.88, 0.4),
            )
            return

        try:
            voznje = db.voznje_za_mesec(mesec)
        except Exception as e:
            _prikazi_popup_poruku("Greska", f"Ne mogu da procitam bazu:\n{e}", size_hint=(0.88, 0.4))
            return

        if not voznje:
            _prikazi_popup_poruku(
                "Nema voznji",
                f"Nema nijedne voznje za {mesec} - PDF nije napravljen.",
                size_hint=(0.85, 0.3),
            )
            return

        try:
            folder = _putanja_backup_foldera()
            os.makedirs(folder, exist_ok=True)
            putanja = os.path.join(folder, f"izvestaj_{mesec}.pdf")
            generisi_mesecni_pdf(mesec, putanja)
            _prikazi_popup_poruku(
                "Sacuvano",
                f"PDF izvestaj ({len(voznje)} voznji) sacuvan u:\n{putanja}",
                size_hint=(0.88, 0.45),
            )
        except Exception as e:
            _prikazi_popup_poruku(
                "Greska", f"Pravljenje PDF-a nije uspelo:\n{e}", size_hint=(0.88, 0.45)
            )


class KalkulatorScreen(Screen):
    tekst_cene = StringProperty("Unesi kilometrazu da vidis cenu")
    dugme_tekst = StringProperty("Sacuvaj voznju")
    tarife_lista = list(DEFAULT_TARIFE.keys())
    editing_id = None

    def on_pre_enter(self, *args):
        global EDIT_VOZNJA
        if EDIT_VOZNJA is not None:
            v = EDIT_VOZNJA
            self.editing_id = v.get("id")
            self.ids.input_km.text = f"{v.get('km', 0):g}"
            self.ids.input_od.text = v.get("od_adresa") or ""
            self.ids.input_do.text = v.get("do_adresa") or ""
            self.ids.input_napomena.text = v.get("napomena") or ""
            tarifa = v.get("tarifa_naziv")
            if tarifa in self.tarife_lista and "spinner_tarifa" in self.ids:
                self.ids.spinner_tarifa.text = tarifa
            self.dugme_tekst = "Sacuvaj izmenu"
            self.izracunaj()
            EDIT_VOZNJA = None
        else:
            self.editing_id = None
            self.dugme_tekst = "Sacuvaj voznju"
            if CENE.nocna_aktivna and "spinner_tarifa" in self.ids:
                self.ids.spinner_tarifa.text = "Nocna (22-07h)"
                self.izracunaj()

    def izracunaj(self):
        try:
            km = float(self.ids.input_km.text.replace(",", "."))
        except (ValueError, AttributeError):
            self.tekst_cene = "Unesi kilometrazu da vidis cenu"
            return
        tarifa_naziv = self.ids.spinner_tarifa.text
        cena_po_km = CENE.tarife.get(tarifa_naziv, CENE.tarife["Osnovna (07-22h)"])
        ukupno = CENE.start_fee + km * cena_po_km
        self.tekst_cene = (
            f"Cena: {formatiraj_cenu(ukupno)}\n"
            f"(start {formatiraj_cenu(CENE.start_fee)} + {km:g} km x {formatiraj_cenu(cena_po_km)})"
        )

    def sacuvaj_voznju(self):
        try:
            km = float(self.ids.input_km.text.replace(",", "."))
        except (ValueError, AttributeError):
            self._poruka("Unesi ispravnu kilometrazu pre cuvanja.")
            return
        if km <= 0:
            self._poruka("Kilometraza mora biti veca od 0.")
            return

        tarifa_naziv = self.ids.spinner_tarifa.text
        cena_po_km = CENE.tarife.get(tarifa_naziv, CENE.tarife["Osnovna (07-22h)"])
        ukupno = CENE.start_fee + km * cena_po_km

        if self.editing_id is not None:
            db.obrisi_voznju(self.editing_id)

        db.dodaj_voznju(
            od_adresa=self.ids.input_od.text.strip(),
            do_adresa=self.ids.input_do.text.strip(),
            km=km,
            tarifa_naziv=tarifa_naziv,
            cena_po_km=cena_po_km,
            start_taksa=CENE.start_fee,
            ukupna_cena=ukupno,
            napomena=self.ids.input_napomena.text.strip(),
        )

        bila_izmena = self.editing_id is not None
        self.editing_id = None
        self.dugme_tekst = "Sacuvaj voznju"

        # reset forme
        self.ids.input_km.text = ""
        self.ids.input_od.text = ""
        self.ids.input_do.text = ""
        self.ids.input_napomena.text = ""
        self.tekst_cene = "Unesi kilometrazu da vidis cenu"

        if bila_izmena:
            self._poruka(f"Izmena sacuvana! Cena voznje: {formatiraj_cenu(ukupno)}")
        else:
            self._poruka(f"Sacuvano! Cena voznje: {formatiraj_cenu(ukupno)}")

    def _poruka(self, tekst):
        _prikazi_popup_poruku("Info", tekst, size_hint=(0.8, 0.3))


class EvidencijaScreen(Screen):
    def on_pre_enter(self, *args):
        self.ucitaj_voznje()

    def ucitaj_voznje(self):
        kontejner = self.ids.lista_voznji
        kontejner.clear_widgets()
        voznje = db.sve_voznje(limit=200)

        if not voznje:
            kontejner.add_widget(Label(
                text="Jos uvek nema evidentiranih voznji.",
                size_hint_y=None, height=40,
                color=(1, 1, 1, 1),
            ))
            return

        for v in voznje:
            red = self._napravi_red(v)
            kontejner.add_widget(red)

    def _napravi_red(self, v):
        od = v["od_adresa"] or "-"
        do = v["do_adresa"] or "-"

        vreme_pocetka = v["vreme_pocetka"] if "vreme_pocetka" in v.keys() else None
        if vreme_pocetka:
            vreme_txt = f"Pocetak {vreme_pocetka}  |  Kraj {v['vreme']}"
        else:
            vreme_txt = f"Kraj {v['vreme']}"

        opis = (
            f"[b]{v['datum']}[/b]  {vreme_txt}\n"
            f"{v['km']:g} km  |  {v['tarifa_naziv']}\n"
            f"{od}\n-> {do}\n"
            f"[color=cc8a00][b]{formatiraj_cenu(v['ukupna_cena'])}[/b][/color]"
        )
        return napravi_red_liste(
            opis,
            tint=(0.40, 0.38, 0.52, 0.92),
            boja_teksta=(0.94, 0.93, 0.98, 1),
            dugmad=[
                ("Izmeni", (0.36, 0.46, 0.64, 1), (0.95, 0.96, 1, 1),
                 lambda inst, v=v: self._izmeni(v)),
                ("Obrisi", (0.66, 0.30, 0.34, 1), (1, 0.95, 0.95, 1),
                 lambda inst, vid=v["id"]: self._obrisi(vid)),
            ],
        )

    def _izmeni(self, v):
        global EDIT_VOZNJA
        EDIT_VOZNJA = dict(v)
        self.manager.current = "kalkulator"

    def _obrisi(self, voznja_id):
        db.obrisi_voznju(voznja_id)
        self.ucitaj_voznje()


class IzvestajScreen(Screen):
    tekst_danas = StringProperty("")
    tekst_nedelja = StringProperty("")
    tekst_mesec = StringProperty("")

    def on_pre_enter(self, *args):
        self.osvezi()

    def osvezi(self):
        danas_dt = datetime.now()
        danas = danas_dt.strftime("%Y-%m-%d")
        mesec = danas_dt.strftime("%Y-%m")
        pocetak_nedelje = (danas_dt - timedelta(days=danas_dt.weekday())).strftime("%Y-%m-%d")

        voznje_danas = db.voznje_za_datum(danas)
        broj_d, prihod_d, km_d = db.zbir_voznji(voznje_danas)
        self.tekst_danas = (
            f"DANAS ({danas})\n"
            f"Broj voznji: {broj_d}\n"
            f"Ukupno km: {km_d:.1f}\n"
            f"Ukupna zarada: {formatiraj_cenu(prihod_d)}"
        )
        self._prikazi_voznje_danas(voznje_danas)

        voznje_nedelje = db.voznje_izmedju(pocetak_nedelje, danas)
        broj_n, prihod_n, km_n = db.zbir_voznji(voznje_nedelje)
        self.tekst_nedelja = (
            f"OVA NEDELJA ({pocetak_nedelje} - {danas})\n"
            f"Broj voznji: {broj_n}\n"
            f"Ukupno km: {km_n:.1f}\n"
            f"Ukupna zarada: {formatiraj_cenu(prihod_n)}"
        )

        voznje_mesec = db.voznje_za_mesec(mesec)
        broj_m, prihod_m, km_m = db.zbir_voznji(voznje_mesec)
        self.tekst_mesec = (
            f"OVAJ MESEC ({mesec})\n"
            f"Broj voznji: {broj_m}\n"
            f"Ukupno km: {km_m:.1f}\n"
            f"Ukupna zarada: {formatiraj_cenu(prihod_m)}"
        )

    def _prikazi_voznje_danas(self, voznje):
        kontejner = self.ids.lista_danas_voznje
        kontejner.clear_widgets()

        if not voznje:
            kontejner.add_widget(Label(
                text="Jos uvek nema voznji danas.",
                size_hint_y=None, height=32,
                color=(1, 1, 1, 1),
            ))
            return

        for v in voznje:
            vreme_pocetka = v["vreme_pocetka"] if "vreme_pocetka" in v.keys() else None
            vreme_txt = f"{vreme_pocetka} -> {v['vreme']}" if vreme_pocetka else f"Kraj {v['vreme']}"
            opis = f"{vreme_txt}   |   [b]{formatiraj_cenu(v['ukupna_cena'])}[/b]"
            kontejner.add_widget(napravi_red_liste(
                opis,
                tint=(0.30, 0.40, 0.36, 0.85),
                boja_teksta=(0.92, 0.98, 0.94, 1),
                dugmad=[],
            ))


def _crash_log_path():
    try:
        from kivy.app import App
        base = App.get_running_app().user_data_dir if App.get_running_app() else "."
    except Exception:
        base = "."
    return os.path.join(base, "crash_log.txt")


def _zapisi_gresku(tekst):
    try:
        with open(_crash_log_path(), "w", encoding="utf-8") as f:
            f.write(tekst)
    except Exception:
        pass


def _prikazi_popup_poruku(naslov, tekst, size_hint=(0.85, 0.5)):
    """Otvara Popup sa tekstom koji se pravilno prelama u novi red i,
    ako je predugacak, moze da se skroluje - umesto da tekst 'iscuri'
    van okvira popupa kao ranije.
    """
    sv = ScrollView()
    lbl = Label(
        text=tekst,
        size_hint_y=None,
        halign="center",
        valign="middle",
        color=(1, 1, 1, 1),
        padding=(10, 10),
    )
    lbl.bind(texture_size=lambda inst, val: setattr(lbl, "height", val[1]))
    lbl.bind(width=lambda inst, val: setattr(lbl, "text_size", (val, None)))
    sv.add_widget(lbl)

    popup = Popup(
        title=naslov,
        content=sv,
        size_hint=size_hint,
    )
    popup.open()
    return popup


def _prikazi_gresku_ekran(poruka):
    """Vraca prost Kivy ekran koji ispisuje gresku umesto da app pukne bez traga."""
    sv = ScrollView()
    lbl = Label(
        text=(
            "GRESKA PRI POKRETANJU APLIKACIJE\n"
            "Posalji ovaj tekst da se ispravi:\n\n" + poruka
        ),
        markup=False,
        size_hint_y=None,
        text_size=(None, None),
        color=(1, 1, 1, 1),
        padding=(20, 20),
    )
    lbl.bind(texture_size=lambda inst, val: setattr(lbl, "size", val))
    lbl.bind(width=lambda inst, val: setattr(lbl, "text_size", (val - 40, None)))
    sv.add_widget(lbl)
    root = BoxLayout()
    root.add_widget(sv)
    return root


class TaksiApp(App):
    background_img = StringProperty(BACKGROUND_IMG)

    def build(self):
        # Globalni hvatac neuhvacenih gresaka posle pokretanja (npr. u dugmadima)
        sys.excepthook = self._globalna_greska

        self.title = "Taksi App"
        try:
            db.init_db()
            CENE.ucitaj(self.user_data_dir)
            GORIVO.ucitaj(self.user_data_dir)
            SERVIS.ucitaj(self.user_data_dir)
            AKTIVNA_VOZNJA.ucitaj(self.user_data_dir)
            API.ucitaj(self.user_data_dir)
            VOZAC.ucitaj(self.user_data_dir)
            KURS.ucitaj(self.user_data_dir)
            # Kurs se povlaci sa interneta u pozadini (posebna nit), da
            # app ne "visi" na pokretanju ako je internet spor ili ga
            # nema - u tom slucaju samo ostaje poslednji sacuvani kurs.
            threading.Thread(
                target=lambda: KURS.osvezi_ako_treba(self.user_data_dir),
                daemon=True,
            ).start()
            return Builder.load_string(KV)
        except Exception:
            greska = traceback.format_exc()
            _zapisi_gresku(greska)
            return _prikazi_gresku_ekran(greska)

    def _globalna_greska(self, exc_type, exc_value, exc_tb):
        greska = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        _zapisi_gresku(greska)
        try:
            _prikazi_popup_poruku("Greska u aplikaciji", greska[-1500:], size_hint=(0.95, 0.8))
        except Exception:
            pass

    def on_pause(self):
        # Vratiti True znaci "Android, pauziraj me ali ne gasi", tako
        # da GPS voznja u toku (ako postoji) ne bude prekinuta kad
        # dodje poziv ili korisnik kratko izadje iz aplikacije.
        return True

    def on_resume(self):
        # Kad se korisnik vrati (npr. posle poziva), ponovo
        # zakacinjemo GPS oslonac i osvezavamo prikaz ako je voznja
        # u toku - Android ume da "otkine" listener dok je app u
        # pozadini, pa ga vracamo rucno umesto da samo cekamo.
        try:
            if not AKTIVNA_VOZNJA.aktivna:
                return
            sm = self.root
            if sm is None:
                return
            ekran = sm.get_screen("gps_voznja")
            ekran._android_gps_start()
            if getattr(ekran, "_tajmer", None) is None:
                ekran._pokreni_tajmer()
            if getattr(ekran, "_brojac_poll", None) is None:
                ekran._brojac_poll = Clock.schedule_interval(ekran._pull_lokaciju, 2)
            ekran._osvezi_prikaz()
        except Exception:
            pass


if __name__ == "__main__":
    TaksiApp().run()
