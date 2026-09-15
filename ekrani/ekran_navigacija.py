"""
ekran_navigacija.py
Ekran za brzo otvaranje Google navigacije ka unetoj adresi.

Izdvojen iz main.py radi lakseg odrzavanja - main.py i dalje uvozi ovaj
fajl (import ekran_navigacija) i dodaje NAVIGACIJA_KV u glavni KV pre
Builder.load_string(), isti obrazac kao vec postojeci grafik_zarade.py.
"""

import webbrowser
import urllib.parse

from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty

from servisi import jezici


# ============================================================
# main.py ovo postavlja posle uvoza (izbegava kruzni import) - isti
# obrazac kao poveži_valutu u grafik_zarade.py
# ============================================================

_PRIKAZI_POPUP = None  # main._prikazi_popup_poruku, injektuje main.py


def poveži_popup(prikazi_popup_fn):
    """main.py poziva ovo jednom, odmah posle 'import ekran_navigacija'."""
    global _PRIKAZI_POPUP
    _PRIKAZI_POPUP = prikazi_popup_fn


class NavigacijaScreen(Screen):
    tekst_naslov = StringProperty("Navigacija")
    tekst_pocetna = StringProperty("Pocetna")
    tekst_podesavanja = StringProperty("Podesavanja")
    tekst_odrediste_label = StringProperty("Odrediste (adresa ili naziv mesta)")
    hint_odrediste = StringProperty("npr. Terazije 5, Beograd")
    tekst_otvori_navigaciju = StringProperty("Otvori navigaciju")
    tekst_napomena = StringProperty("")

    def on_pre_enter(self, *args):
        self.tekst_naslov = jezici._t("navigacija.naslov")
        self.tekst_pocetna = jezici._t("buttons.pocetna")
        self.tekst_podesavanja = jezici._t("home.podesavanja")
        self.tekst_odrediste_label = jezici._t("navigacija.odrediste_label")
        self.hint_odrediste = jezici._t("navigacija.odrediste_hint")
        self.tekst_otvori_navigaciju = jezici._t("navigacija.otvori_navigaciju")
        self.tekst_napomena = jezici._t("navigacija.napomena")

    def otvori_navigaciju(self):
        odrediste = self.ids.input_odrediste.text.strip()
        if not odrediste:
            _PRIKAZI_POPUP(jezici._t("buttons.info"), jezici._t("navigacija.unesi_odrediste"), size_hint=(0.8, 0.3))
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
                _PRIKAZI_POPUP(jezici._t("profil.greska"), jezici._t("navigacija.ne_mogu_navigaciju"), size_hint=(0.8, 0.3))


NAVIGACIJA_KV = """
# ============================================================
# NAVIGACIJA
# ============================================================

<NavigacijaScreen>:
    name: "navigacija"
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
            text: root.tekst_odrediste_label

        PastelTextInput:
            id: input_odrediste
            hint_text: root.hint_odrediste

        RoundButton:
            label_text: root.tekst_otvori_navigaciju
            tint: 0.36, 0.46, 0.64, 1
            text_color: 0.95, 0.96, 1, 1
            size_hint_y: None
            height: dp(52)
            on_release: root.otvori_navigaciju()

        FieldLabel:
            text: root.tekst_napomena
            size_hint_y: None
            height: dp(60)
            text_size: self.width, None

        Widget:
"""
