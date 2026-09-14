"""
ekran_profil.py
Ekran Profil vozaca - licni podaci i podaci o vozilu, plus pracenje
roka isteka registracije/osiguranja.

Izdvojen iz main.py - isti obrazac kao grafik_zarade.py.
"""

from datetime import datetime

from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ListProperty
from kivy.app import App

from servisi import jezici


# ============================================================
# main.py ovo postavlja posle uvoza (izbegava kruzni import)
# ============================================================

_VOZAC_REF = None      # main.VOZAC (VozacPodesavanja instanca), injektuje main.py
_PRIKAZI_POPUP = None  # main._prikazi_popup_poruku, injektuje main.py


def poveži(vozac_obj, prikazi_popup_fn):
    """main.py poziva ovo jednom, odmah posle 'import ekran_profil'."""
    global _VOZAC_REF, _PRIKAZI_POPUP
    _VOZAC_REF = vozac_obj
    _PRIKAZI_POPUP = prikazi_popup_fn


def _dani_do_isteka(datum_str):
    """Vraca broj dana do isteka za dati datum (format GGGG-MM-DD), ili
    None ako datum nije unet ili nije validan. Broj moze biti
    negativan ako je datum vec prosao (znaci da je vec isteklo)."""
    if not datum_str:
        return None
    try:
        datum = datetime.strptime(datum_str, "%Y-%m-%d").date()
    except ValueError:
        return None
    return (datum - datetime.now().date()).days


def _stanje_dokumenata_vozila():
    """Vraca (tekst, boja) za kombinovani status registracije i
    osiguranja - koristi se na ekranu Profil vozaca. Boja kartice
    prati NAJGORE od ta dva stanja (crveno ako je bar jedno isteklo,
    zuto ako bar jedno istice u naredni 30 dana, inace zeleno; sivo
    ako nijedan datum jos nije unet)."""

    def opis_registracija(dani):
        if dani is None:
            return jezici._t("profil.reg_nije_unet")
        if dani < 0:
            return jezici._t("profil.reg_isteklo", dani=abs(dani))
        if dani == 0:
            return jezici._t("profil.reg_istice_danas")
        return jezici._t("profil.reg_istice_za", dani=dani)

    def opis_osiguranje(dani):
        if dani is None:
            return jezici._t("profil.osig_nije_unet")
        if dani < 0:
            return jezici._t("profil.osig_isteklo", dani=abs(dani))
        if dani == 0:
            return jezici._t("profil.osig_istice_danas")
        return jezici._t("profil.osig_istice_za", dani=dani)

    def nivo(dani):
        if dani is None:
            return 0
        if dani < 0:
            return 3
        if dani <= 30:
            return 2
        return 1

    reg_dani = _dani_do_isteka(_VOZAC_REF.registracija_datum)
    osig_dani = _dani_do_isteka(_VOZAC_REF.osiguranje_datum)

    tekst = opis_registracija(reg_dani) + "\n" + opis_osiguranje(osig_dani)

    boje = {
        0: [0.35, 0.35, 0.45, 0.92],
        1: [0.24, 0.46, 0.30, 0.95],
        2: [0.60, 0.48, 0.16, 0.95],
        3: [0.62, 0.24, 0.24, 0.95],
    }
    najgori_nivo = max(nivo(reg_dani), nivo(osig_dani))
    return tekst, boje[najgori_nivo]


