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
    def otvori_navigaciju(self):
        odrediste = self.ids.input_odrediste.text.strip()
        if not odrediste:
            _PRIKAZI_POPUP("Info", "Unesi odrediste pre otvaranja navigacije.", size_hint=(0.8, 0.3))
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
                _PRIKAZI_POPUP("Greska", "Ne mogu da otvorim navigaciju na ovom uredjaju.", size_hint=(0.8, 0.3))


NAVIGACIJA_KV = """
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
"""
