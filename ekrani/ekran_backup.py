"""
ekran_backup.py
Backup podataka - cuvanje/vracanje SVIH podataka (voznje, gorivo,
servisi, troskovi, profil vozaca) u jedan fajl van same aplikacije
(Preuzimanja/TaksiApp), plus deljenje tog fajla (Drive, WhatsApp...).

Izdvojeno iz main.py - isti obrazac kao grafik_zarade.py.
"""

import os
import json
import shutil

from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.app import App
from kivy.clock import Clock

from servisi import database as db

try:
    from androidstorage4kivy import SharedStorage, ShareSheet
    _DELJENJE_DOSTUPNO = True
except Exception:
    _DELJENJE_DOSTUPNO = False


BACKUP_FAJL_NAZIV = "backup_taksi.json"


# ============================================================
# main.py ovo postavlja posle uvoza (izbegava kruzni import)
# ============================================================

_VOZAC_REF = None                  # main._VOZAC_REF
_GORIVO_REF = None                 # main._GORIVO_REF
_SERVIS_REF = None                 # main._SERVIS_REF
_TROSKOVI_REF = None               # main._TROSKOVI_REF
_IMA_DOZVOLU_SVI_FAJLOVI = None    # main._ima_dozvolu_svi_fajlovi
_ZATRAZI_DOZVOLU_SVI_FAJLOVI = None  # main._zatrazi_dozvolu_svi_fajlovi
_PUTANJA_BACKUP_FOLDERA = None     # main._putanja_backup_foldera
_PRIKAZI_POPUP = None              # main._prikazi_popup_poruku


def poveži(vozac_obj, gorivo_obj, servis_obj, troskovi_obj,
           ima_dozvolu_fn, zatrazi_dozvolu_fn, putanja_backup_fn, prikazi_popup_fn):
    """main.py poziva ovo jednom, odmah posle 'import ekran_backup'."""
    global _VOZAC_REF, _GORIVO_REF, _SERVIS_REF, _TROSKOVI_REF
    global _IMA_DOZVOLU_SVI_FAJLOVI, _ZATRAZI_DOZVOLU_SVI_FAJLOVI, _PUTANJA_BACKUP_FOLDERA, _PRIKAZI_POPUP
    _VOZAC_REF = vozac_obj
    _GORIVO_REF = gorivo_obj
    _SERVIS_REF = servis_obj
    _TROSKOVI_REF = troskovi_obj
    _IMA_DOZVOLU_SVI_FAJLOVI = ima_dozvolu_fn
    _ZATRAZI_DOZVOLU_SVI_FAJLOVI = zatrazi_dozvolu_fn
    _PUTANJA_BACKUP_FOLDERA = putanja_backup_fn
    _PRIKAZI_POPUP = prikazi_popup_fn


def _stavka_bez_id(stavka):
    """Vraca kopiju stavke (gorivo/servis) bez 'id' kljuca - koristi se
    da se dve stavke uporede po sadrzaju, bez obzira na to koji im je
    id dodeljen (jer se id razlikuje izmedju telefona)."""
    return {k: v for k, v in stavka.items() if k != "id"}


def _dodaj_stavke_bez_duplikata(log_obj, user_data_dir, nove_stavke):
    """Dodaje stavke iz backupa (gorivo ili servis) u JsonLog, preskacuci
    one koje po sadrzaju vec postoje (da se backup moze ucitati vise puta
    bez pravljenja duplikata). Vraca broj stvarno dodatih stavki."""
    postojece_bez_id = [_stavka_bez_id(s) for s in log_obj.stavke]
    dodato = 0
    for nova in nove_stavke:
        bez_id = _stavka_bez_id(nova)
        if bez_id in postojece_bez_id:
            continue
        log_obj.dodaj(user_data_dir, dict(bez_id))
        postojece_bez_id.append(bez_id)
        dodato += 1
    return dodato


