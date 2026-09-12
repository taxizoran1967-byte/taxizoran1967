"""
ekran_gorivo.py
Evidencija sipanja goriva (vrsta, litara, cena, km na pumpi).

Izdvojeno iz main.py - isti obrazac kao grafik_zarade.py.
"""

import threading
from datetime import datetime

from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.properties import StringProperty
from kivy.app import App
from kivy.clock import Clock

from servisi import ocr_racun


# ============================================================
# main.py ovo postavlja posle uvoza (izbegava kruzni import)
# ============================================================

_GORIVO_REF = None         # main._GORIVO_REF
_API_REF = None            # main.API (ApiPodesavanja instanca - ocr_kljuc)
_FORMATIRAJ_CENU = None    # main.formatiraj_cenu
_NAPRAVI_RED_LISTE = None  # main.napravi_red_liste
_PRIKAZI_POPUP = None      # main._prikazi_popup_poruku


def poveži(gorivo_obj, api_obj, formatiraj_cenu_fn, napravi_red_liste_fn, prikazi_popup_fn):
    """main.py poziva ovo jednom, odmah posle 'import ekran_gorivo'."""
    global _GORIVO_REF, _API_REF, _FORMATIRAJ_CENU, _NAPRAVI_RED_LISTE, _PRIKAZI_POPUP
    _GORIVO_REF = gorivo_obj
    _API_REF = api_obj
    _FORMATIRAJ_CENU = formatiraj_cenu_fn
    _NAPRAVI_RED_LISTE = napravi_red_liste_fn
    _PRIKAZI_POPUP = prikazi_popup_fn


