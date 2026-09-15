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
import glob
from datetime import datetime, timedelta

from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.app import App
from kivy.clock import Clock

from servisi import database as db
from servisi import jezici

try:
    from androidstorage4kivy import SharedStorage, ShareSheet
    _DELJENJE_DOSTUPNO = True
except Exception:
    _DELJENJE_DOSTUPNO = False


BACKUP_PREFIX = "backup_taksi"
BACKUP_FAJL_NAZIV = "backup_taksi.json"  # stari, fiksni naziv - i dalje se
                                          # prepoznaje pri ucitavanju/deljenju
                                          # radi kompatibilnosti sa backupima
                                          # napravljenim pre ove izmene.


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


def _novo_ime_backupa():
    """Svaki backup dobija JEDINSTVENO ime sa datumom i vremenom (npr.
    backup_taksi_2026-09-11_143045.json), da se stari backupi NE
    prepisuju - ostaju svi u folderu, po datumu kad su napravljeni."""
    vreme = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    return f"{BACKUP_PREFIX}_{vreme}.json"


def _svi_backup_fajlovi(folder):
    """Vraca sve backup fajlove u folderu (i stari fiksni naziv i novi
    format sa datumom), sortirane od NAJNOVIJEG ka najstarijem."""
    obrazac = os.path.join(folder, f"{BACKUP_PREFIX}*.json")
    fajlovi = glob.glob(obrazac)
    fajlovi.sort(key=os.path.getmtime, reverse=True)
    return fajlovi


def _najnoviji_backup_fajl(folder):
    """Vraca putanju najnovijeg backup fajla u folderu, ili None ako
    nijedan ne postoji."""
    fajlovi = _svi_backup_fajlovi(folder)
    return fajlovi[0] if fajlovi else None


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
    putanja = os.path.join(folder, _novo_ime_backupa())
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
        folder = _PUTANJA_BACKUP_FOLDERA()
        najnoviji = _najnoviji_backup_fajl(folder)
        if najnoviji is not None:
            poslednja_izmena = datetime.fromtimestamp(os.path.getmtime(najnoviji))
            if datetime.now() - poslednja_izmena < timedelta(hours=24):
                return
        _sacuvaj_backup_fajl()
    except Exception:
        pass


