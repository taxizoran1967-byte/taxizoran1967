"""
ekran_dispeceri.py
Ekran "Poziv / Dispecer" - imenik dispecera sa smenama (1/2/3) i
vremenima smena.

Izdvojeno iz main.py - isti obrazac kao grafik_zarade.py.
"""

import os
import json
import webbrowser
from datetime import datetime, time as dt_time

from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.properties import StringProperty
from kivy.app import App
from kivy.clock import Clock

from servisi import jezici


# ============================================================
# main.py ovo postavlja posle uvoza (izbegava kruzni import)
# ============================================================

_DISPECERI_REF = None      # main.DISPECERI (JsonLog instanca), injektuje main.py
_NAPRAVI_RED_LISTE = None  # main.napravi_red_liste (deljeni helper), injektuje main.py
_PRIKAZI_POPUP = None      # main._prikazi_popup_poruku, injektuje main.py


def poveži(dispeceri_obj, napravi_red_liste_fn, prikazi_popup_fn):
    """main.py poziva ovo jednom, odmah posle 'import ekran_dispeceri'."""
    global _DISPECERI_REF, _NAPRAVI_RED_LISTE, _PRIKAZI_POPUP
    _DISPECERI_REF = dispeceri_obj
    _NAPRAVI_RED_LISTE = napravi_red_liste_fn
    _PRIKAZI_POPUP = prikazi_popup_fn



class SmenePodesavanja:
    """Vremenski opseg za tri smene dispecera (npr. Smena 1: 06:00-14:00).
    Koristi se da se pored imena dispecera prikaze zelena tacka ako mu
    je smena TRENUTNO aktivna (poredi se sa satom na telefonu)."""

    def __init__(self):
        self.smena1_od = "06:00"
        self.smena1_do = "14:00"
        self.smena2_od = "14:00"
        self.smena2_do = "22:00"
        self.smena3_od = "22:00"
        self.smena3_do = "06:00"

    def opseg(self, broj_smene):
        return getattr(self, f"smena{broj_smene}_od"), getattr(self, f"smena{broj_smene}_do")

    def _putanja(self, user_data_dir):
        return os.path.join(user_data_dir, "smene.json")

    def ucitaj(self, user_data_dir):
        try:
            with open(self._putanja(user_data_dir), "r", encoding="utf-8") as f:
                podaci = json.load(f)
            for kljuc in ("smena1_od", "smena1_do", "smena2_od", "smena2_do",
                          "smena3_od", "smena3_do"):
                if kljuc in podaci:
                    setattr(self, kljuc, podaci[kljuc])
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            pass

    def sacuvaj(self, user_data_dir):
        podaci = {
            "smena1_od": self.smena1_od, "smena1_do": self.smena1_do,
            "smena2_od": self.smena2_od, "smena2_do": self.smena2_do,
            "smena3_od": self.smena3_od, "smena3_do": self.smena3_do,
        }
        with open(self._putanja(user_data_dir), "w", encoding="utf-8") as f:
            json.dump(podaci, f, ensure_ascii=False, indent=2)


SMENE = SmenePodesavanja()


def _smena_aktivna_sada(od_str, do_str):
    """Da li je TRENUTNO vreme na telefonu unutar opsega od_str-do_str
    (format 'HH:MM'). Podrzava smenu koja prelazi preko ponoci (npr.
    22:00 do 06:00)."""
    try:
        sada = datetime.now().time()
        od_h, od_m = (int(x) for x in od_str.split(":"))
        do_h, do_m = (int(x) for x in do_str.split(":"))
        od_t = dt_time(od_h, od_m)
        do_t = dt_time(do_h, do_m)
    except (ValueError, AttributeError):
        return False

    if od_t <= do_t:
        return od_t <= sada <= do_t
    else:
        # smena prelazi preko ponoci (npr. 22:00 -> 06:00)
        return sada >= od_t or sada <= do_t


