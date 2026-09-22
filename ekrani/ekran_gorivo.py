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
from servisi import jezici


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

    tekst_naslov = StringProperty("Gorivo")
    tekst_pocetna = StringProperty("Pocetna")
    tekst_podesavanja = StringProperty("Podesavanja")
    tekst_vrsta_goriva = StringProperty("Vrsta goriva")
    tekst_skeniraj_racun = StringProperty("Skeniraj racun (OCR)")
    tekst_datum_label = StringProperty("Datum (GGGG-MM-DD)")
    hint_datum = StringProperty("")
    tekst_kolicina = StringProperty("Kolicina (litara)")
    hint_kolicina = StringProperty("npr. 30")
    tekst_cena_label = StringProperty("Cena (RSD)")
    hint_cena = StringProperty("npr. 3200")
    tekst_km_pumpe_label = StringProperty("Kilometraza na pumpi (opciono, za tacnu potrosnju)")
    hint_km_pumpe = StringProperty("npr. 152340")
    tekst_napomena_label = StringProperty("Napomena (opciono)")
    hint_napomena = StringProperty("npr. NIS pumpa")

    def on_pre_enter(self, *args):
        self.tekst_ocr_status = ""
        self._osvezi_prevod()
        self.ucitaj_gorivo()

    def _osvezi_prevod(self):
        self.tekst_naslov = jezici._t("gorivo.naslov")
        self.tekst_pocetna = jezici._t("buttons.pocetna")
        self.tekst_podesavanja = jezici._t("home.podesavanja")
        self.tekst_vrsta_goriva = jezici._t("gorivo.vrsta_goriva")
        self.tekst_skeniraj_racun = jezici._t("gorivo.skeniraj_racun")
        self.tekst_datum_label = jezici._t("gorivo.datum_label")
        self.hint_datum = jezici._t("gorivo.datum_hint")
        self.tekst_kolicina = jezici._t("gorivo.kolicina")
        self.hint_kolicina = jezici._t("gorivo.kolicina_hint")
        self.tekst_cena_label = jezici._t("gorivo.cena_label")
        self.hint_cena = jezici._t("gorivo.cena_hint")
        self.tekst_km_pumpe_label = jezici._t("gorivo.km_pumpe_label")
        self.hint_km_pumpe = jezici._t("gorivo.km_pumpe_hint")
        self.tekst_napomena_label = jezici._t("gorivo.napomena_label")
        self.hint_napomena = jezici._t("gorivo.napomena_hint")
        if self.izmena_id is None:
            self.dugme_tekst = jezici._t("gorivo.sacuvaj_unos")
        else:
            self.dugme_tekst = jezici._t("gorivo.sacuvaj_izmenu")

    def skeniraj_racun(self):
        if not _API_REF.ocr_kljuc:
            self._poruka(jezici._t("gorivo.api_kljuc_greska"))
            return

        try:
            from plyer import filechooser
        except Exception:
            self._poruka(jezici._t("gorivo.biranje_nedostupno"))
            return

        def na_izbor(fajlovi):
            if not fajlovi:
                return
            self.tekst_ocr_status = jezici._t("gorivo.ucitavam_racun")
            threading.Thread(
                target=self._obradi_racun, args=(fajlovi[0],), daemon=True
            ).start()

        try:
            filechooser.open_file(on_selection=na_izbor, multiple=False)
        except Exception as e:
            self._poruka(jezici._t("gorivo.ne_mogu_galeriju", greska=e))

    def _obradi_racun(self, putanja_slike):
        try:
            podaci = ocr_racun.ocitaj_racun(putanja_slike, _API_REF.ocr_kljuc)
        except Exception as e:
            Clock.schedule_once(lambda dt: self._ocr_greska(str(e)))
            return
        Clock.schedule_once(lambda dt: self._primeni_ocr(podaci))

    def _ocr_greska(self, poruka):
        self.tekst_ocr_status = ""
        self._poruka(jezici._t("gorivo.ocr_neuspesan", poruka=poruka))

    def _primeni_ocr(self, podaci):
        try:
            self._primeni_ocr_podatke(podaci)
        except Exception as e:
            self.tekst_ocr_status = ""
            self._poruka(jezici._t("gorivo.racun_greska_polja", greska=e))

    def _primeni_ocr_podatke(self, podaci):
        litara = podaci.get("litara")
        cena_po_litru = podaci.get("cena_po_litru")
        ukupna_cena = podaci.get("ukupna_cena")
        pumpa = podaci.get("pumpa")
        grad = podaci.get("grad")
        datum = podaci.get("datum")

        if datum:
            self.ids.input_datum_gorivo.text = datum

        if litara:
            self.ids.input_litara.text = f"{litara:g}"

        if litara and cena_po_litru:
            self.ids.input_cena_goriva.text = f"{round(litara * cena_po_litru, 2):g}"
        elif ukupna_cena:
            self.ids.input_cena_goriva.text = f"{ukupna_cena:g}"

        napomena_delovi = [deo for deo in (pumpa, grad) if deo]
        if napomena_delovi:
            self.ids.input_napomena_gorivo.text = ", ".join(napomena_delovi)

        if podaci.get("rotacija_ispravljena"):
            self.tekst_ocr_status = jezici._t("gorivo.racun_bio_okrenut")
        elif litara or ukupna_cena:
            self.tekst_ocr_status = jezici._t("gorivo.racun_ucitan")
        else:
            self.tekst_ocr_status = jezici._t("gorivo.ocr_ne_prepoznaje")

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
        self.tekst_ukupno = jezici._t(
            "gorivo.ukupno_format",
            ukupno=_FORMATIRAJ_CENU(ukupno),
            benzin=_FORMATIRAJ_CENU(ukupno_benzin),
            tng=_FORMATIRAJ_CENU(ukupno_tng),
        )

        if not _GORIVO_REF.stavke:
            kontejner.add_widget(Label(
                text=jezici._t("gorivo.nema_unosa"),
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
        km_tekst = jezici._t("gorivo.km_sufiks", km=f"{km_pumpe:g}") if km_pumpe else ""
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
                (jezici._t("evidencija.izmeni"), (0.36, 0.46, 0.64, 1), (0.95, 0.96, 1, 1),
                 lambda inst, sid=s["id"]: self._izmeni(sid)),
                (jezici._t("evidencija.obrisi"), (0.66, 0.30, 0.34, 1), (1, 0.95, 0.95, 1),
                 lambda inst, sid=s["id"]: self._obrisi(sid)),
            ],
        )

    def _izmeni(self, stavka_id):
        s = _GORIVO_REF.nadji(stavka_id)
        if not s:
            return
        self.izmena_id = stavka_id
        self.ids.input_datum_gorivo.text = s.get("datum", "")
        self.ids.input_litara.text = f"{s.get('litara', 0):g}"
        self.ids.input_cena_goriva.text = f"{s.get('cena', 0):g}"
        self.ids.input_km_pumpe.text = f"{s.get('km_pumpe'):g}" if s.get("km_pumpe") else ""
        self.ids.input_napomena_gorivo.text = s.get("napomena") or ""
        tip = s.get("tip", "Benzin")
        if tip in self.ids.spinner_tip_goriva.values:
            self.ids.spinner_tip_goriva.text = tip
        self.dugme_tekst = jezici._t("gorivo.sacuvaj_izmenu")

    def sacuvaj_gorivo(self):
        try:
            litara = float(self.ids.input_litara.text.replace(",", "."))
            cena = float(self.ids.input_cena_goriva.text.replace(",", "."))
        except (ValueError, AttributeError):
            self._poruka(jezici._t("gorivo.unesi_ispravne_brojeve"))
            return

        km_pumpe_tekst = self.ids.input_km_pumpe.text.strip()
        km_pumpe = None
        if km_pumpe_tekst:
            try:
                km_pumpe = float(km_pumpe_tekst.replace(",", "."))
            except ValueError:
                self._poruka(jezici._t("gorivo.km_pumpe_broj"))
                return

        datum_tekst = self.ids.input_datum_gorivo.text.strip()
        if not datum_tekst:
            datum_tekst = datetime.now().strftime("%Y-%m-%d")
        else:
            try:
                datetime.strptime(datum_tekst, "%Y-%m-%d")
            except ValueError:
                self._poruka(jezici._t("gorivo.datum_format_greska"))
                return

        app = App.get_running_app()
        stavka = {
            "datum": datum_tekst,
            "tip": self.ids.spinner_tip_goriva.text,
            "litara": litara,
            "cena": cena,
            "km_pumpe": km_pumpe,
            "napomena": self.ids.input_napomena_gorivo.text.strip(),
        }

        if self.izmena_id is not None:
            _GORIVO_REF.azuriraj(app.user_data_dir, self.izmena_id, stavka)
            self.izmena_id = None
            self.dugme_tekst = jezici._t("gorivo.sacuvaj_unos")
            self._poruka(jezici._t("gorivo.izmena_sacuvana"))
        else:
            _GORIVO_REF.dodaj(app.user_data_dir, stavka)
            self._poruka(jezici._t("gorivo.unos_sacuvan"))

        self.ids.input_datum_gorivo.text = ""
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
            self.dugme_tekst = jezici._t("gorivo.sacuvaj_unos")
        self.ucitaj_gorivo()

    def _poruka(self, tekst):
        _PRIKAZI_POPUP(jezici._t("buttons.info"), tekst, size_hint=(0.8, 0.3))


GORIVO_KV = """
# ============================================================
# _GORIVO_REF
# ============================================================

<GorivoScreen>:
    name: "gorivo"
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
                    text: root.tekst_vrsta_goriva

                RoundButton:
                    label_text: root.tekst_skeniraj_racun
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
                    text: root.tekst_datum_label

                PastelTextInput:
                    id: input_datum_gorivo
                    hint_text: root.hint_datum

                FieldLabel:
                    text: root.tekst_kolicina

                PastelTextInput:
                    id: input_litara
                    hint_text: root.hint_kolicina
                    input_filter: "float"

                FieldLabel:
                    text: root.tekst_cena_label

                PastelTextInput:
                    id: input_cena_goriva
                    hint_text: root.hint_cena
                    input_filter: "float"

                FieldLabel:
                    text: root.tekst_km_pumpe_label

                PastelTextInput:
                    id: input_km_pumpe
                    hint_text: root.hint_km_pumpe
                    input_filter: "float"

                FieldLabel:
                    text: root.tekst_napomena_label

                PastelTextInput:
                    id: input_napomena_gorivo
                    hint_text: root.hint_napomena

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
