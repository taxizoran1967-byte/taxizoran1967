"""
ekran_google_api.py
Ekran za unos opcionog Google Geocoding API kljuca.

Izdvojen iz main.py - isti obrazac kao grafik_zarade.py.
"""

from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.app import App

from servisi import jezici


# ============================================================
# main.py ovo postavlja posle uvoza (izbegava kruzni import)
# ============================================================

_API_REF = None       # main.API (ApiPodesavanja instanca), injektuje main.py
_PRIKAZI_POPUP = None  # main._prikazi_popup_poruku, injektuje main.py


def poveži(api_obj, prikazi_popup_fn):
    """main.py poziva ovo jednom, odmah posle 'import ekran_google_api'."""
    global _API_REF, _PRIKAZI_POPUP
    _API_REF = api_obj
    _PRIKAZI_POPUP = prikazi_popup_fn


class GoogleApiScreen(Screen):
    tekst_naslov = StringProperty("Google API")
    tekst_pocetna = StringProperty("Pocetna")
    tekst_podesavanja = StringProperty("Podesavanja")
    tekst_google_kljuc_label = StringProperty("")
    tekst_ocr_kljuc_label = StringProperty("")
    tekst_sacuvaj_kljuceve = StringProperty("Sacuvaj kljuceve")
    tekst_napomena = StringProperty("")
    hint_google = StringProperty("npr. AIzaSy...")
    hint_ocr = StringProperty("npr. K81234567890")

    def on_pre_enter(self, *args):
        self.tekst_naslov = "Google API"
        self.tekst_pocetna = jezici._t("buttons.pocetna")
        self.tekst_podesavanja = jezici._t("home.podesavanja")
        self.tekst_google_kljuc_label = jezici._t("google_api.google_kljuc_label")
        self.tekst_ocr_kljuc_label = jezici._t("google_api.ocr_kljuc_label")
        self.tekst_sacuvaj_kljuceve = jezici._t("google_api.sacuvaj_kljuceve")
        self.tekst_napomena = jezici._t("google_api.napomena")
        self.hint_google = jezici._t("google_api.google_hint")
        self.hint_ocr = jezici._t("google_api.ocr_hint")
        self.ids.input_google_kljuc.text = _API_REF.google_kljuc
        self.ids.input_ocr_kljuc.text = _API_REF.ocr_kljuc

    def sacuvaj_kljuc(self):
        _API_REF.google_kljuc = self.ids.input_google_kljuc.text.strip()
        _API_REF.ocr_kljuc = self.ids.input_ocr_kljuc.text.strip()
        app = App.get_running_app()
        _API_REF.sacuvaj(app.user_data_dir)

        _PRIKAZI_POPUP(jezici._t("buttons.info"), jezici._t("google_api.kljucevi_sacuvani"), size_hint=(0.8, 0.3))


GOOGLE_API_KV = """
# ============================================================
# GOOGLE API - unos kljuca za tacnije adrese
# ============================================================

<GoogleApiScreen>:
    name: "google_api"
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

        FieldLabel:
            text: root.tekst_google_kljuc_label

        PastelTextInput:
            id: input_google_kljuc
            hint_text: root.hint_google

        FieldLabel:
            text: root.tekst_ocr_kljuc_label

        PastelTextInput:
            id: input_ocr_kljuc
            hint_text: root.hint_ocr

        RoundButton:
            label_text: root.tekst_sacuvaj_kljuceve
            tint: 0.30, 0.52, 0.36, 1
            text_color: 0.92, 1, 0.94, 1
            size_hint_y: None
            height: dp(52)
            on_release: root.sacuvaj_kljuc()

        FieldLabel:
            text: root.tekst_napomena
            size_hint_y: None
            height: dp(80)
            text_size: self.width, None

        Widget:
"""