class DispeceriScreen(Screen):
    """Imenik dispecera - ime, telefon, smena (1/2/3). Pored svakog
    imena se prikazuje zelena/siva tacka zavisno od toga da li mu je
    smena TRENUTNO aktivna (poredi se sa vremenom na telefonu i sa
    opsezima iz SMENE)."""

    dugme_tekst = StringProperty("Dodaj dispecera")
    izmena_id = None

    smena1_od = StringProperty("06:00")
    smena1_do = StringProperty("14:00")
    smena2_od = StringProperty("14:00")
    smena2_do = StringProperty("22:00")
    smena3_od = StringProperty("22:00")
    smena3_do = StringProperty("06:00")

    tekst_naslov = StringProperty("Poziv / Dispecer")
    tekst_pocetna = StringProperty("Pocetna")
    tekst_podesavanja = StringProperty("Podesavanja")
    tekst_vreme_smena = StringProperty("Vreme smena")
    tekst_smena1_lbl = StringProperty("Smena 1")
    tekst_smena2_lbl = StringProperty("Smena 2")
    tekst_smena3_lbl = StringProperty("Smena 3")
    tekst_sacuvaj_vreme_smena = StringProperty("Sacuvaj vreme smena")
    tekst_ime_prezime_dispecera = StringProperty("Ime i prezime dispecera")
    hint_ime = StringProperty("npr. Marko Markovic")
    tekst_broj_telefona = StringProperty("Broj telefona")
    hint_telefon = StringProperty("npr. 0611234567")
    tekst_smena_label = StringProperty("Smena")

    _tajmer_osvezavanja = None

    def on_pre_enter(self, *args):
        self._osvezi_prevod()
        self.smena1_od, self.smena1_do = SMENE.smena1_od, SMENE.smena1_do
        self.smena2_od, self.smena2_do = SMENE.smena2_od, SMENE.smena2_do
        self.smena3_od, self.smena3_do = SMENE.smena3_od, SMENE.smena3_do
        self.ucitaj_dispecere()

    def _osvezi_prevod(self):
        self.tekst_naslov = jezici._t("dispeceri.naslov")
        self.tekst_pocetna = jezici._t("buttons.pocetna")
        self.tekst_podesavanja = jezici._t("home.podesavanja")
        self.tekst_vreme_smena = jezici._t("dispeceri.vreme_smena")
        self.tekst_smena1_lbl = jezici._t("dispeceri.smena_format", broj=1)
        self.tekst_smena2_lbl = jezici._t("dispeceri.smena_format", broj=2)
        self.tekst_smena3_lbl = jezici._t("dispeceri.smena_format", broj=3)
        self.tekst_sacuvaj_vreme_smena = jezici._t("dispeceri.sacuvaj_vreme_smena")
        self.tekst_ime_prezime_dispecera = jezici._t("dispeceri.ime_prezime_dispecera")
        self.hint_ime = jezici._t("dispeceri.ime_hint")
        self.tekst_broj_telefona = jezici._t("dispeceri.broj_telefona")
        self.hint_telefon = jezici._t("dispeceri.telefon_hint")
        self.tekst_smena_label = jezici._t("dispeceri.smena_label")
        self.dugme_tekst = (
            jezici._t("dispeceri.sacuvaj_izmenu") if self.izmena_id is not None
            else jezici._t("dispeceri.dodaj_dispecera")
        )
        spinner = self.ids.get("spinner_smena_dispecera")
        if spinner is not None:
            spinner.values = [jezici._t("dispeceri.smena_format", broj=n) for n in (1, 2, 3)]
            if not spinner.text or spinner.text not in spinner.values:
                spinner.text = spinner.values[0]

    def on_enter(self, *args):
        # osvezi zelenu/sivu tacku svakih 60s dok je ekran otvoren,
        # da se boja sama promeni kad smena istekne dok gledas ekran
        if self._tajmer_osvezavanja is None:
            self._tajmer_osvezavanja = Clock.schedule_interval(
                lambda dt: self.ucitaj_dispecere(), 60
            )

    def on_leave(self, *args):
        if self._tajmer_osvezavanja is not None:
            self._tajmer_osvezavanja.cancel()
            self._tajmer_osvezavanja = None

    def sacuvaj_smene(self):
        SMENE.smena1_od = self.ids.input_smena1_od.text.strip() or SMENE.smena1_od
        SMENE.smena1_do = self.ids.input_smena1_do.text.strip() or SMENE.smena1_do
        SMENE.smena2_od = self.ids.input_smena2_od.text.strip() or SMENE.smena2_od
        SMENE.smena2_do = self.ids.input_smena2_do.text.strip() or SMENE.smena2_do
        SMENE.smena3_od = self.ids.input_smena3_od.text.strip() or SMENE.smena3_od
        SMENE.smena3_do = self.ids.input_smena3_do.text.strip() or SMENE.smena3_do
        app = App.get_running_app()
        SMENE.sacuvaj(app.user_data_dir)
        self.smena1_od, self.smena1_do = SMENE.smena1_od, SMENE.smena1_do
        self.smena2_od, self.smena2_do = SMENE.smena2_od, SMENE.smena2_do
        self.smena3_od, self.smena3_do = SMENE.smena3_od, SMENE.smena3_do
        self.ucitaj_dispecere()

    def ucitaj_dispecere(self):
        kontejner = self.ids.lista_dispecera
        kontejner.clear_widgets()

        if not _DISPECERI_REF.stavke:
            kontejner.add_widget(Label(
                text=jezici._t("dispeceri.nema_dispecera"),
                size_hint_y=None, height=40,
                color=(1, 1, 1, 1),
            ))
            return

        for s in _DISPECERI_REF.stavke:
            kontejner.add_widget(self._napravi_red(s))

    def _napravi_red(self, s):
        smena = s.get("smena", 1)
        od_str, do_str = SMENE.opseg(smena)
        aktivna = _smena_aktivna_sada(od_str, do_str)
        tacka = "[color=39d353][b]*[/b][/color]" if aktivna else "[color=888888]*[/color]"
        status = jezici._t("dispeceri.aktivna_sada") if aktivna else jezici._t("dispeceri.nije_aktivna")
        opis = (
            f"{tacka} [b]{s.get('ime', '-')}[/b]\n"
            f"{s.get('telefon', '-')}\n"
            f"{jezici._t('dispeceri.red_opis', smena=smena, od=od_str, do=do_str, status=status)}"
        )
        return _NAPRAVI_RED_LISTE(
            opis,
            tint=(0.30, 0.29, 0.42, 0.92),
            boja_teksta=(0.95, 0.95, 1, 1),
            dugmad=[
                (jezici._t("dispeceri.pozovi"), (0.30, 0.52, 0.36, 1), (0.92, 1, 0.94, 1),
                 lambda inst, sid=s["id"]: self._pozovi(sid)),
                (jezici._t("dispeceri.sledeca_smena"), (0.55, 0.45, 0.20, 1), (1, 0.97, 0.90, 1),
                 lambda inst, sid=s["id"]: self._promeni_smenu(sid)),
                (jezici._t("evidencija.izmeni"), (0.36, 0.46, 0.64, 1), (0.95, 0.96, 1, 1),
                 lambda inst, sid=s["id"]: self._izmeni(sid)),
                (jezici._t("evidencija.obrisi"), (0.66, 0.30, 0.34, 1), (1, 0.95, 0.95, 1),
                 lambda inst, sid=s["id"]: self._obrisi(sid)),
            ],
        )

    def _pozovi(self, stavka_id):
        s = _DISPECERI_REF.nadji(stavka_id)
        if not s or not s.get("telefon"):
            return
        try:
            webbrowser.open(f"tel:{s['telefon']}")
        except Exception as e:
            _PRIKAZI_POPUP(jezici._t("profil.greska"), jezici._t("dispeceri.ne_mogu_poziv", greska=e))

    def _promeni_smenu(self, stavka_id):
        s = _DISPECERI_REF.nadji(stavka_id)
        if not s:
            return
        app = App.get_running_app()
        nova_smena = (s.get("smena", 1) % 3) + 1  # 1->2->3->1
        s["smena"] = nova_smena
        _DISPECERI_REF.azuriraj(app.user_data_dir, stavka_id, s)
        self.ucitaj_dispecere()

    def _izmeni(self, stavka_id):
        s = _DISPECERI_REF.nadji(stavka_id)
        if not s:
            return
        self.izmena_id = stavka_id
        self.ids.input_ime_dispecera.text = s.get("ime", "")
        self.ids.input_telefon_dispecera.text = s.get("telefon", "")
        self.ids.spinner_smena_dispecera.text = jezici._t("dispeceri.smena_format", broj=s.get('smena', 1))
        self.dugme_tekst = jezici._t("dispeceri.sacuvaj_izmenu")

    def _obrisi(self, stavka_id):
        app = App.get_running_app()
        _DISPECERI_REF.obrisi(app.user_data_dir, stavka_id)
        self.ucitaj_dispecere()

    def sacuvaj_dispecera(self):
        ime = self.ids.input_ime_dispecera.text.strip()
        telefon = self.ids.input_telefon_dispecera.text.strip()

        if not ime or not telefon:
            _PRIKAZI_POPUP(
                jezici._t("dispeceri.nedostaju_podaci_naslov"),
                jezici._t("dispeceri.nedostaju_podaci_poruka"),
            )
            return

        smena_tekst = self.ids.spinner_smena_dispecera.text
        # Izdvoji broj smene bez oslanjanja na rec ispred njega
        # (prevedena je - "Smena 1" / "Shift 1" - broj je uvek poslednji).
        try:
            smena = int(smena_tekst.strip().split()[-1])
        except (ValueError, IndexError):
            smena = 1

        stavka = {"ime": ime, "telefon": telefon, "smena": smena}
        app = App.get_running_app()

        if self.izmena_id is not None:
            _DISPECERI_REF.azuriraj(app.user_data_dir, self.izmena_id, stavka)
            self.izmena_id = None
            self.dugme_tekst = jezici._t("dispeceri.dodaj_dispecera")
        else:
            _DISPECERI_REF.dodaj(app.user_data_dir, stavka)

        self.ids.input_ime_dispecera.text = ""
        self.ids.input_telefon_dispecera.text = ""
        self.ids.spinner_smena_dispecera.text = jezici._t("dispeceri.smena_format", broj=1)
        self.ucitaj_dispecere()



