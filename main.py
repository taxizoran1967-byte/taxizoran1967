"""
Taksi App - licna aplikacija za taksistu
Kalkulator cene, evidencija voznji, dnevni/mesecni izvestaj zarade.
"""

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import StringProperty
from datetime import datetime

import database as db

# ========================
# TARIFE (iste kao u Telegram botu)
# ========================
TARIFE = {
    "Osnovna (07-22h)": 80,
    "Nocna (22-07h)": 100,
    "Vikend": 90,
    "Aerodromski transfer": 120,
}
START_FEE = 200

KV = """
#:import dp kivy.metrics.dp

ScreenManager:
    KalkulatorScreen:
    EvidencijaScreen:
    IzvestajScreen:

<NavBar@BoxLayout>:
    size_hint_y: None
    height: dp(50)
    spacing: dp(4)
    padding: dp(4)

<TitleLabel@Label>:
    size_hint_y: None
    height: dp(40)
    font_size: '20sp'
    bold: True
    color: 0.1, 0.1, 0.1, 1

<KalkulatorScreen>:
    name: "kalkulator"
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(8)

        TitleLabel:
            text: "Kalkulator voznje"

        NavBar:
            Button:
                text: "Kalkulator"
                on_release: root.manager.current = "kalkulator"
            Button:
                text: "Evidencija"
                on_release: root.manager.current = "evidencija"
            Button:
                text: "Izvestaj"
                on_release: root.manager.current = "izvestaj"

        ScrollView:
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(10)
                padding: dp(4)

                Label:
                    text: "Tarifa:"
                    size_hint_y: None
                    height: dp(24)
                    halign: "left"
                    text_size: self.size

                Spinner:
                    id: spinner_tarifa
                    text: root.tarife_lista[0]
                    values: root.tarife_lista
                    size_hint_y: None
                    height: dp(44)
                    on_text: root.izracunaj()

                Label:
                    text: "Kilometraza (km):"
                    size_hint_y: None
                    height: dp(24)
                    halign: "left"
                    text_size: self.size

                TextInput:
                    id: input_km
                    hint_text: "npr. 8.5"
                    input_filter: "float"
                    multiline: False
                    size_hint_y: None
                    height: dp(44)
                    on_text: root.izracunaj()

                Label:
                    text: "Od (opciono):"
                    size_hint_y: None
                    height: dp(24)
                    halign: "left"
                    text_size: self.size

                TextInput:
                    id: input_od
                    hint_text: "adresa polazista"
                    multiline: False
                    size_hint_y: None
                    height: dp(44)

                Label:
                    text: "Do (opciono):"
                    size_hint_y: None
                    height: dp(24)
                    halign: "left"
                    text_size: self.size

                TextInput:
                    id: input_do
                    hint_text: "adresa odredista"
                    multiline: False
                    size_hint_y: None
                    height: dp(44)

                Label:
                    text: "Napomena (opciono):"
                    size_hint_y: None
                    height: dp(24)
                    halign: "left"
                    text_size: self.size

                TextInput:
                    id: input_napomena
                    hint_text: "npr. cekanje, prtljag..."
                    multiline: False
                    size_hint_y: None
                    height: dp(44)

                BoxLayout:
                    size_hint_y: None
                    height: dp(90)
                    canvas.before:
                        Color:
                            rgba: 0.90, 0.95, 0.90, 1
                        Rectangle:
                            pos: self.pos
                            size: self.size
                    Label:
                        id: label_cena
                        text: root.tekst_cene
                        font_size: '22sp'
                        bold: True
                        color: 0.05, 0.4, 0.05, 1

                Button:
                    text: "Sacuvaj voznju"
                    size_hint_y: None
                    height: dp(50)
                    background_color: 0.2, 0.6, 0.2, 1
                    on_release: root.sacuvaj_voznju()

<EvidencijaScreen>:
    name: "evidencija"
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(8)

        TitleLabel:
            text: "Evidencija voznji"

        NavBar:
            Button:
                text: "Kalkulator"
                on_release: root.manager.current = "kalkulator"
            Button:
                text: "Evidencija"
                on_release: root.manager.current = "evidencija"
            Button:
                text: "Izvestaj"
                on_release: root.manager.current = "izvestaj"

        ScrollView:
            BoxLayout:
                id: lista_voznji
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(6)
                padding: dp(4)

<IzvestajScreen>:
    name: "izvestaj"
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(8)

        TitleLabel:
            text: "Izvestaj zarade"

        NavBar:
            Button:
                text: "Kalkulator"
                on_release: root.manager.current = "kalkulator"
            Button:
                text: "Evidencija"
                on_release: root.manager.current = "evidencija"
            Button:
                text: "Izvestaj"
                on_release: root.manager.current = "izvestaj"

        BoxLayout:
            size_hint_y: None
            height: dp(120)
            canvas.before:
                Color:
                    rgba: 0.90, 0.93, 0.98, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                id: label_danas
                text: root.tekst_danas
                font_size: '16sp'
                halign: "left"
                valign: "top"
                text_size: self.size
                padding: dp(10), dp(10)

        BoxLayout:
            size_hint_y: None
            height: dp(120)
            canvas.before:
                Color:
                    rgba: 0.95, 0.93, 0.90, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                id: label_mesec
                text: root.tekst_mesec
                font_size: '16sp'
                halign: "left"
                valign: "top"
                text_size: self.size
                padding: dp(10), dp(10)

        Widget:
"""


