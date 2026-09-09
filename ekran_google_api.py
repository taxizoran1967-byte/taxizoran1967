"""
ekran_google_api.py
Ekran za unos opcionog Google Geocoding API kljuca.

Izdvojen iz main.py - isti obrazac kao grafik_zarade.py.
"""

from kivy.uix.screenmanager import Screen
from kivy.app import App


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
    def on_pre_enter(self, *args):
        self.ids.input_google_kljuc.text = _API_REF.google_kljuc

    def sacuvaj_kljuc(self):
        _API_REF.google_kljuc = self.ids.input_google_kljuc.text.strip()
        app = App.get_running_app()
        _API_REF.sacuvaj(app.user_data_dir)

        _PRIKAZI_POPUP("Info", "Google API kljuc sacuvan.", size_hint=(0.8, 0.3))


GOOGLE_API_KV = """
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
"""
