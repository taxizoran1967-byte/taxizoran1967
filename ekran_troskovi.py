"""
ekran_troskovi.py
Evidencija ostalih troskova (Parking, Putarina, Pranje, Ostalo).

Izdvojeno iz main.py - isti obrazac kao grafik_zarade.py.
"""

from datetime import datetime

from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.properties import StringProperty
from kivy.app import App


# ============================================================
# main.py ovo postavlja posle uvoza (izbegava kruzni import)
# ============================================================

_TROSKOVI_REF = None       # main._TROSKOVI_REF
_FORMATIRAJ_CENU = None    # main.formatiraj_cenu
_NAPRAVI_RED_LISTE = None  # main.napravi_red_liste
_PRIKAZI_POPUP = None      # main._prikazi_popup_poruku


def poveži(troskovi_obj, formatiraj_cenu_fn, napravi_red_liste_fn, prikazi_popup_fn):
    """main.py poziva ovo jednom, odmah posle 'import ekran_troskovi'."""
    global _TROSKOVI_REF, _FORMATIRAJ_CENU, _NAPRAVI_RED_LISTE, _PRIKAZI_POPUP
    _TROSKOVI_REF = troskovi_obj
    _FORMATIRAJ_CENU = formatiraj_cenu_fn
    _NAPRAVI_RED_LISTE = napravi_red_liste_fn
    _PRIKAZI_POPUP = prikazi_popup_fn


class TroskoviScreen(Screen):
    tekst_ukupno = StringProperty("Ukupno troskova: 0 RSD")
    dugme_tekst = StringProperty("Sacuvaj trosak")
    izmena_id = None

    def on_pre_enter(self, *args):
        self.ucitaj_troskove()

    def ucitaj_troskove(self):
        kontejner = self.ids.lista_troskovi
        kontejner.clear_widgets()

        ukupno = sum(s.get("cena", 0) for s in _TROSKOVI_REF.stavke)
        ukupno_parking = sum(
            s.get("cena", 0) for s in _TROSKOVI_REF.stavke if s.get("vrsta") == "Parking"
        )
        ukupno_putarina = sum(
            s.get("cena", 0) for s in _TROSKOVI_REF.stavke if s.get("vrsta") == "Putarina"
        )
        self.tekst_ukupno = (
            f"Ukupno: {_FORMATIRAJ_CENU(ukupno)}\n"
            f"Parking: {_FORMATIRAJ_CENU(ukupno_parking)}   |   Putarina: {_FORMATIRAJ_CENU(ukupno_putarina)}"
        )

        if not _TROSKOVI_REF.stavke:
            kontejner.add_widget(Label(
                text="Jos uvek nema unetih troskova.",
                size_hint_y=None, height=40,
                color=(1, 1, 1, 1),
            ))
            return

        for s in _TROSKOVI_REF.stavke:
            kontejner.add_widget(self._napravi_red(s))

    def _napravi_red(self, s):
        napomena = s.get("napomena") or "-"
        opis = (
            f"[b]{s.get('datum', '-')}[/b]\n"
            f"{s.get('vrsta', '-')}\n"
            f"{napomena}\n"
            f"[color=6b3d0d][b]{_FORMATIRAJ_CENU(s.get('cena', 0))}[/b][/color]"
        )
        return _NAPRAVI_RED_LISTE(
            opis,
            tint=(0.55, 0.38, 0.26, 0.92),
            boja_teksta=(1, 0.92, 0.85, 1),
            dugmad=[
                ("Izmeni", (0.36, 0.46, 0.64, 1), (0.95, 0.96, 1, 1),
                 lambda inst, sid=s["id"]: self._izmeni(sid)),
                ("Obrisi", (0.66, 0.30, 0.34, 1), (1, 0.95, 0.95, 1),
                 lambda inst, sid=s["id"]: self._obrisi(sid)),
            ],
        )

    def _izmeni(self, stavka_id):
        s = _TROSKOVI_REF.nadji(stavka_id)
        if not s:
            return
        self.izmena_id = stavka_id
        self.ids.input_cena_troska.text = f"{s.get('cena', 0):g}"
        self.ids.input_napomena_troska.text = s.get("napomena") or ""
        vrsta = s.get("vrsta", "Parking")
        if vrsta in self.ids.spinner_vrsta_troska.values:
            self.ids.spinner_vrsta_troska.text = vrsta
        self.dugme_tekst = "Sacuvaj izmenu"

    def sacuvaj_trosak(self):
        try:
            cena = float(self.ids.input_cena_troska.text.replace(",", "."))
        except (ValueError, AttributeError):
            self._poruka("Unesi ispravan broj za cenu.")
            return

        app = App.get_running_app()
        stavka = {
            "datum": datetime.now().strftime("%Y-%m-%d"),
            "vrsta": self.ids.spinner_vrsta_troska.text,
            "cena": cena,
            "napomena": self.ids.input_napomena_troska.text.strip(),
        }

        if self.izmena_id is not None:
            _TROSKOVI_REF.azuriraj(app.user_data_dir, self.izmena_id, stavka)
            self.izmena_id = None
            self.dugme_tekst = "Sacuvaj trosak"
            self._poruka("Izmena sacuvana.")
        else:
            _TROSKOVI_REF.dodaj(app.user_data_dir, stavka)
            self._poruka("Trosak sacuvan.")

        self.ids.input_cena_troska.text = ""
        self.ids.input_napomena_troska.text = ""
        self.ids.spinner_vrsta_troska.text = "Parking"

        self.ucitaj_troskove()

    def _obrisi(self, stavka_id):
        app = App.get_running_app()
        _TROSKOVI_REF.obrisi(app.user_data_dir, stavka_id)
        if self.izmena_id == stavka_id:
            self.izmena_id = None
            self.dugme_tekst = "Sacuvaj trosak"
        self.ucitaj_troskove()

    def _poruka(self, tekst):
        _PRIKAZI_POPUP("Info", tekst, size_hint=(0.8, 0.3))

