"""
ekran_evidencija.py
Istorija svih voznji, sa pretragom (tekst, period, opseg cene) i
mogucnoscu izmene/brisanja pojedinacne voznje.

Izdvojeno iz main.py - isti obrazac kao grafik_zarade.py.
"""

from datetime import datetime

from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.properties import StringProperty

from servisi import database as db
from ekrani import ekran_kalkulator


# ============================================================
# main.py ovo postavlja posle uvoza (izbegava kruzni import)
# ============================================================

_FORMATIRAJ_CENU = None    # main.formatiraj_cenu
_NAPRAVI_RED_LISTE = None  # main.napravi_red_liste
_PRIKAZI_POPUP = None      # main._prikazi_popup_poruku


def poveži(formatiraj_cenu_fn, napravi_red_liste_fn, prikazi_popup_fn):
    """main.py poziva ovo jednom, odmah posle 'import ekran_evidencija'."""
    global _FORMATIRAJ_CENU, _NAPRAVI_RED_LISTE, _PRIKAZI_POPUP
    _FORMATIRAJ_CENU = formatiraj_cenu_fn
    _NAPRAVI_RED_LISTE = napravi_red_liste_fn
    _PRIKAZI_POPUP = prikazi_popup_fn


class EvidencijaScreen(Screen):
    tekst_broj_rezultata = StringProperty("")

    def on_pre_enter(self, *args):
        self.ucitaj_voznje()

    def ucitaj_voznje(self, voznje=None):
        kontejner = self.ids.lista_voznji
        kontejner.clear_widgets()

        if voznje is None:
            voznje = db.sve_voznje(limit=200)
            self.tekst_broj_rezultata = ""

        if not voznje:
            poruka = (
                "Nema voznji koje odgovaraju pretrazi."
                if self.tekst_broj_rezultata else
                "Jos uvek nema evidentiranih voznji."
            )
            kontejner.add_widget(Label(
                text=poruka,
                size_hint_y=None, height=40,
                color=(1, 1, 1, 1),
            ))
            return

        for v in voznje:
            red = self._napravi_red(v)
            kontejner.add_widget(red)

    def pretrazi(self):
        tekst = self.ids.input_pretraga_tekst.text.strip() or None
        datum_od = self.ids.input_pretraga_datum_od.text.strip() or None
        datum_do = self.ids.input_pretraga_datum_do.text.strip() or None

        for naziv, vrednost in (("Datum od", datum_od), ("Datum do", datum_do)):
            if vrednost:
                try:
                    datetime.strptime(vrednost, "%Y-%m-%d")
                except ValueError:
                    _PRIKAZI_POPUP(
                        "Greska",
                        f"{naziv}: format mora biti GGGG-MM-DD (npr. 2026-09-05).",
                        size_hint=(0.85, 0.4),
                    )
                    return

        cena_od_tekst = self.ids.input_pretraga_cena_od.text.strip()
        cena_do_tekst = self.ids.input_pretraga_cena_do.text.strip()
        cena_min = None
        cena_max = None
        try:
            if cena_od_tekst:
                cena_min = float(cena_od_tekst.replace(",", "."))
            if cena_do_tekst:
                cena_max = float(cena_do_tekst.replace(",", "."))
        except ValueError:
            _PRIKAZI_POPUP("Greska", "Cena mora biti broj.", size_hint=(0.85, 0.3))
            return

        voznje = db.pretrazi_voznje(
            pocetak=datum_od, kraj=datum_do, tekst=tekst,
            cena_min=cena_min, cena_max=cena_max,
        )
        broj, prihod, km = db.zbir_voznji(voznje)
        self.tekst_broj_rezultata = (
            f"Nadjeno: {broj} voznji   |   {km:.1f} km   |   {_FORMATIRAJ_CENU(prihod)}"
        )
        self.ucitaj_voznje(voznje)

    def resetuj_pretragu(self):
        self.ids.input_pretraga_tekst.text = ""
        self.ids.input_pretraga_datum_od.text = ""
        self.ids.input_pretraga_datum_do.text = ""
        self.ids.input_pretraga_cena_od.text = ""
        self.ids.input_pretraga_cena_do.text = ""
        self.tekst_broj_rezultata = ""
        self.ucitaj_voznje()

    def _napravi_red(self, v):
        od = v["od_adresa"] or "-"
        do = v["do_adresa"] or "-"

        vreme_pocetka = v["vreme_pocetka"] if "vreme_pocetka" in v.keys() else None
        if vreme_pocetka:
            vreme_txt = f"Pocetak {vreme_pocetka}  |  Kraj {v['vreme']}"
        else:
            vreme_txt = f"Kraj {v['vreme']}"

        opis = (
            f"[b]{v['datum']}[/b]  {vreme_txt}\n"
            f"{v['km']:g} km  |  {v['tarifa_naziv']}\n"
            f"{od}\n-> {do}\n"
            f"[color=cc8a00][b]{_FORMATIRAJ_CENU(v['ukupna_cena'])}[/b][/color]"
        )
        return _NAPRAVI_RED_LISTE(
            opis,
            tint=(0.40, 0.38, 0.52, 0.92),
            boja_teksta=(0.94, 0.93, 0.98, 1),
            dugmad=[
                ("Izmeni", (0.36, 0.46, 0.64, 1), (0.95, 0.96, 1, 1),
                 lambda inst, v=v: self._izmeni(v)),
                ("Obrisi", (0.66, 0.30, 0.34, 1), (1, 0.95, 0.95, 1),
                 lambda inst, vid=v["id"]: self._obrisi(vid)),
            ],
        )

    def _izmeni(self, v):
        ekran_kalkulator.EDIT_VOZNJA = dict(v)
        self.manager.current = "kalkulator"

    def _obrisi(self, voznja_id):
        db.obrisi_voznju(voznja_id)
        if self.tekst_broj_rezultata:
            self.pretrazi()
        else:
            self.ucitaj_voznje()