class BackupScreen(Screen):
    tekst_status = StringProperty("")

    tekst_naslov = StringProperty("Backup podataka")
    tekst_pocetna = StringProperty("Pocetna")
    tekst_podesavanja = StringProperty("Podesavanja")
    tekst_napomena_gore = StringProperty("")
    tekst_odobri_pristup = StringProperty("Odobri pristup fajlovima")
    tekst_napomena_auto = StringProperty("")
    tekst_sacuvaj_backup = StringProperty("Sacuvaj backup sada")
    tekst_vrati_podatke = StringProperty("Vrati podatke iz backupa")
    tekst_podeli_backup = StringProperty("Podeli backup (Drive, WhatsApp...)")
    tekst_napomena_dole = StringProperty("")

    def on_pre_enter(self, *args):
        self._osvezi_prevod()
        self._osvezi_status()

    def _osvezi_prevod(self):
        self.tekst_naslov = jezici._t("backup.naslov")
        self.tekst_pocetna = jezici._t("buttons.pocetna")
        self.tekst_podesavanja = jezici._t("home.podesavanja")
        self.tekst_napomena_gore = jezici._t("backup.napomena_gore")
        self.tekst_odobri_pristup = jezici._t("backup.odobri_pristup")
        self.tekst_napomena_auto = jezici._t("backup.napomena_auto")
        self.tekst_sacuvaj_backup = jezici._t("backup.sacuvaj_backup_sada")
        self.tekst_vrati_podatke = jezici._t("backup.vrati_podatke")
        self.tekst_podeli_backup = jezici._t("backup.podeli_backup")
        self.tekst_napomena_dole = jezici._t("backup.napomena_dole")

    def _osvezi_status(self):
        folder = _PUTANJA_BACKUP_FOLDERA()
        if _IMA_DOZVOLU_SVI_FAJLOVI():
            dozvola_txt = jezici._t("backup.dozvola_da")
        else:
            dozvola_txt = jezici._t("backup.dozvola_ne")

        try:
            broj = db.broj_voznji()
        except Exception:
            broj = "?"

        vozac_txt = jezici._t("backup.popunjeni") if _VOZAC_REF.ime_prezime else jezici._t("backup.nisu_popunjeni")

        svi_backupi = _svi_backup_fajlovi(folder)
        if svi_backupi:
            backup_txt = jezici._t(
                "backup.backup_broj_format", broj=len(svi_backupi), naziv=os.path.basename(svi_backupi[0])
            )
        else:
            backup_txt = jezici._t("backup.nema_backupa")

        self.tekst_status = jezici._t(
            "backup.status_format",
            dozvola=dozvola_txt, folder=folder, backup_info=backup_txt,
            broj=broj, gorivo=len(_GORIVO_REF.stavke), servis=len(_SERVIS_REF.stavke),
            troskovi=len(_TROSKOVI_REF.stavke), vozac=vozac_txt,
        )

    def zatrazi_dozvolu(self):
        _ZATRAZI_DOZVOLU_SVI_FAJLOVI()
        Clock.schedule_once(lambda dt: self._osvezi_status(), 1)

    def sacuvaj_backup(self):
        if not _IMA_DOZVOLU_SVI_FAJLOVI():
            _PRIKAZI_POPUP(
                jezici._t("backup.nedostaje_dozvola_naslov"),
                jezici._t("backup.nedostaje_dozvola_poruka"),
                size_hint=(0.88, 0.4),
            )
            return
        try:
            putanja, podaci_voznje = _sacuvaj_backup_fajl()
            _PRIKAZI_POPUP(
                jezici._t("backup.sacuvano_naslov"),
                jezici._t(
                    "backup.sacuvano_poruka",
                    broj_voznji=len(podaci_voznje), gorivo=len(_GORIVO_REF.stavke),
                    servis=len(_SERVIS_REF.stavke), troskovi=len(_TROSKOVI_REF.stavke),
                    putanja=putanja,
                ),
                size_hint=(0.88, 0.55),
            )
        except Exception as e:
            _PRIKAZI_POPUP(
                jezici._t("profil.greska"), jezici._t("backup.backup_neuspeo_poruka", greska=e), size_hint=(0.88, 0.4)
            )
        self._osvezi_status()

    def ucitaj_backup(self):
        if not _IMA_DOZVOLU_SVI_FAJLOVI():
            _PRIKAZI_POPUP(
                jezici._t("backup.nedostaje_dozvola_naslov"),
                jezici._t("backup.nedostaje_dozvola_poruka"),
                size_hint=(0.88, 0.4),
            )
            return

        folder = _PUTANJA_BACKUP_FOLDERA()
        putanja = _najnoviji_backup_fajl(folder)
        if putanja is None:
            _PRIKAZI_POPUP(
                jezici._t("backup.nema_backup_fajla_naslov"),
                jezici._t("backup.nema_backup_fajla_poruka", folder=folder),
                size_hint=(0.88, 0.5),
            )
            return
        try:
            with open(putanja, "r", encoding="utf-8") as f:
                podaci = json.load(f)
        except Exception as e:
            _PRIKAZI_POPUP(
                jezici._t("profil.greska"), jezici._t("backup.citanje_neuspesno", greska=e), size_hint=(0.88, 0.4)
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
            jezici._t("backup.vraceno_naslov"),
            jezici._t(
                "backup.vraceno_poruka",
                naziv=os.path.basename(putanja), dodato=dodato, preskoceno=preskoceno,
                gorivo=dodato_gorivo, servisi=dodato_servisi, troskovi=dodato_troskovi,
                vozac_status=jezici._t("backup.azurirani") if vozac_podaci else jezici._t("backup.nije_bilo_backupu"),
            ),
            size_hint=(0.88, 0.6),
        )
        self._osvezi_status()

    def podeli_backup(self):
        """Otvara Android-ov sistemski meni za deljenje (isti koji se
        koristi za deljenje slika) sa backup fajlom - korisnik bira
        Google Drive, WhatsApp, email, itd. Ne zahteva prijavu ni na
        jedan nalog unutar ove aplikacije."""
        if not _DELJENJE_DOSTUPNO:
            _PRIKAZI_POPUP(
                jezici._t("backup.deljenje_nedostupno_naslov"),
                jezici._t("backup.deljenje_nedostupno_poruka"),
                size_hint=(0.85, 0.35),
            )
            return

        folder = _PUTANJA_BACKUP_FOLDERA()
        putanja = _najnoviji_backup_fajl(folder)
        if putanja is None:
            _PRIKAZI_POPUP(
                jezici._t("backup.nema_backup_fajla_naslov"),
                jezici._t("backup.nema_backupa_deljenje_poruka"),
                size_hint=(0.85, 0.4),
            )
            return

        try:
            app = App.get_running_app()
            # SharedStorage ocekuje fajl iz privatnog prostora aplikacije,
            # a nas backup je u javnom Download folderu - zato prvo
            # napravimo privatnu kopiju, pa nju delimo.
            privatna_kopija = os.path.join(app.user_data_dir, os.path.basename(putanja))
            shutil.copyfile(putanja, privatna_kopija)

            skladiste = SharedStorage()
            deljeni_fajl = skladiste.copy_to_shared(privatna_kopija, collection="Documents")
            if deljeni_fajl is None:
                _PRIKAZI_POPUP(
                    jezici._t("profil.greska"), jezici._t("backup.deljenje_neuspelo"), size_hint=(0.85, 0.35)
                )
                return

            if getattr(self, "_share_sheet", None) is None:
                self._share_sheet = ShareSheet()
            self._share_sheet.share_file(deljeni_fajl)
        except Exception as e:
            _PRIKAZI_POPUP(
                jezici._t("profil.greska"), jezici._t("backup.deljenje_neuspelo_greska", greska=e), size_hint=(0.88, 0.4)
            )




