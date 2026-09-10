"""
ekran_jezik.py
Probni ekran za prebacivanje jezika interfejsa izmedju srpskog i engleskog.
"""

from kivy.app import App
from kivy.properties import DictProperty, StringProperty
from kivy.uix.screenmanager import Screen

from servisi import i18n


class JezikScreen(Screen):
    tekstovi = DictProperty({})
    aktivni_jezik = StringProperty("sr")

    def on_pre_enter(self, *args):
        self.osvezi_tekstove()

    def osvezi_tekstove(self):
        app = App.get_running_app()
        jezik = getattr(app, "jezik", "sr") if app else "sr"
        self.aktivni_jezik = jezik
        self.tekstovi = {
            "title": i18n.prevedi(jezik, "language_title"),
            "home": i18n.prevedi(jezik, "nav_home"),
            "settings": i18n.prevedi(jezik, "nav_settings"),
            "current": i18n.prevedi(
                jezik,
                "language_current",
                language=i18n.naziv_jezika(jezik, jezik),
            ),
            "serbian": i18n.prevedi(jezik, "language_serbian"),
            "english": i18n.prevedi(jezik, "language_english"),
            "trial_info": i18n.prevedi(jezik, "language_trial_info"),
        }

    def postavi_jezik(self, jezik):
        app = App.get_running_app()
        if app is None:
            return
        app.postavi_jezik(jezik)
        self.osvezi_tekstove()


JEZIK_KV = """
# ============================================================
# JEZIK - probno prebacivanje SR/EN
# ============================================================

<JezikScreen>:
    name: "jezik"
    ScreenRoot:

        TitleLabel:
            text: root.tekstovi.get("title", "")

        NavBar:
            RoundButton:
                label_text: root.tekstovi.get("home", "")
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: root.tekstovi.get("settings", "")
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "podesavanja"

        PastelCard:
            tint: 0.30, 0.29, 0.42, 0.90
            size_hint_y: None
            height: dp(74)
            padding: dp(14)
            Label:
                text: root.tekstovi.get("current", "")
                color: 1, 1, 1, 1
                halign: "center"
                valign: "middle"
                text_size: self.size

        BoxLayout:
            size_hint_y: None
            height: dp(56)
            spacing: dp(10)

            RoundButton:
                label_text: root.tekstovi.get("serbian", "")
                tint: (0.30, 0.52, 0.36, 1) if root.aktivni_jezik == "sr" else (0.36, 0.35, 0.48, 1)
                text_color: 0.95, 1, 0.96, 1
                on_release: root.postavi_jezik("sr")

            RoundButton:
                label_text: root.tekstovi.get("english", "")
                tint: (0.30, 0.52, 0.36, 1) if root.aktivni_jezik == "en" else (0.36, 0.35, 0.48, 1)
                text_color: 0.95, 1, 0.96, 1
                on_release: root.postavi_jezik("en")

        FieldLabel:
            text: root.tekstovi.get("trial_info", "")
            size_hint_y: None
            height: dp(74)
            text_size: self.width, None

        Widget:
"""
