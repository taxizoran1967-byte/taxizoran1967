"""
ekran_cenovnik.py
Ekran za izmenu cena tarifa (CenovnikScreen) i prekidac za nocnu
tarifu (NocnaTarifaScreen).

Izdvojeno iz main.py - isti obrazac kao grafik_zarade.py.
"""

from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.app import App


# ============================================================
# main.py ovo postavlja posle uvoza (izbegava kruzni import)
# ============================================================

_CENE_REF = None       # main._CENE_REF
_PRIKAZI_POPUP = None  # main._prikazi_popup_poruku


def poveži(cene_obj, prikazi_popup_fn):
    """main.py poziva ovo jednom, odmah posle 'import ekran_cenovnik'."""
    global _CENE_REF, _PRIKAZI_POPUP
    _CENE_REF = cene_obj
    _PRIKAZI_POPUP = prikazi_popup_fn


class CenovnikScreen(Screen):
    def on_pre_enter(self, *args):
        self.ids.input_start.text = f"{_CENE_REF.start_fee:g}"
        self.ids.input_osnovna.text = f"{_CENE_REF.tarife['Osnovna (07-22h)']:g}"
        self.ids.input_nocna.text = f"{_CENE_REF.tarife['Nocna (22-07h)']:g}"
        self.ids.input_vikend.text = f"{_CENE_REF.tarife['Vikend']:g}"
        self.ids.input_aerodromski.text = f"{_CENE_REF.tarife['Aerodromski transfer']:g}"

    def sacuvaj_cene(self):
        try:
            start = float(self.ids.input_start.text.replace(",", "."))
            osnovna = float(self.ids.input_osnovna.text.replace(",", "."))
            nocna = float(self.ids.input_nocna.text.replace(",", "."))
            vikend = float(self.ids.input_vikend.text.replace(",", "."))
            aerodromski = float(self.ids.input_aerodromski.text.replace(",", "."))
        except (ValueError, AttributeError):
            self._poruka("Unesi ispravne brojeve za sve cene.")
            return

        _CENE_REF.start_fee = start
        _CENE_REF.tarife["Osnovna (07-22h)"] = osnovna
        _CENE_REF.tarife["Nocna (22-07h)"] = nocna
        _CENE_REF.tarife["Vikend"] = vikend
        _CENE_REF.tarife["Aerodromski transfer"] = aerodromski

        app = App.get_running_app()
        _CENE_REF.sacuvaj(app.user_data_dir)

        self._poruka("Cene su sacuvane.")

    def _poruka(self, tekst):
        _PRIKAZI_POPUP("Info", tekst, size_hint=(0.8, 0.3))

class NocnaTarifaScreen(Screen):
    tekst_status = StringProperty("")
    tekst_dugme = StringProperty("")
    tint_dugme = (0.7, 0.9, 0.72, 1)

    def on_pre_enter(self, *args):
        self._osvezi()

    def _osvezi(self):
        if _CENE_REF.nocna_aktivna:
            self.tekst_status = "Nocna tarifa: UKLJUCENA"
            self.tekst_dugme = "Iskljuci nocnu tarifu"
            self.tint_dugme = (0.66, 0.30, 0.34, 1)
        else:
            self.tekst_status = "Nocna tarifa: ISKLJUCENA"
            self.tekst_dugme = "Ukljuci nocnu tarifu"
            self.tint_dugme = (0.30, 0.52, 0.36, 1)

    def promeni(self):
        _CENE_REF.nocna_aktivna = not _CENE_REF.nocna_aktivna
        app = App.get_running_app()
        _CENE_REF.sacuvaj(app.user_data_dir)
        self._osvezi()


CENOVNIK_KV = """
# ============================================================
# CENOVNIK - izmena cena tarifa i start takse
# ============================================================

<CenovnikScreen>:
    name: "cene"
    ScreenRoot:

        TitleLabel:
            text: "Cene / Tarife"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Podesavanja"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "podesavanja"

        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: dp(4)

                FieldLabel:
                    text: "Start taksa (RSD)"

                PastelTextInput:
                    id: input_start
                    input_filter: "float"

                FieldLabel:
                    text: "Osnovna (07-22h) - cena po km"

                PastelTextInput:
                    id: input_osnovna
                    input_filter: "float"

                FieldLabel:
                    text: "Nocna (22-07h) - cena po km"

                PastelTextInput:
                    id: input_nocna
                    input_filter: "float"

                FieldLabel:
                    text: "Vikend - cena po km"

                PastelTextInput:
                    id: input_vikend
                    input_filter: "float"

                FieldLabel:
                    text: "Aerodromski transfer - cena po km"

                PastelTextInput:
                    id: input_aerodromski
                    input_filter: "float"

                RoundButton:
                    label_text: "Sacuvaj cene"
                    tint: 0.30, 0.52, 0.36, 1
                    text_color: 0.92, 1, 0.94, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.sacuvaj_cene()


# ============================================================
# NOCNA TARIFA - prekidac
# ============================================================

<NocnaTarifaScreen>:
    name: "nocna_tarifa"
    ScreenRoot:

        TitleLabel:
            text: "Nocna tarifa"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Podesavanja"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "podesavanja"

        PastelCard:
            tint: 0.38, 0.32, 0.52, 0.92
            size_hint_y: None
            height: self.minimum_height
            padding: dp(14)
            Label:
                id: label_status
                text: root.tekst_status
                font_size: '18sp'
                bold: True
                color: 0.92, 0.88, 1, 1
                halign: "center"
                valign: "middle"
                size_hint_y: None
                text_size: self.width, None
                height: self.texture_size[1]

        RoundButton:
            id: dugme_toggle
            label_text: root.tekst_dugme
            tint: root.tint_dugme
            text_color: 0.1, 0.1, 0.1, 1
            size_hint_y: None
            height: dp(52)
            on_release: root.promeni()

        FieldLabel:
            text: "Kada je ukljucena, kalkulator ce pri otvaranju automatski predloziti nocnu tarifu (i dalje mozes rucno da promenis tarifu za konkretnu voznju)."
            size_hint_y: None
            height: dp(60)
            text_size: self.width, None

        Widget:


"""