DISPECERI_KV = """
# ============================================================
# DISPECERI (Poziv)
# ============================================================

<DispeceriScreen>:
    name: "poziv"
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
                spacing: dp(12)
                padding: dp(4)

                PastelCard:
                    orientation: "vertical"
                    tint: 0.30, 0.29, 0.42, 0.92
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(12)
                    spacing: dp(8)

                    Label:
                        text: root.tekst_vreme_smena
                        bold: True
                        font_size: '15sp'
                        color: 1, 1, 1, 1
                        size_hint_y: None
                        height: dp(28)
                        halign: "left"
                        text_size: self.width, None

                    BoxLayout:
                        size_hint_y: None
                        height: dp(48)
                        spacing: dp(6)
                        Label:
                            text: root.tekst_smena1_lbl
                            size_hint_x: 0.4
                            color: 1, 1, 1, 1
                        PastelTextInput:
                            id: input_smena1_od
                            text: root.smena1_od
                            hint_text: "06:00"
                        PastelTextInput:
                            id: input_smena1_do
                            text: root.smena1_do
                            hint_text: "14:00"

                    BoxLayout:
                        size_hint_y: None
                        height: dp(48)
                        spacing: dp(6)
                        Label:
                            text: root.tekst_smena2_lbl
                            size_hint_x: 0.4
                            color: 1, 1, 1, 1
                        PastelTextInput:
                            id: input_smena2_od
                            text: root.smena2_od
                            hint_text: "14:00"
                        PastelTextInput:
                            id: input_smena2_do
                            text: root.smena2_do
                            hint_text: "22:00"

                    BoxLayout:
                        size_hint_y: None
                        height: dp(48)
                        spacing: dp(6)
                        Label:
                            text: root.tekst_smena3_lbl
                            size_hint_x: 0.4
                            color: 1, 1, 1, 1
                        PastelTextInput:
                            id: input_smena3_od
                            text: root.smena3_od
                            hint_text: "22:00"
                        PastelTextInput:
                            id: input_smena3_do
                            text: root.smena3_do
                            hint_text: "06:00"

                    RoundButton:
                        label_text: root.tekst_sacuvaj_vreme_smena
                        tint: 0.36, 0.46, 0.64, 1
                        size_hint_y: None
                        height: dp(46)
                        on_release: root.sacuvaj_smene()

                FieldLabel:
                    text: root.tekst_ime_prezime_dispecera

                PastelTextInput:
                    id: input_ime_dispecera
                    hint_text: root.hint_ime

                FieldLabel:
                    text: root.tekst_broj_telefona

                PastelTextInput:
                    id: input_telefon_dispecera
                    hint_text: root.hint_telefon
                    input_type: "number"

                FieldLabel:
                    text: root.tekst_smena_label

                Spinner:
                    id: spinner_smena_dispecera
                    text: "Smena 1"
                    values: ["Smena 1", "Smena 2", "Smena 3"]
                    size_hint_y: None
                    height: dp(48)
                    background_color: 0.78, 0.80, 0.90, 1
                    color: 0.12, 0.12, 0.24, 1

                RoundButton:
                    label_text: root.dugme_tekst
                    tint: 0.30, 0.52, 0.36, 1
                    text_color: 0.92, 1, 0.94, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.sacuvaj_dispecera()

                BoxLayout:
                    id: lista_dispecera
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(10)
                    padding: dp(4), dp(10)


"""