def _sacuvaj_backup_fajl():
    """Upisuje trenutne podatke (voznje, vozac, gorivo, servisi,
    troskovi) u backup fajl. Koristi ga i rucno dugme 'Sacuvaj backup
    sada' i automatski dnevni backup, da se logika ne duplira negde.
    Vraca (putanja, podaci_voznje) ako uspe; baca izuzetak ako ne
    uspe (npr. nema dozvole za fajlove)."""
    voznje = db.sve_voznje_za_izvoz()
    podaci_voznje = [dict(v) for v in voznje]

    podaci_vozac = {
        "ime_prezime": _VOZAC_REF.ime_prezime,
        "telefon": _VOZAC_REF.telefon,
        "broj_licence": _VOZAC_REF.broj_licence,
        "tablice": _VOZAC_REF.tablice,
        "vozilo": _VOZAC_REF.vozilo,
        "registracija_datum": _VOZAC_REF.registracija_datum,
        "osiguranje_datum": _VOZAC_REF.osiguranje_datum,
    }

    podaci = {
        "voznje": podaci_voznje,
        "vozac": podaci_vozac,
        "gorivo": _GORIVO_REF.stavke,
        "servisi": _SERVIS_REF.stavke,
        "troskovi": _TROSKOVI_REF.stavke,
    }

    folder = _PUTANJA_BACKUP_FOLDERA()
    os.makedirs(folder, exist_ok=True)
    putanja = os.path.join(folder, BACKUP_FAJL_NAZIV)
    with open(putanja, "w", encoding="utf-8") as f:
        json.dump(podaci, f, ensure_ascii=False, indent=2)

    return putanja, podaci_voznje


def _auto_backup_ako_treba(*_args):
    """Ako je proslo vise od 24h od poslednjeg backupa (ili backup
    fajl uopste ne postoji), napravi novi backup automatski i TIHO
    (bez popup poruka) - poziva se jednom pri svakom pokretanju
    aplikacije (vidi TaksiApp.build). Ako nesto pukne (nema dozvole,
    baza jos nije spremna...), jednostavno preskace - automatski
    backup ne sme nikad da obori app niti da gnjavi korisnika
    porukama o gresci."""
    try:
        if not _IMA_DOZVOLU_SVI_FAJLOVI():
            return
        putanja = os.path.join(_PUTANJA_BACKUP_FOLDERA(), BACKUP_FAJL_NAZIV)
        if os.path.exists(putanja):
            poslednja_izmena = datetime.fromtimestamp(os.path.getmtime(putanja))
            if datetime.now() - poslednja_izmena < timedelta(hours=24):
                return
        _sacuvaj_backup_fajl()
    except Exception:
        pass