class ProfilScreen(Screen):
    tekst_dokumenti = StringProperty("")
    boja_dokumenti = ListProperty([0.35, 0.35, 0.45, 0.92])

    tekst_naslov = StringProperty("Profil vozaca")
    tekst_pocetna = StringProperty("Pocetna")
    tekst_ime = StringProperty("Ime i prezime")
    tekst_telefon = StringProperty("Telefon")
    tekst_licenca = StringProperty("Broj licence / dozvole za taksi")
    tekst_tablice = StringProperty("Registarske tablice")
    tekst_vozilo = StringProperty("Vozilo (marka i model)")
    tekst_registracija = StringProperty("Registracija istice (format GGGG-MM-DD)")
    tekst_osiguranje = StringProperty("Osiguranje istice (format GGGG-MM-DD)")
    tekst_sacuvaj = StringProperty("Sacuvaj profil")
    tekst_pdf_napomena = StringProperty("")
    hint_ime = StringProperty("npr. Petar Petrovic")
    hint_telefon = StringProperty("npr. 065 123 4567")
    hint_licenca = StringProperty("npr. TX-00123")
    hint_tablice = StringProperty("npr. BG-1234-AB")
    hint_vozilo = StringProperty("npr. Skoda Octavia")
    hint_registracija = StringProperty("npr. 2026-12-31")
    hint_osiguranje = StringProperty("npr. 2026-11-15")

    def on_pre_enter(self, *args):
        self._osvezi_prevod()
        self.ids.input_ime.text = _VOZAC_REF.ime_prezime
        self.ids.input_telefon.text = _VOZAC_REF.telefon
        self.ids.input_licenca.text = _VOZAC_REF.broj_licence
        self.ids.input_tablice.text = _VOZAC_REF.tablice
        self.ids.input_vozilo.text = _VOZAC_REF.vozilo
        self.ids.input_registracija.text = _VOZAC_REF.registracija_datum
        self.ids.input_osiguranje.text = _VOZAC_REF.osiguranje_datum
        self._osvezi_dokumenti()

    def _osvezi_prevod(self):
        self.tekst_naslov = jezici._t("profil.naslov")
        self.tekst_pocetna = jezici._t("buttons.pocetna")
        self.tekst_ime = jezici._t("profil.ime")
        self.tekst_telefon = jezici._t("profil.telefon")
        self.tekst_licenca = jezici._t("profil.licenca")
        self.tekst_tablice = jezici._t("profil.tablice")
        self.tekst_vozilo = jezici._t("profil.vozilo")
        self.tekst_registracija = jezici._t("profil.registracija")
        self.tekst_osiguranje = jezici._t("profil.osiguranje")
        self.tekst_sacuvaj = jezici._t("profil.sacuvaj")
        self.tekst_pdf_napomena = jezici._t("profil.pdf_napomena")
        self.hint_ime = jezici._t("profil.ime_hint")
        self.hint_telefon = jezici._t("profil.telefon_hint")
        self.hint_licenca = jezici._t("profil.licenca_hint")
        self.hint_tablice = jezici._t("profil.tablice_hint")
        self.hint_vozilo = jezici._t("profil.vozilo_hint")
        self.hint_registracija = jezici._t("profil.registracija_hint")
        self.hint_osiguranje = jezici._t("profil.osiguranje_hint")

    def _osvezi_dokumenti(self):
        self.tekst_dokumenti, self.boja_dokumenti = _stanje_dokumenata_vozila()

    def sacuvaj_profil(self):
        reg_tekst = self.ids.input_registracija.text.strip()
        osig_tekst = self.ids.input_osiguranje.text.strip()

        for naziv, vrednost in (
            (jezici._t("profil.registracija_rec"), reg_tekst),
            (jezici._t("profil.osiguranje_rec"), osig_tekst),
        ):
            if vrednost and _dani_do_isteka(vrednost) is None:
                _PRIKAZI_POPUP(
                    jezici._t("profil.greska"),
                    jezici._t("profil.datum_format", naziv=naziv),
                    size_hint=(0.85, 0.4),
                )
                return

        _VOZAC_REF.ime_prezime = self.ids.input_ime.text.strip()
        _VOZAC_REF.telefon = self.ids.input_telefon.text.strip()
        _VOZAC_REF.broj_licence = self.ids.input_licenca.text.strip()
        _VOZAC_REF.tablice = self.ids.input_tablice.text.strip()
        _VOZAC_REF.vozilo = self.ids.input_vozilo.text.strip()
        _VOZAC_REF.registracija_datum = reg_tekst
        _VOZAC_REF.osiguranje_datum = osig_tekst

        app = App.get_running_app()
        _VOZAC_REF.sacuvaj(app.user_data_dir)
        self._osvezi_dokumenti()

        _PRIKAZI_POPUP(
            jezici._t("buttons.info"),
            jezici._t("profil.sacuvano"),
            size_hint=(0.8, 0.3),
        )


PROFIL_KV = """
# ============================================================
# PROFIL VOZACA
# ============================================================

<ProfilScreen>:
    name: "profil"
    ScreenRoot:

        TitleLabel:
            text: root.tekst_naslov

        NavBar:
            RoundButton:
                label_text: root.tekst_pocetna
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"

        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(8)
                padding: dp(2), dp(4)

                FieldLabel:
                    text: root.tekst_ime

                PastelTextInput:
                    id: input_ime
                    hint_text: root.hint_ime

                FieldLabel:
                    text: root.tekst_telefon

                PastelTextInput:
                    id: input_telefon
                    hint_text: root.hint_telefon

                FieldLabel:
                    text: root.tekst_licenca

                PastelTextInput:
                    id: input_licenca
                    hint_text: root.hint_licenca

                FieldLabel:
                    text: root.tekst_tablice

                PastelTextInput:
                    id: input_tablice
                    hint_text: root.hint_tablice

                FieldLabel:
                    text: root.tekst_vozilo

                PastelTextInput:
                    id: input_vozilo
                    hint_text: root.hint_vozilo

                FieldLabel:
                    text: root.tekst_registracija

                PastelTextInput:
                    id: input_registracija
                    hint_text: root.hint_registracija

                FieldLabel:
                    text: root.tekst_osiguranje

                PastelTextInput:
                    id: input_osiguranje
                    hint_text: root.hint_osiguranje

                RoundButton:
                    label_text: root.tekst_sacuvaj
                    tint: 0.30, 0.52, 0.36, 1
                    text_color: 1, 1, 1, 1
                    size_hint_y: None
                    height: dp(56)
                    on_release: root.sacuvaj_profil()

                PastelCard:
                    tint: root.boja_dokumenti
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(12)
                    orientation: "vertical"
                    Label:
                        text: root.tekst_dokumenti
                        font_size: '14sp'
                        bold: True
                        color: 1, 1, 1, 1
                        halign: "left"
                        valign: "top"
                        size_hint_y: None
                        text_size: self.width, None
                        height: self.texture_size[1]

                FieldLabel:
                    text: root.tekst_pdf_napomena
                    size_hint_y: None
                    height: dp(60)
                    text_size: self.width, None
"""