class GorivoScreen(Screen):
    tekst_ukupno = StringProperty("Ukupno potroseno: 0 RSD")
    dugme_tekst = StringProperty("Sacuvaj unos")
    tekst_ocr_status = StringProperty("")
    izmena_id = None

    def on_pre_enter(self, *args):
        self.tekst_ocr_status = ""
        self.ucitaj_gorivo()

    def skeniraj_racun(self):
        if not _API_REF.ocr_kljuc:
            self._poruka(
                "Prvo unesi OCR.space API kljuc u Podesavanja -> Google API "
                "(besplatan je na ocr.space/ocrapi)."
            )
            return

        try:
            from plyer import filechooser
        except Exception:
            self._poruka("Biranje slike nije dostupno na ovom uredjaju.")
            return

        def na_izbor(fajlovi):
            if not fajlovi:
                return
            self.tekst_ocr_status = "Ucitavam racun, sacekaj..."
            threading.Thread(
                target=self._obradi_racun, args=(fajlovi[0],), daemon=True
            ).start()

        try:
            filechooser.open_file(on_selection=na_izbor, multiple=False)
        except Exception as e:
            self._poruka(f"Ne mogu da otvorim galeriju:\n{e}")

    def _obradi_racun(self, putanja_slike):
        try:
            podaci = ocr_racun.ocitaj_racun(putanja_slike, _API_REF.ocr_kljuc)
        except Exception as e:
            Clock.schedule_once(lambda dt: self._ocr_greska(str(e)))
            return
        Clock.schedule_once(lambda dt: self._primeni_ocr(podaci))

    def _ocr_greska(self, poruka):
        self.tekst_ocr_status = ""
        self._poruka(f"OCR nije uspeo:\n{poruka}")

    def _primeni_ocr(self, podaci):
        litara = podaci.get("litara")
        cena_po_litru = podaci.get("cena_po_litru")
        ukupna_cena = podaci.get("ukupna_cena")
        pumpa = podaci.get("pumpa")
        grad = podaci.get("grad")

        if litara:
            self.ids.input_litara.text = f"{litara:g}"

        if litara and cena_po_litru:
            self.ids.input_cena_goriva.text = f"{round(litara * cena_po_litru, 2):g}"
        elif ukupna_cena:
            self.ids.input_cena_goriva.text = f"{ukupna_cena:g}"

        napomena_delovi = [deo for deo in (pumpa, grad) if deo]
        if napomena_delovi:
            self.ids.input_napomena_gorivo.text = ", ".join(napomena_delovi)

        if litara or ukupna_cena:
            self.tekst_ocr_status = "Racun ucitan - proveri podatke pre cuvanja."
        else:
            self.tekst_ocr_status = (
                "OCR nije uspeo da prepozna kolicinu/cenu - unesi ih rucno."
            )

    def ucitaj_gorivo(self):
        kontejner = self.ids.lista_gorivo
        kontejner.clear_widgets()

        ukupno = sum(s.get("cena", 0) for s in _GORIVO_REF.stavke)
        ukupno_benzin = sum(
            s.get("cena", 0) for s in _GORIVO_REF.stavke if s.get("tip") == "Benzin"
        )
        ukupno_tng = sum(
            s.get("cena", 0) for s in _GORIVO_REF.stavke if s.get("tip") == "TNG"
        )
        self.tekst_ukupno = (
            f"Ukupno: {_FORMATIRAJ_CENU(ukupno)}\n"
            f"Benzin: {_FORMATIRAJ_CENU(ukupno_benzin)}   |   TNG: {_FORMATIRAJ_CENU(ukupno_tng)}"
        )

        if not _GORIVO_REF.stavke:
            kontejner.add_widget(Label(
                text="Jos uvek nema unosa goriva.",
                size_hint_y=None, height=40,
                color=(1, 1, 1, 1),
            ))
            return

        for s in _GORIVO_REF.stavke:
            kontejner.add_widget(self._napravi_red(s))

    def _napravi_red(self, s):
        napomena = s.get("napomena") or "-"
        tip = s.get("tip", "Benzin")
        km_pumpe = s.get("km_pumpe")
        km_tekst = f"  |  {km_pumpe:g} km" if km_pumpe else ""
        opis = (
            f"[b]{s.get('datum', '-')}[/b]\n"
            f"{tip}  |  {s.get('litara', 0):g} l{km_tekst}\n"
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
        s = _GORIVO_REF.nadji(stavka_id)
        if not s:
            return
        self.izmena_id = stavka_id
        self.ids.input_litara.text = f"{s.get('litara', 0):g}"
        self.ids.input_cena_goriva.text = f"{s.get('cena', 0):g}"
        self.ids.input_km_pumpe.text = f"{s.get('km_pumpe'):g}" if s.get("km_pumpe") else ""
        self.ids.input_napomena_gorivo.text = s.get("napomena") or ""
        tip = s.get("tip", "Benzin")
        if tip in self.ids.spinner_tip_goriva.values:
            self.ids.spinner_tip_goriva.text = tip
        self.dugme_tekst = "Sacuvaj izmenu"

    def sacuvaj_gorivo(self):
        try:
            litara = float(self.ids.input_litara.text.replace(",", "."))
            cena = float(self.ids.input_cena_goriva.text.replace(",", "."))
        except (ValueError, AttributeError):
            self._poruka("Unesi ispravne brojeve za kolicinu i cenu.")
            return

        km_pumpe_tekst = self.ids.input_km_pumpe.text.strip()
        km_pumpe = None
        if km_pumpe_tekst:
            try:
                km_pumpe = float(km_pumpe_tekst.replace(",", "."))
            except ValueError:
                self._poruka("Kilometraza na pumpi mora biti broj (ili ostavi prazno).")
                return

        app = App.get_running_app()
        stavka = {
            "datum": datetime.now().strftime("%Y-%m-%d"),
            "tip": self.ids.spinner_tip_goriva.text,
            "litara": litara,
            "cena": cena,
            "km_pumpe": km_pumpe,
            "napomena": self.ids.input_napomena_gorivo.text.strip(),
        }

        if self.izmena_id is not None:
            _GORIVO_REF.azuriraj(app.user_data_dir, self.izmena_id, stavka)
            self.izmena_id = None
            self.dugme_tekst = "Sacuvaj unos"
            self._poruka("Izmena sacuvana.")
        else:
            _GORIVO_REF.dodaj(app.user_data_dir, stavka)
            self._poruka("Unos sacuvan.")

        self.ids.input_litara.text = ""
        self.ids.input_cena_goriva.text = ""
        self.ids.input_km_pumpe.text = ""
        self.ids.input_napomena_gorivo.text = ""
        self.ids.spinner_tip_goriva.text = "Benzin"
        self.tekst_ocr_status = ""

        self.ucitaj_gorivo()

    def _obrisi(self, stavka_id):
        app = App.get_running_app()
        _GORIVO_REF.obrisi(app.user_data_dir, stavka_id)
        if self.izmena_id == stavka_id:
            self.izmena_id = None
            self.dugme_tekst = "Sacuvaj unos"
        self.ucitaj_gorivo()

    def _poruka(self, tekst):
        _PRIKAZI_POPUP("Info", tekst, size_hint=(0.8, 0.3))


GORIVO_KV = """
# ============================================================
# _GORIVO_REF
# ============================================================

<GorivoScreen>:
    name: "gorivo"
    ScreenRoot:

        TitleLabel:
            text: "Gorivo"

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
                        id: label_ukupno_gorivo
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
                    text: "Vrsta goriva"

                RoundButton:
                    label_text: "Skeniraj racun (OCR)"
                    tint: 0.36, 0.46, 0.64, 1
                    text_color: 1, 1, 1, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.skeniraj_racun()

                Label:
                    text: root.tekst_ocr_status
                    font_size: '13sp'
                    color: 1, 0.90, 0.80, 1
                    size_hint_y: None
                    height: dp(24) if root.tekst_ocr_status else 0
                    halign: "left"
                    valign: "middle"
                    text_size: self.width, None

                Spinner:
                    id: spinner_tip_goriva
                    text: "Benzin"
                    values: ["Benzin", "TNG"]
                    size_hint_y: None
                    height: dp(48)
                    background_color: 0.78, 0.80, 0.90, 1
                    color: 0.12, 0.12, 0.24, 1

                FieldLabel:
                    text: "Kolicina (litara)"

                PastelTextInput:
                    id: input_litara
                    hint_text: "npr. 30"
                    input_filter: "float"

                FieldLabel:
                    text: "Cena (RSD)"

                PastelTextInput:
                    id: input_cena_goriva
                    hint_text: "npr. 3200"
                    input_filter: "float"

                FieldLabel:
                    text: "Kilometraza na pumpi (opciono, za tacnu potrosnju)"

                PastelTextInput:
                    id: input_km_pumpe
                    hint_text: "npr. 152340"
                    input_filter: "float"

                FieldLabel:
                    text: "Napomena (opciono)"

                PastelTextInput:
                    id: input_napomena_gorivo
                    hint_text: "npr. NIS pumpa"

                RoundButton:
                    label_text: root.dugme_tekst
                    tint: 0.30, 0.52, 0.36, 1
                    text_color: 0.92, 1, 0.94, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.sacuvaj_gorivo()

                BoxLayout:
                    id: lista_gorivo
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(10)
                    padding: dp(4), dp(10)


"""