class BackupScreen(Screen):
    tekst_status = StringProperty("")

    def on_pre_enter(self, *args):
        self._osvezi_status()

    def _osvezi_status(self):
        putanja = os.path.join(_PUTANJA_BACKUP_FOLDERA(), BACKUP_FAJL_NAZIV)
        if _IMA_DOZVOLU_SVI_FAJLOVI():
            dozvola_txt = "Dozvola za fajlove: DA"
        else:
            dozvola_txt = "Dozvola za fajlove: NE (klikni dugme ispod)"

        try:
            broj = db.broj_voznji()
        except Exception:
            broj = "?"

        vozac_txt = "popunjeni" if _VOZAC_REF.ime_prezime else "nisu popunjeni"

        self.tekst_status = (
            f"{dozvola_txt}\n\n"
            f"Backup fajl se cuva ovde:\n{putanja}\n\n"
            f"Voznji trenutno u bazi: {broj}\n"
            f"Unosa goriva: {len(_GORIVO_REF.stavke)}\n"
            f"Unosa servisa: {len(_SERVIS_REF.stavke)}\n"
            f"Ostalih troskova: {len(_TROSKOVI_REF.stavke)}\n"
            f"Podaci o vozacu: {vozac_txt}"
        )

    def zatrazi_dozvolu(self):
        _ZATRAZI_DOZVOLU_SVI_FAJLOVI()
        Clock.schedule_once(lambda dt: self._osvezi_status(), 1)

    def sacuvaj_backup(self):
        if not _IMA_DOZVOLU_SVI_FAJLOVI():
            _PRIKAZI_POPUP(
                "Nedostaje dozvola",
                "Prvo klikni 'Odobri pristup fajlovima', potvrdi na sledecem "
                "ekranu, pa se vrati ovde i probaj ponovo.",
                size_hint=(0.88, 0.4),
            )
            return
        try:
            putanja, podaci_voznje = _sacuvaj_backup_fajl()
            _PRIKAZI_POPUP(
                "Sacuvano",
                f"Sacuvano u backup:\n"
                f"- {len(podaci_voznje)} voznji\n"
                f"- {len(_GORIVO_REF.stavke)} unosa goriva\n"
                f"- {len(_SERVIS_REF.stavke)} unosa servisa\n"
                f"- {len(_TROSKOVI_REF.stavke)} ostalih troskova\n"
                f"- podaci o vozacu\n\n"
                f"Fajl:\n{putanja}",
                size_hint=(0.88, 0.55),
            )
        except Exception as e:
            _PRIKAZI_POPUP(
                "Greska", f"Backup nije uspeo:\n{e}", size_hint=(0.88, 0.4)
            )
        self._osvezi_status()

    def ucitaj_backup(self):
        if not _IMA_DOZVOLU_SVI_FAJLOVI():
            _PRIKAZI_POPUP(
                "Nedostaje dozvola",
                "Prvo klikni 'Odobri pristup fajlovima', potvrdi na sledecem "
                "ekranu, pa se vrati ovde i probaj ponovo.",
                size_hint=(0.88, 0.4),
            )
            return

        putanja = os.path.join(_PUTANJA_BACKUP_FOLDERA(), BACKUP_FAJL_NAZIV)
        try:
            with open(putanja, "r", encoding="utf-8") as f:
                podaci = json.load(f)
        except FileNotFoundError:
            _PRIKAZI_POPUP(
                "Nema backup fajla",
                f"Nije pronadjen fajl:\n{putanja}\n\n"
                f"Prvo napravi backup na starom telefonu, pa taj fajl "
                f"prebaci u isti folder na ovom telefonu.",
                size_hint=(0.88, 0.5),
            )
            return
        except Exception as e:
            _PRIKAZI_POPUP(
                "Greska", f"Ne mogu da procitam backup:\n{e}", size_hint=(0.88, 0.4)
            )
            return

        # Stari backup fajlovi su bili obicna lista voznji (bez vozaca,
        # goriva i servisa) - ako je ucitani fajl takav, samo ga
        # "umotamo" u isti oblik kao novi format, da dole radi isti kod.
        if isinstance(podaci, list):
            podaci = {"voznje": podaci}

        voznje_podaci = podaci.get("voznje", [])
        vozac_podaci = podaci.get("vozac")
        gorivo_podaci = podaci.get("gorivo", [])
        servisi_podaci = podaci.get("servisi", [])
        troskovi_podaci = podaci.get("troskovi", [])

        dodato = 0
        preskoceno = 0
        for v in voznje_podaci:
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

        app = App.get_running_app()

        if vozac_podaci:
            _VOZAC_REF.ime_prezime = vozac_podaci.get("ime_prezime", _VOZAC_REF.ime_prezime)
            _VOZAC_REF.telefon = vozac_podaci.get("telefon", _VOZAC_REF.telefon)
            _VOZAC_REF.broj_licence = vozac_podaci.get("broj_licence", _VOZAC_REF.broj_licence)
            _VOZAC_REF.tablice = vozac_podaci.get("tablice", _VOZAC_REF.tablice)
            _VOZAC_REF.vozilo = vozac_podaci.get("vozilo", _VOZAC_REF.vozilo)
            _VOZAC_REF.registracija_datum = vozac_podaci.get("registracija_datum", _VOZAC_REF.registracija_datum)
            _VOZAC_REF.osiguranje_datum = vozac_podaci.get("osiguranje_datum", _VOZAC_REF.osiguranje_datum)
            _VOZAC_REF.sacuvaj(app.user_data_dir)

        dodato_gorivo = _dodaj_stavke_bez_duplikata(_GORIVO_REF, app.user_data_dir, gorivo_podaci)
        dodato_servisi = _dodaj_stavke_bez_duplikata(_SERVIS_REF, app.user_data_dir, servisi_podaci)
        dodato_troskovi = _dodaj_stavke_bez_duplikata(_TROSKOVI_REF, app.user_data_dir, troskovi_podaci)

        _PRIKAZI_POPUP(
            "Vraceno iz backupa",
            f"Voznje - dodato: {dodato}, preskoceno (vec postoje): {preskoceno}\n"
            f"Gorivo - dodato novih unosa: {dodato_gorivo}\n"
            f"Servisi - dodato novih unosa: {dodato_servisi}\n"
            f"Ostali troskovi - dodato novih unosa: {dodato_troskovi}\n"
            f"Podaci o vozacu: {'azurirani' if vozac_podaci else 'nije bilo u ovom backupu'}",
            size_hint=(0.88, 0.55),
        )
        self._osvezi_status()

    def podeli_backup(self):
        """Otvara Android-ov sistemski meni za deljenje (isti koji se
        koristi za deljenje slika) sa backup fajlom - korisnik bira
        Google Drive, WhatsApp, email, itd. Ne zahteva prijavu ni na
        jedan nalog unutar ove aplikacije."""
        if not _DELJENJE_DOSTUPNO:
            _PRIKAZI_POPUP(
                "Nije dostupno",
                "Deljenje fajlova radi samo na Android telefonu.",
                size_hint=(0.85, 0.35),
            )
            return

        putanja = os.path.join(_PUTANJA_BACKUP_FOLDERA(), BACKUP_FAJL_NAZIV)
        if not os.path.exists(putanja):
            _PRIKAZI_POPUP(
                "Nema backup fajla",
                "Prvo napravi backup klikom na 'Sacuvaj backup sada', pa onda podeli.",
                size_hint=(0.85, 0.4),
            )
            return

        try:
            app = App.get_running_app()
            # SharedStorage ocekuje fajl iz privatnog prostora aplikacije,
            # a nas backup je u javnom Download folderu - zato prvo
            # napravimo privatnu kopiju, pa nju delimo.
            privatna_kopija = os.path.join(app.user_data_dir, BACKUP_FAJL_NAZIV)
            shutil.copyfile(putanja, privatna_kopija)

            skladiste = SharedStorage()
            deljeni_fajl = skladiste.copy_to_shared(privatna_kopija, collection="Documents")
            if deljeni_fajl is None:
                _PRIKAZI_POPUP(
                    "Greska", "Deljenje nije uspelo - probaj ponovo.", size_hint=(0.85, 0.35)
                )
                return

            if getattr(self, "_share_sheet", None) is None:
                self._share_sheet = ShareSheet()
            self._share_sheet.share_file(deljeni_fajl)
        except Exception as e:
            _PRIKAZI_POPUP(
                "Greska", f"Deljenje nije uspelo:\n{e}", size_hint=(0.88, 0.4)
            )




BACKUP_KV = """
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

        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(16)
                padding: dp(2), dp(4)

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

                FieldLabel:
                    text: "Automatski backup: app sam napravi svez backup jednom dnevno pri pokretanju (tiho, bez poruke) - dugme ispod je za rucni backup kad god zelis."
                    size_hint_y: None
                    height: dp(70)
                    text_size: self.width, None

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

                RoundButton:
                    label_text: "Podeli backup (Drive, WhatsApp...)"
                    tint: 0.30, 0.40, 0.58, 1
                    text_color: 1, 1, 1, 1
                    size_hint_y: None
                    height: dp(56)
                    on_release: root.podeli_backup()

                FieldLabel:
                    text: "Ako menjas telefon: napravi backup na starom, prebaci fajl (WhatsApp/Drive/USB) u isti folder na novom, instaliraj app, pa klikni 'Vrati podatke'."
                    size_hint_y: None
                    height: dp(90)
                    text_size: self.width, None


"""
