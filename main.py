"""
Taksi App - licna aplikacija za taksistu
Kalkulator cene, evidencija voznji, dnevni/mesecni izvestaj zarade.
"""

import os
import shutil
import csv
import sys
import re
import json
import math
import calendar
import threading
import time
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
from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.properties import StringProperty, BooleanProperty, ListProperty, DictProperty
from datetime import datetime, timedelta, time as dt_time

from servisi import database as db
from servisi import grafik_zarade
from servisi import i18n
from ekrani import ekran_navigacija
from ekrani import ekran_google_api
from ekrani import ekran_profil
from ekrani import ekran_valuta
from ekrani import ekran_jezik
from ekrani import ekran_sigurnost
from ekrani import ekran_uputstvo
from ekrani import ekran_dispeceri
from ekrani import ekran_backup
from ekrani import ekran_izvoz
from ekrani import ekran_cenovnik
from ekrani import ekran_gorivo
from ekrani import ekran_servis
from ekrani import ekran_troskovi
from ekrani import ekran_kalkulator
from ekrani import ekran_evidencija
from ekrani import ekran_izvestaj
from ekrani import ekran_gps_voznja

try:
    from androidstorage4kivy import SharedStorage, ShareSheet
    _DELJENJE_DOSTUPNO = True
except Exception:
    _DELJENJE_DOSTUPNO = False

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
TROSKOVI = JsonLog("troskovi.json")
DISPECERI = JsonLog("dispeceri.json")
JEZIK = i18n.JezikPodesavanja()


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
    tablice, vozilo, i datume isteka registracije/osiguranja. Koristi
    se za prikaz u app-u i u zaglavlju PDF mesecnog izvestaja."""

    def __init__(self):
        self.ime_prezime = ""
        self.telefon = ""
        self.broj_licence = ""
        self.tablice = ""
        self.vozilo = ""
        self.registracija_datum = ""
        self.osiguranje_datum = ""

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
            self.registracija_datum = podaci.get("registracija_datum", "")
            self.osiguranje_datum = podaci.get("osiguranje_datum", "")
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            pass

    def sacuvaj(self, user_data_dir):
        podaci = {
            "ime_prezime": self.ime_prezime,
            "telefon": self.telefon,
            "broj_licence": self.broj_licence,
            "tablice": self.tablice,
            "vozilo": self.vozilo,
            "registracija_datum": self.registracija_datum,
            "osiguranje_datum": self.osiguranje_datum,
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


grafik_zarade.poveži_valutu(formatiraj_cenu)


# ============================================================
# BACKUP - trajno cuvanje voznji van aplikacije (prezivi
# deinstalaciju i promenu telefona)
# ============================================================

BACKUP_FOLDER_NAZIV = "TaksiApp"
# BACKUP_FAJL_NAZIV je premesten u ekran_backup.py (jedino mesto gde se koristi)


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


def _stavke_izmedju(stavke, pocetak_str, kraj_str):
    """Filtrira listu stavki (gorivo ili servis) po polju 'datum' - vraca
    samo one izmedju pocetak_str i kraj_str (format GGGG-MM-DD), oba
    kraja ukljucena. Poredjenje teksta radi ispravno jer je format
    datuma takav da abecedno poredjenje odgovara hronoloskom."""
    return [
        s for s in stavke
        if s.get("datum") and pocetak_str <= s["datum"] <= kraj_str
    ]


def _izracunaj_potrosnju_intervale(sve_stavke_goriva):
    """Racuna potrosnju goriva (l/100km) izmedju uzastopnih sipanja, na
    osnovu kilometraze sa pumpe (km_pumpe). Uzima se CELA istorija
    goriva (ne samo izabrani period) da bi se ispravno uparila dva
    uzastopna sipanja, cak i kad jedno od njih pada van perioda.

    Vraca listu recnika sa kljucevima: datum, km_predjeno, litara,
    potrosnja (l/100km), cena. 'datum' je datum DRUGOG (kasnijeg) od
    dva uzastopna sipanja - to je datum kad je taj interval "zavrsen".

    Sipanja bez upisane kilometraze (km_pumpe) se preskacu - ne mogu
    uci u racunicu jer nemaju tacku od koje bi se merila predjena
    kilometraza."""
    sa_km = [s for s in sve_stavke_goriva if s.get("km_pumpe")]
    sa_km.sort(key=lambda s: (s["km_pumpe"], s.get("datum", "")))

    intervali = []
    for prethodno, trenutno in zip(sa_km, sa_km[1:]):
        km_predjeno = trenutno["km_pumpe"] - prethodno["km_pumpe"]
        if km_predjeno <= 0:
            continue
        litara = trenutno.get("litara", 0)
        intervali.append({
            "datum": trenutno.get("datum", "-"),
            "km_predjeno": km_predjeno,
            "litara": litara,
            "potrosnja": litara / km_predjeno * 100,
            "cena": trenutno.get("cena", 0),
        })
    return intervali


grafik_zarade.poveži_gorivo_servis(_stavke_izmedju, _izracunaj_potrosnju_intervale, GORIVO, SERVIS, TROSKOVI)






# Pamti sa kog je ekrana korisnik dosao kad PREVUCE prstom (swipe) u
# Podesavanja - da bi povratni swipe (udesno) vratio tacno tamo, a ne
# uvek na Pocetnu. Postavlja ga ScreenRoot.on_touch_up pri swipe-u;
# ostaje None ako je korisnik usao u Podesavanja preko obicnog dugmeta
# (u tom slucaju povratni swipe ide na Pocetnu).
EKRAN_PRE_PODESAVANJA = None


# ========================
# GPS VOZNJA - pomocne funkcije i cuvanje stanja aktivne voznje
# ========================



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

    dugmad_kolona = _BoxLayout(
        orientation="vertical",
        size_hint_x=None,
        size_hint_y=None,
        width=dp(84),
        spacing=dp(6),
    )
    # Visina kolone dugmadi RACUNA SE UNAPRED (broj dugmadi * njihova
    # visina + razmaci) - bitno kad ima vise od 2 dugmeta (npr. kod
    # dispecera: Pozovi/Smena/Izmeni/Obrisi), inace bi kolona bila visa
    # od kartice i dugmad bi se preklapala sa sledecim redom u listi.
    dugmad_kolona.height = (
        len(dugmad) * dp(38) + max(0, len(dugmad) - 1) * dp(6)
    )

    def _osvezi_velicinu(*_a):
        labela.text_size = (labela.width, None)
        labela.height = labela.texture_size[1]
        red.height = max(labela.height, dugmad_kolona.height) + dp(24)

    labela.bind(width=_osvezi_velicinu, texture_size=_osvezi_velicinu)
    red.add_widget(labela)

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
    LockScreen:
    HomeScreen:
    KalkulatorScreen:
    EvidencijaScreen:
    IzvestajScreen:
    PodesavanjaScreen:
    CenovnikScreen:
    NocnaTarifaScreen:
    GorivoScreen:
    ServisScreen:
    TroskoviScreen:
    GpsVoznjaScreen:
    NavigacijaScreen:
    GoogleApiScreen:
    ProfilScreen:
    ValutaScreen:
    JezikScreen:
    BackupScreen:
    IzvozPdfScreen:
    GrafikZaradeScreen:
    SigurnostScreen:
    UputstvoScreen:
    DispeceriScreen:

# ============================================================
# ZAJEDNICKI STIL - pastelne kartice, zaobljeni uglovi, tipografija
# ============================================================

<ScreenRoot>:
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

<TaxiZoranNaslov@FloatLayout>:
    size_hint_y: None
    height: dp(64)
    # Naslov "TAXI ZORAN" na pocetnom ekranu - centriran, sa efektom
    # dubine (3D): 3 sloja istog teksta, malo pomerena jedan od drugog,
    # od najtamnijeg (senka, u dnu) do najsvetlijeg zlatnog (na vrhu) -
    # to stvara utisak izdignutog/uklesanog zlatnog slova. Svaki sloj
    # ima velicinu roditelja (root.size) i centrira tekst unutar sebe
    # preko halign/valign - ovo je pouzdanije od rucnog pomeranja
    # centra, jer se ne oslanja na sirinu samog teksta.
    Label:
        text: "TAXI ZORAN"
        font_size: '28sp'
        bold: True
        size: root.size
        pos: root.x + dp(2.5), root.y - dp(2.5)
        halign: "center"
        valign: "middle"
        text_size: self.size
        color: 0.08, 0.04, 0.01, 0.85
    Label:
        text: "TAXI ZORAN"
        font_size: '28sp'
        bold: True
        size: root.size
        pos: root.x + dp(1.2), root.y - dp(1.2)
        halign: "center"
        valign: "middle"
        text_size: self.size
        color: 0.55, 0.30, 0.08, 1
    Label:
        text: "TAXI ZORAN"
        font_size: '28sp'
        bold: True
        size: root.size
        pos: root.pos
        halign: "center"
        valign: "middle"
        text_size: self.size
        color: 1, 0.83, 0.32, 1

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
    height: max(dp(72), label_menu_tekst.texture_size[1] + dp(24))
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
        id: label_menu_tekst
        text: root.tekst
        font_size: '17sp'
        bold: True
        color: 0.94, 0.93, 0.98, 1
        halign: "left"
        valign: "middle"
        text_size: self.width, None

<HomeMenuButton>:
    # Poseban izgled SAMO za Pocetni ekran - bez okvira/kutije oko
    # ikonice i teksta, veca kruzna ikonica na vrhu, tekst centriran
    # ispod (visina se racuna automatski prema duzini teksta, da
    # nijedan naziv ne bude odsecen). MenuButton (iznad) ostaje
    # nepromenjen i i dalje se koristi na ekranu Podesavanja.
    orientation: "vertical"
    size_hint_y: None
    height: self.minimum_height
    spacing: dp(4)
    padding: dp(4), dp(8)

    AnchorLayout:
        anchor_x: "center"
        anchor_y: "center"
        size_hint_y: None
        height: dp(74)

        BoxLayout:
            size_hint: None, None
            size: dp(74), dp(74)
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
        font_size: '16sp'
        bold: True
        color: 0.94, 0.93, 0.98, 1
        halign: "center"
        valign: "top"
        text_size: self.width, None
        size_hint_y: None
        height: self.texture_size[1] + dp(4)

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

        TaxiZoranNaslov:

        ScrollView:
            do_scroll_x: False
            GridLayout:
                cols: 2
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(14)
                padding: dp(2), dp(4)

                HomeMenuButton:
                    icon_src: "assets/icons/start_ride.png"
                    tekst: root.tekstovi.get("gps_auto", "")
                    on_release: app.root.current = "gps_voznja"

                HomeMenuButton:
                    icon_src: "assets/icons/end_ride.png"
                    tekst: root.tekstovi.get("manual_ride", "")
                    on_release: app.root.current = "kalkulator"

                HomeMenuButton:
                    icon_src: "assets/icons/history.png"
                    tekst: root.tekstovi.get("history", "")
                    on_release: app.root.current = "evidencija"

                HomeMenuButton:
                    icon_src: "assets/icons/daily_report.png"
                    tekst: root.tekstovi.get("report", "")
                    on_release: app.root.current = "izvestaj"

                HomeMenuButton:
                    icon_src: "assets/icons/profil.png"
                    tekst: root.tekstovi.get("profile", "")
                    on_release: app.root.current = "profil"

                HomeMenuButton:
                    icon_src: "assets/icons/settings.png"
                    tekst: root.tekstovi.get("settings", "")
                    on_release: app.root.current = "podesavanja"

                HomeMenuButton:
                    icon_src: "assets/icons/settings.png"
                    tekst: root.tekstovi.get("instructions", "")
                    on_release: app.root.current = "uputstvo"

# ============================================================
# PODESAVANJA
# ============================================================

<PodesavanjaScreen>:
    name: "podesavanja"
    ScreenRoot:

        TitleLabel:
            text: root.tekstovi.get("title", "")

        NavBar:
            RoundButton:
                label_text: root.tekstovi.get("home", "")
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"

        ScrollView:
            do_scroll_x: False
            GridLayout:
                cols: 2
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(14)
                padding: dp(2), dp(4)

                HomeMenuButton:
                    icon_src: "assets/icons/earnings_chart.png"
                    tekst: root.tekstovi.get("chart", "")
                    on_release: app.root.current = "grafik"

                HomeMenuButton:
                    icon_src: "assets/icons/navigation.png"
                    tekst: root.tekstovi.get("navigation", "")
                    on_release: app.root.current = "navigacija"

                HomeMenuButton:
                    icon_src: "assets/icons/night_tariff.png"
                    tekst: root.tekstovi.get("night_tariff", "")
                    on_release: app.root.current = "nocna_tarifa"

                HomeMenuButton:
                    icon_src: "assets/icons/service.png"
                    tekst: root.tekstovi.get("service", "")
                    on_release: app.root.current = "servis"

                HomeMenuButton:
                    icon_src: "assets/icons/fuel.png"
                    tekst: root.tekstovi.get("fuel", "")
                    on_release: app.root.current = "gorivo"

                HomeMenuButton:
                    icon_src: "assets/icons/calculator.png"
                    tekst: root.tekstovi.get("other_costs", "")
                    on_release: app.root.current = "troskovi"

                HomeMenuButton:
                    icon_src: "assets/icons/weekly_report.png"
                    tekst: root.tekstovi.get("weekly_report", "")
                    on_release: app.root.current = "izvestaj"

                HomeMenuButton:
                    icon_src: "assets/icons/monthly_report.png"
                    tekst: root.tekstovi.get("monthly_report", "")
                    on_release: app.root.current = "izvestaj"

                HomeMenuButton:
                    icon_src: "assets/icons/calculator.png"
                    tekst: root.tekstovi.get("calculator", "")
                    on_release: app.root.current = "kalkulator"

                HomeMenuButton:
                    icon_src: "assets/icons/profil.png"
                    tekst: root.tekstovi.get("profile", "")
                    on_release: app.root.current = "profil"

                HomeMenuButton:
                    icon_src: "assets/icons/poziv.png"
                    tekst: root.tekstovi.get("dispatcher", "")
                    on_release: app.root.current = "poziv"

                HomeMenuButton:
                    icon_src: "assets/icons/settings.png"
                    tekst: root.tekstovi.get("prices", "")
                    on_release: app.root.current = "cene"

                HomeMenuButton:
                    icon_src: "assets/icons/settings.png"
                    tekst: root.tekstovi.get("google_api", "")
                    on_release: app.root.current = "google_api"

                HomeMenuButton:
                    icon_src: "assets/icons/settings.png"
                    tekst: root.tekstovi.get("currency", "")
                    on_release: app.root.current = "valuta"

                HomeMenuButton:
                    icon_src: "assets/icons/settings.png"
                    tekst: root.tekstovi.get("language", "")
                    on_release: app.root.current = "jezik"

                HomeMenuButton:
                    icon_src: "assets/icons/settings.png"
                    tekst: root.tekstovi.get("backup", "")
                    on_release: app.root.current = "backup"

                HomeMenuButton:
                    icon_src: "assets/icons/settings.png"
                    tekst: root.tekstovi.get("security", "")
                    on_release: app.root.current = "sigurnost"

# NavigacijaScreen, GoogleApiScreen, ProfilScreen, ValutaScreen su
# izdvojeni u ekran_navigacija.py / ekran_google_api.py /
# ekran_profil.py / ekran_valuta.py (KV deo se dodaje nize, u
# TaksiApp.build()).

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


class HomeMenuButton(ButtonBehavior, BoxLayout):
    """Isti princip kao MenuButton (ikonica + tekst + klik za prelazak
    na drugi ekran), samo drugaciji izgled - koristi se ISKLJUCIVO na
    Pocetnom ekranu. Vidi <HomeMenuButton>: pravilo u KV-u."""
    icon_src = StringProperty("")
    tekst = StringProperty("")




class ScreenRoot(BoxLayout):
    """Osnovni kontejner svakog ekrana (izgled - pozadina, padding -
    je i dalje definisan u <ScreenRoot>: pravilu u KV-u). Ovde se
    dodaje SAMO hvatanje horizontalnog prevlacenja prstom (swipe) kao
    precica izmedju trenutnog ekrana i Podesavanja:

      - Swipe ULEVO (bilo gde, osim na ekranu zakljucavanja i vec u
        Podesavanjima) -> otvara Podesavanja, pamteci u
        EKRAN_PRE_PODESAVANJA sa kog si ekrana dosao.
      - Swipe UDESNO, dok si u Podesavanjima -> vraca te NAZAD na taj
        upamceni ekran (ne uvek na Pocetnu) - ako si usao u
        Podesavanja preko obicnog dugmeta (ne swipe-om), vraca na
        Pocetnu, jer tada EKRAN_PRE_PODESAVANJA nije postavljen.

    Sve ostalo (dugmad, NavBar, skrolovanje) ostaje potpuno
    nepromenjeno - super().on_touch_up() se poziva PRVI, pa ako neki
    dugme/ScrollView vec obradi dodir, swipe provera se uopste ne
    izvrsava.
    """

    PRAG_SWIPE = dp(60)  # minimalna horizontalna distanca da se racuna kao swipe

    def on_touch_up(self, touch):
        if super().on_touch_up(touch):
            return True

        dx = touch.x - touch.ox
        dy = touch.y - touch.oy

        if abs(dx) < self.PRAG_SWIPE or abs(dx) < abs(dy) * 1.5:
            return False

        app = App.get_running_app()
        if app is None or app.root is None:
            return False
        manager = app.root
        trenutni = manager.current

        if trenutni == "lock":
            return False

        global EKRAN_PRE_PODESAVANJA

        if dx < 0:
            if trenutni == "podesavanja":
                return False
            EKRAN_PRE_PODESAVANJA = trenutni
            manager.transition.direction = "left"
            manager.current = "podesavanja"
            return True
        else:
            if trenutni != "podesavanja":
                return False
            manager.transition.direction = "right"
            manager.current = EKRAN_PRE_PODESAVANJA or "home"
            return True


class HomeScreen(Screen):
    tekstovi = DictProperty({})

    def on_pre_enter(self, *args):
        self.osvezi_tekstove()

    def osvezi_tekstove(self):
        app = App.get_running_app()
        jezik = getattr(app, "jezik", "sr") if app else "sr"
        self.tekstovi = {
            "gps_auto": i18n.prevedi(jezik, "home_gps_auto"),
            "manual_ride": i18n.prevedi(jezik, "home_manual_ride"),
            "history": i18n.prevedi(jezik, "home_history"),
            "report": i18n.prevedi(jezik, "home_report"),
            "profile": i18n.prevedi(jezik, "home_profile"),
            "settings": i18n.prevedi(jezik, "home_settings"),
            "instructions": i18n.prevedi(jezik, "home_instructions"),
        }






class PodesavanjaScreen(Screen):
    tekstovi = DictProperty({})

    def on_pre_enter(self, *args):
        self.osvezi_tekstove()

    def osvezi_tekstove(self):
        app = App.get_running_app()
        jezik = getattr(app, "jezik", "sr") if app else "sr"
        self.tekstovi = {
            "title": i18n.prevedi(jezik, "settings_title"),
            "home": i18n.prevedi(jezik, "nav_home"),
            "chart": i18n.prevedi(jezik, "settings_chart"),
            "navigation": i18n.prevedi(jezik, "settings_navigation"),
            "night_tariff": i18n.prevedi(jezik, "settings_night_tariff"),
            "service": i18n.prevedi(jezik, "settings_service"),
            "fuel": i18n.prevedi(jezik, "settings_fuel"),
            "other_costs": i18n.prevedi(jezik, "settings_other_costs"),
            "weekly_report": i18n.prevedi(jezik, "settings_weekly_report"),
            "monthly_report": i18n.prevedi(jezik, "settings_monthly_report"),
            "calculator": i18n.prevedi(jezik, "settings_calculator"),
            "profile": i18n.prevedi(jezik, "settings_profile"),
            "dispatcher": i18n.prevedi(jezik, "settings_dispatcher"),
            "prices": i18n.prevedi(jezik, "settings_prices"),
            "google_api": i18n.prevedi(jezik, "settings_google_api"),
            "currency": i18n.prevedi(jezik, "settings_currency"),
            "language": i18n.prevedi(jezik, "settings_language"),
            "backup": i18n.prevedi(jezik, "settings_backup"),
            "security": i18n.prevedi(jezik, "settings_security"),
        }


class PlaceholderScreen(Screen):
    naslov = StringProperty("")























# NavigacijaScreen -> ekran_navigacija.py
# GoogleApiScreen -> ekran_google_api.py
# ProfilScreen (+ _dani_do_isteka, _stanje_dokumenata_vozila) -> ekran_profil.py
# ValutaScreen -> ekran_valuta.py














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


ekran_navigacija.poveži_popup(_prikazi_popup_poruku)
ekran_google_api.poveži(API, _prikazi_popup_poruku)
ekran_profil.poveži(VOZAC, _prikazi_popup_poruku)
ekran_valuta.poveži(KURS, _prikazi_popup_poruku)
ekran_uputstvo.poveži(
    _registruj_font_za_pdf, _ima_dozvolu_svi_fajlovi,
    _putanja_backup_foldera, _prikazi_popup_poruku,
)
ekran_dispeceri.poveži(DISPECERI, napravi_red_liste, _prikazi_popup_poruku)
ekran_backup.poveži(
    VOZAC, GORIVO, SERVIS, TROSKOVI,
    _ima_dozvolu_svi_fajlovi, _zatrazi_dozvolu_svi_fajlovi,
    _putanja_backup_foldera, _prikazi_popup_poruku,
)
ekran_izvoz.poveži(
    GORIVO, SERVIS, TROSKOVI, VOZAC,
    formatiraj_cenu, _stavke_izmedju, _izracunaj_potrosnju_intervale,
    _registruj_font_za_pdf, _ima_dozvolu_svi_fajlovi,
    _putanja_backup_foldera, _prikazi_popup_poruku,
)
ekran_cenovnik.poveži(CENE, _prikazi_popup_poruku)
ekran_gorivo.poveži(GORIVO, formatiraj_cenu, napravi_red_liste, _prikazi_popup_poruku)
ekran_servis.poveži(SERVIS, GORIVO, formatiraj_cenu, napravi_red_liste, _prikazi_popup_poruku)
ekran_troskovi.poveži(TROSKOVI, formatiraj_cenu, napravi_red_liste, _prikazi_popup_poruku)
ekran_kalkulator.poveži(DEFAULT_TARIFE, CENE, formatiraj_cenu, _prikazi_popup_poruku)
ekran_evidencija.poveži(formatiraj_cenu, napravi_red_liste, _prikazi_popup_poruku)
ekran_izvestaj.poveži(
    GORIVO, SERVIS, TROSKOVI,
    _stavke_izmedju, _izracunaj_potrosnju_intervale,
    formatiraj_cenu, napravi_red_liste,
)
ekran_gps_voznja.poveži(CENE, API, formatiraj_cenu, _prikazi_popup_poruku)


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
    jezik = StringProperty("sr")

    def postavi_jezik(self, jezik):
        if jezik not in i18n.SUPPORTED_LANGUAGES:
            return
        self.jezik = jezik
        JEZIK.jezik = jezik
        JEZIK.sacuvaj(self.user_data_dir)
        self.osvezi_tekstove_ekrana()

    def osvezi_tekstove_ekrana(self, manager=None):
        sm = manager or self.root
        if sm is None:
            return
        for ekran in sm.screens:
            osvezi = getattr(ekran, "osvezi_tekstove", None)
            if callable(osvezi):
                osvezi()

    def build(self):
        # Globalni hvatac neuhvacenih gresaka posle pokretanja (npr. u dugmadima)
        sys.excepthook = self._globalna_greska

        self.title = "Taksi App"
        try:
            db.init_db()
            CENE.ucitaj(self.user_data_dir)
            GORIVO.ucitaj(self.user_data_dir)
            SERVIS.ucitaj(self.user_data_dir)
            TROSKOVI.ucitaj(self.user_data_dir)
            ekran_servis.SERVIS_PODSETNIK.ucitaj(self.user_data_dir)
            ekran_gps_voznja.AKTIVNA_VOZNJA.ucitaj(self.user_data_dir)
            API.ucitaj(self.user_data_dir)
            VOZAC.ucitaj(self.user_data_dir)
            KURS.ucitaj(self.user_data_dir)
            JEZIK.ucitaj(self.user_data_dir)
            self.jezik = JEZIK.jezik
            ekran_sigurnost.SIGURNOST.ucitaj(self.user_data_dir)
            DISPECERI.ucitaj(self.user_data_dir)
            ekran_dispeceri.SMENE.ucitaj(self.user_data_dir)
            # Kurs se povlaci sa interneta u pozadini (posebna nit), da
            # app ne "visi" na pokretanju ako je internet spor ili ga
            # nema - u tom slucaju samo ostaje poslednji sacuvani kurs.
            threading.Thread(
                target=lambda: KURS.osvezi_ako_treba(self.user_data_dir),
                daemon=True,
            ).start()
            root = Builder.load_string(
                KV
                + grafik_zarade.GRAFIK_KV
                + ekran_navigacija.NAVIGACIJA_KV
                + ekran_google_api.GOOGLE_API_KV
                + ekran_profil.PROFIL_KV
                + ekran_valuta.VALUTA_KV
                + ekran_jezik.JEZIK_KV
                + ekran_sigurnost.SIGURNOST_KV
                + ekran_uputstvo.UPUTSTVO_KV
                + ekran_dispeceri.DISPECERI_KV
                + ekran_backup.BACKUP_KV
                + ekran_izvoz.IZVOZ_KV
                + ekran_cenovnik.CENOVNIK_KV
                + ekran_gorivo.GORIVO_KV
                + ekran_servis.SERVIS_KV
                + ekran_troskovi.TROSKOVI_KV
                + ekran_kalkulator.KALKULATOR_KV
                + ekran_evidencija.EVIDENCIJA_KV
                + ekran_izvestaj.IZVESTAJ_KV
                + ekran_gps_voznja.GPS_VOZNJA_KV
            )
            self.osvezi_tekstove_ekrana(root)
            # Provera zakljucavanja (otisak) se pokrece tek NAKON sto je
            # citav ScreenManager sagradjen (vidi napomenu u
            # LockScreen.pokusaj_ili_preskoci) - zato ide kroz
            # Clock.schedule_once, a ne odmah ovde.
            Clock.schedule_once(
                lambda dt: root.get_screen("lock").pokusaj_ili_preskoci()
            )
            # Automatski dnevni backup (tih, bez poruka) - pokrece se
            # 3 sekunde posle starta, da ne uspori pokretanje app-a i
            # da saceka da se ekran zakljucavanja resi.
            Clock.schedule_once(ekran_backup._auto_backup_ako_treba, 3)
            return root
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
            if not ekran_gps_voznja.AKTIVNA_VOZNJA.aktivna:
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
