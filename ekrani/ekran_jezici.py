"""
ekran_jezici.py
Ekran za izbor jezika - korisnik bira izmedju srpskog, engleskog,
italijanskog, francuskog, nemackog, ruskog, poljskog, turskog i
spanskog jezika.

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

# Jezici koji su vidljivi u dugmetu ali JOS NISU prevedeni - klik na
# njih samo prikazuje poruku "U izradi", ne menja stvarni jezik app-a.
# Trenutno su svi jezici prevedeni, pa je lista prazna. Ako se u
# buduce doda novi jezik pre nego sto bude preveden, upisi ga ovde
# (npr. "pt": "Português 🇵🇹") i u dugmetu pozovi root.jezik_u_izradi("pt").
JEZICI_U_IZRADI = {}


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
        elif lang == "it":
            self.tekst_trenutni = "Lingua selezionata: Italiano 🇮🇹"
        elif lang == "fr":
            self.tekst_trenutni = "Langue sélectionnée : Français 🇫🇷"
        elif lang == "de":
            self.tekst_trenutni = "Ausgewählte Sprache: Deutsch 🇩🇪"
        elif lang == "ru":
            self.tekst_trenutni = "Выбранный язык: Русский 🇷🇺"
        elif lang == "pl":
            self.tekst_trenutni = "Wybrany język: Polski"
        elif lang == "tr":
            self.tekst_trenutni = "Seçilen dil: Türkçe"
        elif lang == "es":
            self.tekst_trenutni = "Idioma seleccionado: Español"
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
        elif lang_code == "it":
            self.tekst_trenutni = "Lingua selezionata: Italiano 🇮🇹"
            poruka_naslov = "Info"
            poruka_tekst = "Lingua cambiata in Italiano!"
        elif lang_code == "fr":
            self.tekst_trenutni = "Langue sélectionnée : Français 🇫🇷"
            poruka_naslov = "Info"
            poruka_tekst = "Langue changée en Français !"
        elif lang_code == "de":
            self.tekst_trenutni = "Ausgewählte Sprache: Deutsch 🇩🇪"
            poruka_naslov = "Info"
            poruka_tekst = "Sprache auf Deutsch geändert!"
        elif lang_code == "ru":
            self.tekst_trenutni = "Выбранный язык: Русский 🇷🇺"
            poruka_naslov = "Инфо"
            poruka_tekst = "Язык изменён на русский!"
        elif lang_code == "pl":
            self.tekst_trenutni = "Wybrany język: Polski"
            poruka_naslov = "Info"
            poruka_tekst = "Język zmieniono na polski!"
        elif lang_code == "tr":
            self.tekst_trenutni = "Seçilen dil: Türkçe"
            poruka_naslov = "Bilgi"
            poruka_tekst = "Dil Türkçe olarak değiştirildi!"
        elif lang_code == "es":
            self.tekst_trenutni = "Idioma seleccionado: Español"
            poruka_naslov = "Info"
            poruka_tekst = "¡Idioma cambiado a español!"
        else:
            self.tekst_trenutni = f"Current language: {lang_code.upper()}"
            poruka_naslov = "Info"
            poruka_tekst = f"Language changed to {lang_code.upper()}!"

        if _PRIKAZI_POPUP:
            _PRIKAZI_POPUP(poruka_naslov, poruka_tekst, size_hint=(0.8, 0.3))

    def jezik_u_izradi(self, lang_code):
        """Poziva se za jezike koji su samo najavljeni u listi, ali
        prevod za njih jos nije ubacen u app. Ne menja stvarni jezik,
        samo prikazuje poruku da je u izradi."""
        naziv = JEZICI_U_IZRADI.get(lang_code, lang_code.upper())
        if _PRIKAZI_POPUP:
            _PRIKAZI_POPUP(
                "U izradi",
                f"{naziv}\n\nOvaj jezik je u izradi i uskoro ce biti dostupan.",
                size_hint=(0.8, 0.35),
            )


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
                    on_release: root.promeni_jezici("sr")

                RoundButton:
                    label_text: "English 🇬🇧"
                    tint: 0.36, 0.46, 0.64, 1
                    text_color: 0.95, 0.96, 1, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.promeni_jezici("en")

                RoundButton:
                    label_text: "Italiano 🇮🇹"
                    tint: 0.36, 0.46, 0.64, 1
                    text_color: 0.95, 0.96, 1, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.promeni_jezici("it")

                RoundButton:
                    label_text: "Français 🇫🇷"
                    tint: 0.36, 0.46, 0.64, 1
                    text_color: 0.95, 0.96, 1, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.promeni_jezici("fr")

                RoundButton:
                    label_text: "Deutsch 🇩🇪"
                    tint: 0.36, 0.46, 0.64, 1
                    text_color: 0.95, 0.96, 1, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.promeni_jezici("de")

                RoundButton:
                    label_text: "Русский 🇷🇺"
                    tint: 0.36, 0.46, 0.64, 1
                    text_color: 0.95, 0.96, 1, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.promeni_jezici("ru")

                RoundButton:
                    label_text: "Polski"
                    tint: 0.36, 0.46, 0.64, 1
                    text_color: 0.95, 0.96, 1, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.promeni_jezici("pl")

                RoundButton:
                    label_text: "Türkçe"
                    tint: 0.36, 0.46, 0.64, 1
                    text_color: 0.95, 0.96, 1, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.promeni_jezici("tr")

                RoundButton:
                    label_text: "Español"
                    tint: 0.36, 0.46, 0.64, 1
                    text_color: 0.95, 0.96, 1, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.promeni_jezici("es")

                Widget:
"""
