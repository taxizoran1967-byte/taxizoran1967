"""
ekran_valuta.py
Ekran za izbor prikaza cena (RSD ili EUR) i osvezavanje kursa.

Izdvojen iz main.py - isti obrazac kao grafik_zarade.py.
"""

import threading

from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.app import App
from kivy.clock import Clock


# ============================================================
# main.py ovo postavlja posle uvoza (izbegava kruzni import)
# ============================================================

_KURS_REF = None       # main.KURS (KursPodesavanja instanca), injektuje main.py
_PRIKAZI_POPUP = None  # main._prikazi_popup_poruku, injektuje main.py


def poveži(kurs_obj, prikazi_popup_fn):
    """main.py poziva ovo jednom, odmah posle 'import ekran_valuta'."""
    global _KURS_REF, _PRIKAZI_POPUP
    _KURS_REF = kurs_obj
    _PRIKAZI_POPUP = prikazi_popup_fn


class ValutaScreen(Screen):
    tekst_kurs = StringProperty("")
    valuta_izbor = StringProperty("RSD")

    def on_pre_enter(self, *args):
        self.valuta_izbor = _KURS_REF.valuta
        self._osvezi_tekst()

    def _osvezi_tekst(self):
        if _KURS_REF.kurs_eur_rsd:
            self.tekst_kurs = (
                f"1 EUR = {_KURS_REF.kurs_eur_rsd:.2f} RSD\n"
                f"(kurs od {_KURS_REF.datum_kursa or 'nepoznatog datuma'})"
            )
        else:
            self.tekst_kurs = "Kurs jos nije povucen sa interneta."

    def izaberi_valutu(self, valuta):
        self.valuta_izbor = valuta
        _KURS_REF.valuta = valuta
        app = App.get_running_app()
        _KURS_REF.sacuvaj(app.user_data_dir)

    def osvezi_kurs_rucno(self):
        app = App.get_running_app()

        def posao():
            uspeh, greska = _KURS_REF.osvezi_ako_treba(app.user_data_dir, prinudno=True)
            Clock.schedule_once(lambda dt: self._posle_osvezavanja(uspeh, greska))

        threading.Thread(target=posao, daemon=True).start()

    def _posle_osvezavanja(self, uspeh, greska):
        self._osvezi_tekst()
        if uspeh:
            _PRIKAZI_POPUP("Info", "Kurs je osvezen.", size_hint=(0.8, 0.3))
        else:
            _PRIKAZI_POPUP(
                "Greska",
                f"Nije uspelo povlacenje kursa:\n{greska}",
                size_hint=(0.85, 0.4),
            )


VALUTA_KV = """
# ============================================================
# VALUTA - izbor prikaza cena (RSD ili EUR) i kurs
# ============================================================

<ValutaScreen>:
    name: "valuta"
    ScreenRoot:

        TitleLabel:
            text: "Valuta"

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
            text: "Cene se u aplikaciji uvek racunaju i cuvaju u dinarima. Ovde bira se samo u kojoj valuti da se PRIKAZUJU."

        BoxLayout:
            size_hint_y: None
            height: dp(80)
            padding: dp(10)
            canvas.before:
                Color:
                    rgba: 0.30, 0.29, 0.42, 0.85
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(14)]
            Label:
                text: root.tekst_kurs
                color: 1, 1, 1, 1
                halign: "center"
                valign: "middle"
                text_size: self.size

        BoxLayout:
            size_hint_y: None
            height: dp(56)
            spacing: dp(10)

            RoundButton:
                label_text: "Prikazuj u RSD"
                tint: (0.30, 0.52, 0.36, 1) if root.valuta_izbor == "RSD" else (0.36, 0.35, 0.48, 1)
                text_color: 0.95, 1, 0.96, 1
                on_release: root.izaberi_valutu("RSD")

            RoundButton:
                label_text: "Prikazuj u EUR"
                tint: (0.30, 0.52, 0.36, 1) if root.valuta_izbor == "EUR" else (0.36, 0.35, 0.48, 1)
                text_color: 0.95, 1, 0.96, 1
                on_release: root.izaberi_valutu("EUR")

        RoundButton:
            label_text: "Osvezi kurs sada"
            tint: 0.36, 0.46, 0.64, 1
            text_color: 1, 1, 1, 1
            size_hint_y: None
            height: dp(52)
            on_release: root.osvezi_kurs_rucno()

        FieldLabel:
            text: "Kurs se automatski osvezava jednom dnevno (kad prvi put otvoris app tog dana). Ovde mozes rucno da ga povuces ponovo, npr. ako juce nije bilo interneta."
            size_hint_y: None
            height: dp(70)
            text_size: self.width, None

        Widget:
"""