EVIDENCIJA_KV = """
# ============================================================
# EVIDENCIJA
# ============================================================

<EvidencijaScreen>:
    name: "evidencija"
    ScreenRoot:

        TitleLabel:
            text: "Evidencija voznji"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                font_size: '13sp'
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Kalkulator"
                tint: 0.36, 0.46, 0.64, 1
                font_size: '13sp'
                on_release: root.manager.current = "kalkulator"
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
                spacing: dp(10)
                padding: dp(4)

                PastelCard:
                    orientation: "vertical"
                    tint: 0.30, 0.29, 0.42, 0.92
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(12)
                    spacing: dp(8)

                    FieldLabel:
                        text: "Pretraga (adresa ili napomena)"

                    PastelTextInput:
                        id: input_pretraga_tekst
                        hint_text: "npr. bulevar, aerodrom..."

                    BoxLayout:
                        size_hint_y: None
                        height: dp(48)
                        spacing: dp(8)
                        PastelTextInput:
                            id: input_pretraga_datum_od
                            hint_text: "Datum od (GGGG-MM-DD)"
                        PastelTextInput:
                            id: input_pretraga_datum_do
                            hint_text: "Datum do (GGGG-MM-DD)"

                    BoxLayout:
                        size_hint_y: None
                        height: dp(48)
                        spacing: dp(8)
                        PastelTextInput:
                            id: input_pretraga_cena_od
                            hint_text: "Cena od"
                            input_filter: "float"
                        PastelTextInput:
                            id: input_pretraga_cena_do
                            hint_text: "Cena do"
                            input_filter: "float"

                    BoxLayout:
                        size_hint_y: None
                        height: dp(48)
                        spacing: dp(8)
                        RoundButton:
                            label_text: "Pretrazi"
                            tint: 0.30, 0.52, 0.36, 1
                            text_color: 1, 1, 1, 1
                            on_release: root.pretrazi()
                        RoundButton:
                            label_text: "Resetuj"
                            tint: 0.45, 0.45, 0.52, 1
                            text_color: 1, 1, 1, 1
                            on_release: root.resetuj_pretragu()

                FieldLabel:
                    id: label_broj_rezultata
                    text: root.tekst_broj_rezultata

                BoxLayout:
                    id: lista_voznji
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(10)
                    padding: dp(4)


"""