TROSKOVI_KV = """
# ============================================================
# OSTALI _TROSKOVI_REF - parking, putarina, pranje, ostalo
# ============================================================

<TroskoviScreen>:
    name: "troskovi"
    ScreenRoot:

        TitleLabel:
            text: "Ostali troskovi"

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

                PastelCard:
                    tint: 0.55, 0.38, 0.26, 0.92
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(12)
                    Label:
                        id: label_ukupno_troskovi
                        text: root.tekst_ukupno
                        font_size: '14sp'
                        bold: True
                        color: 1, 0.90, 0.80, 1
                        halign: "left"
                        valign: "middle"
                        size_hint_y: None
                        text_size: self.width, None
                        height: self.texture_size[1]

                FieldLabel:
                    text: "Vrsta troska"

                Spinner:
                    id: spinner_vrsta_troska
                    text: "Parking"
                    values: ["Parking", "Putarina", "Pranje", "Ostalo"]
                    size_hint_y: None
                    height: dp(48)
                    background_color: 0.78, 0.80, 0.90, 1
                    color: 0.12, 0.12, 0.24, 1

                FieldLabel:
                    text: "Cena (RSD)"

                PastelTextInput:
                    id: input_cena_troska
                    hint_text: "npr. 150"
                    input_filter: "float"

                FieldLabel:
                    text: "Napomena (opciono)"

                PastelTextInput:
                    id: input_napomena_troska
                    hint_text: "npr. parking centar grada"

                RoundButton:
                    label_text: root.dugme_tekst
                    tint: 0.30, 0.52, 0.36, 1
                    text_color: 0.92, 1, 0.94, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.sacuvaj_trosak()

                BoxLayout:
                    id: lista_troskovi
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(10)
                    padding: dp(4), dp(10)


"""