BACKUP_KV = """
# ============================================================
# BACKUP - trajno cuvanje/vracanje voznji
# ============================================================

<BackupScreen>:
    name: "backup"
    ScreenRoot:

        TitleLabel:
            text: root.tekst_naslov

        NavBar:
            RoundButton:
                label_text: root.tekst_pocetna
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: root.tekst_podesavanja
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
                    text: root.tekst_napomena_gore

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
                    label_text: root.tekst_odobri_pristup
                    tint: 0.36, 0.46, 0.64, 1
                    text_color: 1, 1, 1, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.zatrazi_dozvolu()

                FieldLabel:
                    text: root.tekst_napomena_auto
                    size_hint_y: None
                    height: dp(70)
                    text_size: self.width, None

                RoundButton:
                    label_text: root.tekst_sacuvaj_backup
                    tint: 0.30, 0.52, 0.36, 1
                    text_color: 1, 1, 1, 1
                    size_hint_y: None
                    height: dp(56)
                    on_release: root.sacuvaj_backup()

                RoundButton:
                    label_text: root.tekst_vrati_podatke
                    tint: 0.55, 0.38, 0.26, 1
                    text_color: 1, 1, 1, 1
                    size_hint_y: None
                    height: dp(56)
                    on_release: root.ucitaj_backup()

                RoundButton:
                    label_text: root.tekst_podeli_backup
                    tint: 0.30, 0.40, 0.58, 1
                    text_color: 1, 1, 1, 1
                    size_hint_y: None
                    height: dp(56)
                    on_release: root.podeli_backup()

                FieldLabel:
                    text: root.tekst_napomena_dole
                    size_hint_y: None
                    height: dp(90)
                    text_size: self.width, None


"""
