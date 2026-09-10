"""
ekran_jezici.py
Ekran za izbor jezika - korisnik bira između srpskog i engleskog

Izdvojeno iz main.py - isti obrazac kao grafik_zarade.py.
"""

from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.app import App

from servisi import jezici


# ============================================================
# main.py ovo postavlja posle uvoza (izbegava kruzni import)
# ============================================================

_PRIKAZI_POPUP = None  # main._prikazi_popup_poruku


def povezi(prikazi_popup_fn):
    """main.py poziva ovo jednom, odmah posle 'import ekran_jezici'."""
    global _PRIKAZI_POPUP
    _PRIKAZI_POPUP = prikazi_popup_fn


class JeziciScreen(Screen):
    tekst_trenutni = StringProperty("Izabrani jezik: Srpski")
    
    def on_pre_enter(self, *args):
        """Osvezi prikaz trenutnog jezika pri ulasku na ekran"""
        lang = jezici.get_current_language()
        if lang == "sr":
            self.tekst_trenutni = "Izabrani jezik: Srpski 🇷🇸"
        elif lang == "en":
            self.tekst_trenutni = "Selected language: English 🇬🇧"
        else:
            self.tekst_trenutni = f"Current language: {lang.upper()}"
    
    def promeni_jezici(self, lang_code):
        """Promeni jezik i osvezi ekran"""
        jezici.set_language(lang_code)
        
        # Osvezi prikaz
        if lang_code == "sr":
            self.tekst_trenutni = "Izabrani jezik: Srpski 🇷🇸"
            poruka_naslov = "Info"
            poruka_tekst = "Jezik je promenjen na Srpski!"
        elif lang_code == "en":
            self.tekst_trenutni = "Selected language: English 🇬🇧"
            poruka_naslov = "Info"
            poruka_tekst = "Language changed to English!"
        else:
            self.tekst_trenutni = f"Current language: {lang_code.upper()}"
            poruka_naslov = "Info"
            poruka_tekst = f"Language changed to {lang_code.upper()}!"
        
        if _PRIKAZI_POPUP:
            _PRIKAZI_POPUP(poruka_naslov, poruka_tekst, size_hint=(0.8, 0.3))


JEZICI_KV = """
# ============================================================
# IZBOR JEZIKA
# ============================================================

<JeziciScreen>:
    name: "jezici"
    ScreenRoot:

        TitleLabel:
            text: "Izbor jezika / Language"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                font_size: '13sp'
                on_release: root.manager.current = "home"

        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(16)
                padding: dp(16)

                PastelCard:
                    tint: 0.28, 0.48, 0.34, 0.92
                    size_hint_y: None
                    height: dp(80)
                    padding: dp(12)
                    Label:
                        text: root.tekst_trenutni
                        font_size: '16sp'
                        bold: True
                        color: 1, 1, 1, 1
                        halign: "center"
                        valign: "middle"
                        text_size: self.size

                FieldLabel:
                    text: "Dostupni jezici / Available languages:"

                RoundButton:
                    label_text: "Srpski 🇷🇸"
                    tint: 0.36, 0.46, 0.64, 1
                    text_color: 0.95, 0.96, 1, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.promeni_jeziki("sr")

                RoundButton:
                    label_text: "English 🇬🇧"
                    tint: 0.36, 0.46, 0.64, 1
                    text_color: 0.95, 0.96, 1, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.promeni_jeziki("en")

                Widget:
"""