class KalkulatorScreen(Screen):
    tekst_cene = StringProperty("Unesi kilometrazu da vidis cenu")
    tarife_lista = list(TARIFE.keys())

    def izracunaj(self):
        try:
            km = float(self.ids.input_km.text.replace(",", "."))
        except (ValueError, AttributeError):
            self.tekst_cene = "Unesi kilometrazu da vidis cenu"
            return
        tarifa_naziv = self.ids.spinner_tarifa.text
        cena_po_km = TARIFE.get(tarifa_naziv, TARIFE["Osnovna (07-22h)"])
        ukupno = START_FEE + km * cena_po_km
        self.tekst_cene = (
            f"Cena: {ukupno:.0f} RSD\n"
            f"(start {START_FEE} + {km:g} km x {cena_po_km} RSD)"
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
        cena_po_km = TARIFE.get(tarifa_naziv, TARIFE["Osnovna (07-22h)"])
        ukupno = START_FEE + km * cena_po_km

        db.dodaj_voznju(
            od_adresa=self.ids.input_od.text.strip(),
            do_adresa=self.ids.input_do.text.strip(),
            km=km,
            tarifa_naziv=tarifa_naziv,
            cena_po_km=cena_po_km,
            start_taksa=START_FEE,
            ukupna_cena=ukupno,
            napomena=self.ids.input_napomena.text.strip(),
        )

        # reset forme
        self.ids.input_km.text = ""
        self.ids.input_od.text = ""
        self.ids.input_do.text = ""
        self.ids.input_napomena.text = ""
        self.tekst_cene = "Unesi kilometrazu da vidis cenu"

        self._poruka(f"Sacuvano! Cena voznje: {ukupno:.0f} RSD")

    def _poruka(self, tekst):
        popup = Popup(
            title="Info",
            content=Label(text=tekst),
            size_hint=(0.8, 0.3),
        )
        popup.open()


class EvidencijaScreen(Screen):
    def on_pre_enter(self, *args):
        self.ucitaj_voznje()

    def ucitaj_voznje(self):
        kontejner = self.ids.lista_voznji
        kontejner.clear_widgets()
        voznje = db.sve_voznje(limit=200)

        if not voznje:
            kontejner.add_widget(Label(
                text="Jos uvek nema evidentiranih voznji.",
                size_hint_y=None, height=40,
            ))
            return

        for v in voznje:
            red = self._napravi_red(v)
            kontejner.add_widget(red)

    def _napravi_red(self, v):
        od = v["od_adresa"] or "-"
        do = v["do_adresa"] or "-"
        opis = (
            f"[b]{v['datum']} {v['vreme']}[/b]  |  {v['km']:g} km  |  "
            f"{v['tarifa_naziv']}\n{od} -> {do}\n"
            f"[color=1a7a1a][b]{v['ukupna_cena']:.0f} RSD[/b][/color]"
        )
        red = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=80,
            spacing=8,
        )
        red.add_widget(Label(
            text=opis, markup=True, halign="left", valign="middle",
            text_size=(None, None),
        ))
        obrisi_dugme = Button(text="Obrisi", size_hint_x=None, width=80)
        obrisi_dugme.bind(on_release=lambda inst, vid=v["id"]: self._obrisi(vid))
        red.add_widget(obrisi_dugme)
        return red

    def _obrisi(self, voznja_id):
        db.obrisi_voznju(voznja_id)
        self.ucitaj_voznje()


class IzvestajScreen(Screen):
    tekst_danas = StringProperty("")
    tekst_mesec = StringProperty("")

    def on_pre_enter(self, *args):
        self.osvezi()

    def osvezi(self):
        danas = datetime.now().strftime("%Y-%m-%d")
        mesec = datetime.now().strftime("%Y-%m")

        voznje_danas = db.voznje_za_datum(danas)
        broj_d, prihod_d, km_d = db.zbir_voznji(voznje_danas)
        self.tekst_danas = (
            f"DANAS ({danas})\n"
            f"Broj voznji: {broj_d}\n"
            f"Ukupno km: {km_d:.1f}\n"
            f"Ukupna zarada: {prihod_d:.0f} RSD"
        )

        voznje_mesec = db.voznje_za_mesec(mesec)
        broj_m, prihod_m, km_m = db.zbir_voznji(voznje_mesec)
        self.tekst_mesec = (
            f"OVAJ MESEC ({mesec})\n"
            f"Broj voznji: {broj_m}\n"
            f"Ukupno km: {km_m:.1f}\n"
            f"Ukupna zarada: {prihod_m:.0f} RSD"
        )


class TaksiApp(App):
    def build(self):
        db.init_db()
        self.title = "Taksi App"
        return Builder.load_string(KV)


if __name__ == "__main__":
    TaksiApp().run()
