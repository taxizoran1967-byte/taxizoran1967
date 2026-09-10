"""
ekran_kalkulator.py
Rucni unos voznje (izbor tarife, kilometraza -> automatski
izracunata cena) - koristi se i za dodavanje NOVE voznje i za IZMENU
postojece (kad korisnik klikne "Izmeni" na ekranu Evidencija).

Izdvojeno iz main.py - isti obrazac kao grafik_zarade.py.
"""

from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, DictProperty, ListProperty
from kivy.app import App

from servisi import database as db
from servisi import i18n


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
    tekstovi = DictProperty({})
    tekst_cene = StringProperty("Unesi kilometrazu da vidis cenu")
    dugme_tekst = StringProperty("Sacuvaj voznju")
    tarife_prikaz = ListProperty([])
    @property
    def tarife_lista(self):
        return list(_DEFAULT_TARIFE.keys())
    editing_id = None
    _prikaz_u_tarifu = {}

    def osvezi_tekstove(self):
        app = App.get_running_app()
        jezik = getattr(app, "jezik", "sr") if app else "sr"
        self.tekstovi = {
            "title": i18n.prevedi(jezik, "calc_title"),
            "home": i18n.prevedi(jezik, "nav_home"),
            "history": i18n.prevedi(jezik, "calc_nav_history"),
            "report": i18n.prevedi(jezik, "calc_nav_report"),
            "tariff": i18n.prevedi(jezik, "calc_tariff"),
            "distance": i18n.prevedi(jezik, "calc_distance"),
            "distance_hint": i18n.prevedi(jezik, "calc_distance_hint"),
            "from": i18n.prevedi(jezik, "calc_from"),
            "from_hint": i18n.prevedi(jezik, "calc_from_hint"),
            "to": i18n.prevedi(jezik, "calc_to"),
            "to_hint": i18n.prevedi(jezik, "calc_to_hint"),
            "note": i18n.prevedi(jezik, "calc_note"),
            "note_hint": i18n.prevedi(jezik, "calc_note_hint"),
            "save": i18n.prevedi(jezik, "calc_save_ride"),
            "save_edit": i18n.prevedi(jezik, "calc_save_edit"),
        }
        self.tarife_prikaz = [
            i18n.prevedi_tarifu(tarifa, jezik) for tarifa in self.tarife_lista
        ]
        self._prikaz_u_tarifu = dict(zip(self.tarife_prikaz, self.tarife_lista))
        self.dugme_tekst = (
            self.tekstovi["save_edit"] if self.editing_id is not None else self.tekstovi["save"]
        )
        self._osvezi_spinner_tarife()
        self.izracunaj()

    def _osvezi_spinner_tarife(self):
        spinner = self.ids.get("spinner_tarifa")
        if spinner is None:
            return
        trenutni_kljuc = self._tarifa_kljuc()
        spinner.values = self.tarife_prikaz
        spinner.text = i18n.prevedi_tarifu(trenutni_kljuc, self._jezik())

    def _jezik(self):
        app = App.get_running_app()
        return getattr(app, "jezik", "sr") if app else "sr"

    def _tarifa_kljuc(self):
        spinner = self.ids.get("spinner_tarifa")
        if spinner is None:
            return self.tarife_lista[0]
        tekst = spinner.text
        if tekst in self._prikaz_u_tarifu:
            return self._prikaz_u_tarifu[tekst]
        if tekst in self.tarife_lista:
            return tekst
        return self.tarife_lista[0]

    def on_pre_enter(self, *args):
        self.osvezi_tekstove()
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
                self.ids.spinner_tarifa.text = i18n.prevedi_tarifu(tarifa, self._jezik())
            self.dugme_tekst = self.tekstovi["save_edit"]
            self.izracunaj()
            EDIT_VOZNJA = None
        else:
            self.editing_id = None
            self.dugme_tekst = self.tekstovi["save"]
            if _CENE_REF.nocna_aktivna and "spinner_tarifa" in self.ids:
                self.ids.spinner_tarifa.text = i18n.prevedi_tarifu("Nocna (22-07h)", self._jezik())
                self.izracunaj()

    def izracunaj(self):
        try:
            km = float(self.ids.input_km.text.replace(",", "."))
        except (ValueError, AttributeError):
            self.tekst_cene = i18n.prevedi(self._jezik(), "calc_enter_km")
            return
        tarifa_naziv = self._tarifa_kljuc()
        cena_po_km = _CENE_REF.tarife.get(tarifa_naziv, _CENE_REF.tarife["Osnovna (07-22h)"])
        ukupno = _CENE_REF.start_fee + km * cena_po_km
        self.tekst_cene = (
            i18n.prevedi(self._jezik(), "calc_price", price=_FORMATIRAJ_CENU(ukupno))
            + "\n"
            + i18n.prevedi(
                self._jezik(),
                "calc_formula",
                start=_FORMATIRAJ_CENU(_CENE_REF.start_fee),
                km=f"{km:g}",
                price=_FORMATIRAJ_CENU(cena_po_km),
            )
        )

    def sacuvaj_voznju(self):
        try:
            km = float(self.ids.input_km.text.replace(",", "."))
        except (ValueError, AttributeError):
            self._poruka(i18n.prevedi(self._jezik(), "calc_invalid_km"))
            return
        if km <= 0:
            self._poruka(i18n.prevedi(self._jezik(), "calc_km_positive"))
            return

        tarifa_naziv = self._tarifa_kljuc()
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
        self.dugme_tekst = self.tekstovi["save"]

        # reset forme
        self.ids.input_km.text = ""
        self.ids.input_od.text = ""
        self.ids.input_do.text = ""
        self.ids.input_napomena.text = ""
        self.tekst_cene = i18n.prevedi(self._jezik(), "calc_enter_km")

        if bila_izmena:
            self._poruka(
                i18n.prevedi(
                    self._jezik(), "calc_edit_saved", price=_FORMATIRAJ_CENU(ukupno)
                )
            )
        else:
            self._poruka(
                i18n.prevedi(
                    self._jezik(), "calc_saved", price=_FORMATIRAJ_CENU(ukupno)
                )
            )

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
            text: root.tekstovi.get("title", "")

        NavBar:
            RoundButton:
                label_text: root.tekstovi.get("home", "")
                tint: 0.36, 0.46, 0.64, 1
                font_size: '13sp'
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: root.tekstovi.get("history", "")
                tint: 0.36, 0.46, 0.64, 1
                font_size: '13sp'
                on_release: root.manager.current = "evidencija"
            RoundButton:
                label_text: root.tekstovi.get("report", "")
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
                    text: root.tekstovi.get("tariff", "")

                Spinner:
                    id: spinner_tarifa
                    text: root.tarife_prikaz[0] if root.tarife_prikaz else ""
                    values: root.tarife_prikaz
                    size_hint_y: None
                    height: dp(48)
                    background_color: 0.78, 0.80, 0.90, 1
                    color: 0.12, 0.12, 0.24, 1
                    on_text: root.izracunaj()

                FieldLabel:
                    text: root.tekstovi.get("distance", "")

                PastelTextInput:
                    id: input_km
                    hint_text: root.tekstovi.get("distance_hint", "")
                    input_filter: "float"
                    on_text: root.izracunaj()

                FieldLabel:
                    text: root.tekstovi.get("from", "")

                PastelTextInput:
                    id: input_od
                    hint_text: root.tekstovi.get("from_hint", "")

                FieldLabel:
                    text: root.tekstovi.get("to", "")

                PastelTextInput:
                    id: input_do
                    hint_text: root.tekstovi.get("to_hint", "")

                FieldLabel:
                    text: root.tekstovi.get("note", "")

                PastelTextInput:
                    id: input_napomena
                    hint_text: root.tekstovi.get("note_hint", "")

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
