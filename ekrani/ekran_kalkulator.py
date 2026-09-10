"""
ekran_kalkulator.py
Rucni unos voznje (izbor tarife, kilometraza -> automatski
izracunata cena) - koristi se i za dodavanje NOVE voznje i za IZMENU
postojece (kad korisnik klikne "Izmeni" na ekranu Evidencija).

Izdvojeno iz main.py - isti obrazac kao grafik_zarade.py.
"""

from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.app import App

from servisi import database as db


# Kad korisnik klikne "Izmeni" na voznji u Evidenciji (ekran_evidencija.py
# postavlja ovo direktno, preko 'import ekran_kalkulator'), podaci te
# voznje se privremeno stave ovde da bi ih ovaj ekran pokupio i
# popunio formu za ispravku.
EDIT_VOZNJA = None


# ============================================================
# main.py ovo postavlja posle uvoza (izbegava kruzni import)
# ============================================================

_DEFAULT_TARIFE = None    # main._DEFAULT_TARIFE
_CENE_REF = None          # main._CENE_REF
_FORMATIRAJ_CENU = None   # main.formatiraj_cenu
_PRIKAZI_POPUP = None     # main._prikazi_popup_poruku


def poveži(default_tarife, cene_obj, formatiraj_cenu_fn, prikazi_popup_fn):
    """main.py poziva ovo jednom, odmah posle 'import ekran_kalkulator'."""
    global _DEFAULT_TARIFE, _CENE_REF, _FORMATIRAJ_CENU, _PRIKAZI_POPUP
    _DEFAULT_TARIFE = default_tarife
    _CENE_REF = cene_obj
    _FORMATIRAJ_CENU = formatiraj_cenu_fn
    _PRIKAZI_POPUP = prikazi_popup_fn


class KalkulatorScreen(Screen):
    tekst_cene = StringProperty("Unesi kilometrazu da vidis cenu")
    dugme_tekst = StringProperty("Sacuvaj voznju")
    @property
    def tarife_lista(self):
        return list(_DEFAULT_TARIFE.keys())
    editing_id = None

    def on_pre_enter(self, *args):
        global EDIT_VOZNJA
        if EDIT_VOZNJA is not None:
            v = EDIT_VOZNJA
            self.editing_id = v.get("id")
            self.ids.input_km.text = f"{v.get('km', 0):g}"
            self.ids.input_od.text = v.get("od_adresa") or ""
            self.ids.input_do.text = v.get("do_adresa") or ""
            self.ids.input_napomena.text = v.get("napomena") or ""
            tarifa = v.get("tarifa_naziv")
            if tarifa in self.tarife_lista and "spinner_tarifa" in self.ids:
                self.ids.spinner_tarifa.text = tarifa
            self.dugme_tekst = "Sacuvaj izmenu"
            self.izracunaj()
            EDIT_VOZNJA = None
        else:
            self.editing_id = None
            self.dugme_tekst = "Sacuvaj voznju"
            if _CENE_REF.nocna_aktivna and "spinner_tarifa" in self.ids:
                self.ids.spinner_tarifa.text = "Nocna (22-07h)"
                self.izracunaj()

    def izracunaj(self):
        try:
            km = float(self.ids.input_km.text.replace(",", "."))
        except (ValueError, AttributeError):
            self.tekst_cene = "Unesi kilometrazu da vidis cenu"
            return
        tarifa_naziv = self.ids.spinner_tarifa.text
        cena_po_km = _CENE_REF.tarife.get(tarifa_naziv, _CENE_REF.tarife["Osnovna (07-22h)"])
        ukupno = _CENE_REF.start_fee + km * cena_po_km
        self.tekst_cene = (
            f"Cena: {_FORMATIRAJ_CENU(ukupno)}\n"
            f"(start {_FORMATIRAJ_CENU(_CENE_REF.start_fee)} + {km:g} km x {_FORMATIRAJ_CENU(cena_po_km)})"
        )

    def sacuvaj_voznju(self):
        try:
            km = float(self.ids.input_km.text.replace(",", "."))
        except (ValueError, AttributeError):
            self._poruka("Unesi ispravnu kilometrazu pre cuvanja.")
            return
        if km <= 0:
            self._poruka("Kilometraza mora biti veca od 0.")
            return

        tarifa_naziv = self.ids.spinner_tarifa.text
        cena_po_km = _CENE_REF.tarife.get(tarifa_naziv, _CENE_REF.tarife["Osnovna (07-22h)"])
        ukupno = _CENE_REF.start_fee + km * cena_po_km

        if self.editing_id is not None:
            db.obrisi_voznju(self.editing_id)

        db.dodaj_voznju(
            od_adresa=self.ids.input_od.text.strip(),
            do_adresa=self.ids.input_do.text.strip(),
            km=km,
            tarifa_naziv=tarifa_naziv,
            cena_po_km=cena_po_km,
            start_taksa=_CENE_REF.start_fee,
            ukupna_cena=ukupno,
            napomena=self.ids.input_napomena.text.strip(),
        )

        bila_izmena = self.editing_id is not None
        self.editing_id = None
        self.dugme_tekst = "Sacuvaj voznju"

        # reset forme
        self.ids.input_km.text = ""
        self.ids.input_od.text = ""
        self.ids.input_do.text = ""
        self.ids.input_napomena.text = ""
        self.tekst_cene = "Unesi kilometrazu da vidis cenu"

        if bila_izmena:
            self._poruka(f"Izmena sacuvana! Cena voznje: {_FORMATIRAJ_CENU(ukupno)}")
        else:
            self._poruka(f"Sacuvano! Cena voznje: {_FORMATIRAJ_CENU(ukupno)}")

    def _poruka(self, tekst):
        _PRIKAZI_POPUP("Info", tekst, size_hint=(0.8, 0.3))

