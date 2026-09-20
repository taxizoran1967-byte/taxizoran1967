"""
ekran_izgled.py
Ekran "Izgled aplikacije" - izbor teme boja. Promena se odmah (uz
glatku animaciju) vidi u celoj aplikaciji, a izbor se pamti.

Tema se primenjuje preko main.py (funkcija postavi_temu), a ovaj ekran
samo prikazuje kartice sa temama.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import (
    StringProperty,
    ListProperty,
    BooleanProperty,
)

from servisi import jezici
from servisi import teme


# ============================================================
# main.py ovo postavlja posle uvoza (izbegava kruzni import)
# ============================================================

_POSTAVI_TEMU = None   # main: TaksiApp.postavi_temu(tema_id)
_TRENUTNA_TEMA = None  # main: funkcija koja vraca id trenutne teme


def povezi(postavi_temu_fn, trenutna_tema_fn):
    """main.py poziva ovo jednom, odmah posle 'import ekran_izgled'."""
    global _POSTAVI_TEMU, _TRENUTNA_TEMA
    _POSTAVI_TEMU = postavi_temu_fn
    _TRENUTNA_TEMA = trenutna_tema_fn


class TemaKartica(ButtonBehavior, BoxLayout):
    """Jedna kartica teme - crta svoju pravu boju (ne prolazi kroz
    pomeranje boja teme, da preview uvek izgleda kako treba)."""

    tema_id = StringProperty("")
    naziv = StringProperty("")
    boja = ListProperty([0.4, 0.4, 0.6, 1])
    akcent = ListProperty([1, 1, 1, 1])
    izabrana = BooleanProperty(False)


class IzgledScreen(Screen):
    tekst_naslov = StringProperty("Izgled aplikacije")
    tekst_pocetna = StringProperty("Pocetna")
    tekst_opis = StringProperty("")
    tekst_osnovna = StringProperty("Osnovna tema")

    def on_pre_enter(self, *args):
        self.tekst_naslov = teme.t("naslov")
        self.tekst_pocetna = jezici._t("buttons.pocetna")
        self.tekst_opis = teme.t("opis")
        self.tekst_osnovna = teme.t("osnovna")
        self._napravi_kartice()

    def _trenutna(self):
        try:
            return _TRENUTNA_TEMA() if _TRENUTNA_TEMA else teme.OSNOVNA_TEMA
        except Exception:
            return teme.OSNOVNA_TEMA

    def _napravi_kartice(self):
        lista = self.ids.lista
        lista.clear_widgets()

        trenutna = self._trenutna()

        for tema_id in teme.REDOSLED:
            kartica = TemaKartica(
                tema_id=tema_id,
                naziv=teme.naziv_teme(tema_id),
                boja=teme.boja_teme(tema_id),
                akcent=teme.TEME[tema_id]["akcent"],
                izabrana=(tema_id == trenutna),
            )
            kartica.bind(
                on_release=lambda w: self.izaberi(w.tema_id)
            )
            lista.add_widget(kartica)

    def izaberi(self, tema_id):
        """Primeni temu i oznaci izabranu karticu."""
        if _POSTAVI_TEMU:
            _POSTAVI_TEMU(tema_id)

        for kartica in self.ids.lista.children:
            kartica.izabrana = (kartica.tema_id == tema_id)


IZGLED_KV = """
# ============================================================
# IZGLED APLIKACIJE (izbor teme boja)
# ============================================================

<TemaKartica>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(64)
    padding: dp(16), dp(8)
    spacing: dp(14)

    canvas.before:
        Color:
            rgba: 0, 0, 0, 0.22
        RoundedRectangle:
            pos: self.x, self.y - dp(3)
            size: self.size
            radius: [dp(18)]

        Color:
            rgba: root.boja
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(18)]

        Color:
            rgba: 1, 1, 1, 0.12
        RoundedRectangle:
            pos: self.x, self.center_y
            size: self.width, self.height / 2
            radius: [dp(18), dp(18), 0, 0]

        Color:
            rgba: (1, 1, 1, 0.95) if root.izabrana else (1, 1, 1, 0.16)
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, dp(18))
            width: dp(2.2) if root.izabrana else dp(1)

    Widget:
        size_hint: None, 1
        width: dp(30)
        canvas:
            Color:
                rgba: 1, 1, 1, 0.35
            Ellipse:
                pos: self.center_x - dp(15), self.center_y - dp(15)
                size: dp(30), dp(30)
            Color:
                rgba: root.akcent
            Ellipse:
                pos: self.center_x - dp(12), self.center_y - dp(12)
                size: dp(24), dp(24)

    Label:
        text: root.naziv
        font_size: '17sp'
        bold: True
        color: 1, 1, 1, 1
        halign: "left"
        valign: "middle"
        text_size: self.size

    Widget:
        size_hint: None, 1
        width: dp(26)
        canvas:
            Color:
                rgba: (1, 1, 1, 1) if root.izabrana else (1, 1, 1, 0)
            Ellipse:
                pos: self.center_x - dp(12), self.center_y - dp(12)
                size: dp(24), dp(24)
            Color:
                rgba: root.boja if root.izabrana else (0, 0, 0, 0)
            Ellipse:
                pos: self.center_x - dp(5), self.center_y - dp(5)
                size: dp(10), dp(10)


<IzgledScreen>:
    name: "izgled"
    ScreenRoot:

        TitleLabel:
            text: root.tekst_naslov

        NavBar:
            RoundButton:
                label_text: root.tekst_pocetna
                on_release: root.manager.current = "home"

            RoundButton:
                label_text: root.tekst_osnovna
                tint: 0.28, 0.48, 0.34, 1
                on_release: root.izaberi("original")

        FieldLabel:
            text: root.tekst_opis

        ScrollView:
            do_scroll_x: False

            BoxLayout:
                id: lista
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: 0, dp(4)
"""
