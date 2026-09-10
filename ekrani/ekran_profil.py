"""
ekran_profil.py
Ekran Profil vozaca - licni podaci i podaci o vozilu, plus pracenje
roka isteka registracije/osiguranja.

Izdvojen iz main.py - isti obrazac kao grafik_zarade.py.
MODIFIKOVANO: Koristi _t() za jezičke tekstove
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

    def opis(dani, naziv_key):
        if dani is None:
            return jezici._t(f"profil.{naziv_key}_nije_unet")
        if dani < 0:
            return jezici._t(f"profil.{naziv_key}_isteklo", dani=abs(dani))
        if dani == 0:
            return jezici._t(f"profil.{naziv_key}_istice_danas")
        return jezici._t(f"profil.{naziv_key}_istice_za", dani=dani)

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

    tekst = opis(reg_dani, "reg") + "\n" + opis(osig_dani, "osig")

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

    def on_pre_enter(self, *args):
        self.ids.input_ime.text = _VOZAC_REF.ime_prezime
        self.ids.input_telefon.text = _VOZAC_REF.telefon
        self.ids.input_licenca.text = _VOZAC_REF.broj_licence
        self.ids.input_tablice.text = _VOZAC_REF.tablice
        self.ids.input_vozilo.text = _VOZAC_REF.vozilo
        self.ids.input_registracija.text = _VOZAC_REF.registracija_datum
        self.ids.input_osiguranje.text = _VOZAC_REF.osiguranje_datum
        self._osvezi_dokumenti()

    def _osvezi_dokumenti(self):
        self.tekst_dokumenti, self.boja_dokumenti = _stanje_dokumenata_vozila()

    def sacuvaj_profil(self):
        reg_tekst = self.ids.input_registracija.text.strip()
        osig_tekst = self.ids.input_osiguranje.text.strip()

        # Provera validnosti datuma
        for naziv_key, vrednost in (("reg", reg_tekst), ("osig", osig_tekst)):
            if vrednost and _dani_do_isteka(vrednost) is None:
                naziv = jezici._t(f"profil.{naziv_key}_nije_unet").split(":")[0]
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

        _PRIKAZI_POPUP(jezici._t("buttons.info"), jezici._t("profil.sacuvano"), size_hint=(0.8, 0.3))


PROFIL_KV = """
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
            do_scroll_x: False
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

                FieldLabel:
                    text: "Registracija istice (format GGGG-MM-DD)"

                PastelTextInput:
                    id: input_registracija
                    hint_text: "npr. 2026-12-31"

                FieldLabel:
                    text: "Osiguranje istice (format GGGG-MM-DD)"

                PastelTextInput:
                    id: input_osiguranje
                    hint_text: "npr. 2026-11-15"

                RoundButton:
                    label_text: "Sacuvaj profil"
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
                    text: "Ovi podaci se prikazuju u zaglavlju PDF mesecnog izvestaja (Izvestaj -> Izvoz PDF)."
                    size_hint_y: None
                    height: dp(60)
                    text_size: self.width, None
"""