KALKULATOR_KV = """
# ============================================================
# KALKULATOR
# ============================================================

<KalkulatorScreen>:
    name: "kalkulator"
    ScreenRoot:

        TitleLabel:
            text: "Kalkulator voznje"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                font_size: '13sp'
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Evidencija"
                tint: 0.36, 0.46, 0.64, 1
                font_size: '13sp'
                on_release: root.manager.current = "evidencija"
            RoundButton:
                label_text: "Izvestaj"
                tint: 0.36, 0.46, 0.64, 1
                font_size: '13sp'
                on_release: root.manager.current = "izvestaj"

        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: dp(4)

                FieldLabel:
                    text: "Tarifa"

                Spinner:
                    id: spinner_tarifa
                    text: root.tarife_lista[0]
                    values: root.tarife_lista
                    size_hint_y: None
                    height: dp(48)
                    background_color: 0.78, 0.80, 0.90, 1
                    color: 0.12, 0.12, 0.24, 1
                    on_text: root.izracunaj()

                FieldLabel:
                    text: "Kilometraza (km)"

                PastelTextInput:
                    id: input_km
                    hint_text: "npr. 8.5"
                    input_filter: "float"
                    on_text: root.izracunaj()

                FieldLabel:
                    text: "Od (opciono)"

                PastelTextInput:
                    id: input_od
                    hint_text: "adresa polazista"

                FieldLabel:
                    text: "Do (opciono)"

                PastelTextInput:
                    id: input_do
                    hint_text: "adresa odredista"

                FieldLabel:
                    text: "Napomena (opciono)"

                PastelTextInput:
                    id: input_napomena
                    hint_text: "npr. cekanje, prtljag..."

                PastelCard:
                    tint: 0.28, 0.48, 0.34, 0.92
                    size_hint_y: None
                    height: dp(96)
                    padding: dp(14)
                    Label:
                        id: label_cena
                        text: root.tekst_cene
                        font_size: '20sp'
                        bold: True
                        color: 0.90, 1, 0.92, 1
                        halign: "center"
                        valign: "middle"
                        text_size: self.size

                RoundButton:
                    label_text: root.dugme_tekst
                    tint: 0.30, 0.52, 0.36, 1
                    text_color: 0.92, 1, 0.94, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.sacuvaj_voznju()


"""
