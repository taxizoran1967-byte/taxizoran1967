"""
Taksi App - licna aplikacija za taksistu
Kalkulator cene, evidencija voznji, dnevni/mesecni izvestaj zarade.
"""

import os
import sys
import traceback

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
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

BACKGROUND_IMG = "assets/backgrounds/background.png"

KV = """
#:import dp kivy.metrics.dp

ScreenManager:
    HomeScreen:
    KalkulatorScreen:
    EvidencijaScreen:
    IzvestajScreen:
    PodesavanjaScreen:
    PlaceholderScreen:
        name: "grafik"
        naslov: "Grafik zarade"
    PlaceholderScreen:
        name: "navigacija"
        naslov: "Navigacija"
    PlaceholderScreen:
        name: "nocna_tarifa"
        naslov: "Nocna tarifa"
    PlaceholderScreen:
        name: "servis"
        naslov: "Servis vozila"
    PlaceholderScreen:
        name: "gorivo"
        naslov: "Gorivo"

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
    color: 1, 1, 1, 1

<MenuButton>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(64)
    spacing: dp(12)
    padding: dp(10)
    canvas.before:
        Color:
            rgba: 0.12, 0.10, 0.24, 0.85
        Rectangle:
            pos: self.pos
            size: self.size
    Image:
        source: root.icon_src
        size_hint_x: None
        width: dp(44)
    Label:
        text: root.tekst
        font_size: '18sp'
        bold: True
        color: 1, 1, 1, 1
        halign: "left"
        valign: "middle"
        text_size: self.size

<HomeScreen>:
    name: "home"
    BoxLayout:
        orientation: "vertical"
        padding: dp(16)
        spacing: dp(14)
        canvas.before:
            Rectangle:
                source: app.background_img
                pos: self.pos
                size: self.size

        TitleLabel:
            text: "Taksi App"
            font_size: '26sp'

        ScrollView:
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)

                MenuButton:
                    icon_src: "assets/icons/start_ride.png"
                    tekst: "Pocetak voznje"
                    on_release: app.root.current = "kalkulator"

                MenuButton:
                    icon_src: "assets/icons/end_ride.png"
                    tekst: "Kraj voznje"
                    on_release: app.root.current = "kalkulator"

                MenuButton:
                    icon_src: "assets/icons/history.png"
                    tekst: "Istorija voznji"
                    on_release: app.root.current = "evidencija"

                MenuButton:
                    icon_src: "assets/icons/daily_report.png"
                    tekst: "Izvestaj"
                    on_release: app.root.current = "izvestaj"

                MenuButton:
                    icon_src: "assets/icons/settings.png"
                    tekst: "Podesavanja"
                    on_release: app.root.current = "podesavanja"

<KalkulatorScreen>:
    name: "kalkulator"
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(8)
        canvas.before:
            Rectangle:
                source: app.background_img
                pos: self.pos
                size: self.size

        TitleLabel:
            text: "Kalkulator voznje"

        NavBar:
            Button:
                text: "Pocetna"
                on_release: root.manager.current = "home"
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
                    color: 1, 1, 1, 1

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
                    color: 1, 1, 1, 1

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
                    color: 1, 1, 1, 1

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
                    color: 1, 1, 1, 1

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
                    color: 1, 1, 1, 1

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
        canvas.before:
            Rectangle:
                source: app.background_img
                pos: self.pos
                size: self.size

        TitleLabel:
            text: "Evidencija voznji"

        NavBar:
            Button:
                text: "Pocetna"
                on_release: root.manager.current = "home"
            Button:
                text: "Kalkulator"
                on_release: root.manager.current = "kalkulator"
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
        canvas.before:
            Rectangle:
                source: app.background_img
                pos: self.pos
                size: self.size

        TitleLabel:
            text: "Izvestaj zarade"

        NavBar:
            Button:
                text: "Pocetna"
                on_release: root.manager.current = "home"
            Button:
                text: "Kalkulator"
                on_release: root.manager.current = "kalkulator"
            Button:
                text: "Evidencija"
                on_release: root.manager.current = "evidencija"

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
                color: 0.1, 0.1, 0.1, 1

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
                color: 0.1, 0.1, 0.1, 1

        Widget:

<PodesavanjaScreen>:
    name: "podesavanja"
    BoxLayout:
        orientation: "vertical"
        padding: dp(16)
        spacing: dp(14)
        canvas.before:
            Rectangle:
                source: app.background_img
                pos: self.pos
                size: self.size

        TitleLabel:
            text: "Podesavanja"
            font_size: '24sp'

        NavBar:
            Button:
                text: "Pocetna"
                on_release: root.manager.current = "home"

        ScrollView:
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)

                MenuButton:
                    icon_src: "assets/icons/earnings_chart.png"
                    tekst: "Grafik zarade"
                    on_release: app.root.current = "grafik"

                MenuButton:
                    icon_src: "assets/icons/navigation.png"
                    tekst: "Navigacija"
                    on_release: app.root.current = "navigacija"

                MenuButton:
                    icon_src: "assets/icons/night_tariff.png"
                    tekst: "Nocna tarifa"
                    on_release: app.root.current = "nocna_tarifa"

                MenuButton:
                    icon_src: "assets/icons/service.png"
                    tekst: "Servis vozila"
                    on_release: app.root.current = "servis"

                MenuButton:
                    icon_src: "assets/icons/fuel.png"
                    tekst: "Gorivo"
                    on_release: app.root.current = "gorivo"

                MenuButton:
                    icon_src: "assets/icons/weekly_report.png"
                    tekst: "Nedeljni izvestaj"
                    on_release: app.root.current = "izvestaj"

                MenuButton:
                    icon_src: "assets/icons/monthly_report.png"
                    tekst: "Mesecni izvestaj"
                    on_release: app.root.current = "izvestaj"

<PlaceholderScreen>:
    naslov: ""
    BoxLayout:
        orientation: "vertical"
        padding: dp(16)
        spacing: dp(14)
        canvas.before:
            Rectangle:
                source: app.background_img
                pos: self.pos
                size: self.size

        TitleLabel:
            text: root.naslov

        NavBar:
            Button:
                text: "Pocetna"
                on_release: root.manager.current = "home"
            Button:
                text: "Podesavanja"
                on_release: root.manager.current = "podesavanja"

        Label:
            text: "Uskoro..."
            font_size: '18sp'
            color: 1, 1, 1, 1
"""


class MenuButton(ButtonBehavior, BoxLayout):
    icon_src = StringProperty("")
    tekst = StringProperty("")


class HomeScreen(Screen):
    pass


class PodesavanjaScreen(Screen):
    pass


class PlaceholderScreen(Screen):
    naslov = StringProperty("")


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
                color=(1, 1, 1, 1),
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
            color=(1, 1, 1, 1),
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


def _crash_log_path():
    try:
        from kivy.app import App
        base = App.get_running_app().user_data_dir if App.get_running_app() else "."
    except Exception:
        base = "."
    return os.path.join(base, "crash_log.txt")


def _zapisi_gresku(tekst):
    try:
        with open(_crash_log_path(), "w", encoding="utf-8") as f:
            f.write(tekst)
    except Exception:
        pass


def _prikazi_gresku_ekran(poruka):
    """Vraca prost Kivy ekran koji ispisuje gresku umesto da app pukne bez traga."""
    sv = ScrollView()
    lbl = Label(
        text=(
            "GRESKA PRI POKRETANJU APLIKACIJE\n"
            "Posalji ovaj tekst da se ispravi:\n\n" + poruka
        ),
        markup=False,
        size_hint_y=None,
        text_size=(None, None),
        color=(1, 1, 1, 1),
        padding=(20, 20),
    )
    lbl.bind(texture_size=lambda inst, val: setattr(lbl, "size", val))
    lbl.bind(width=lambda inst, val: setattr(lbl, "text_size", (val - 40, None)))
    sv.add_widget(lbl)
    root = BoxLayout()
    root.add_widget(sv)
    return root


class TaksiApp(App):
    background_img = StringProperty(BACKGROUND_IMG)

    def build(self):
        # Globalni hvatac neuhvacenih gresaka posle pokretanja (npr. u dugmadima)
        sys.excepthook = self._globalna_greska

        self.title = "Taksi App"
        try:
            db.init_db()
            return Builder.load_string(KV)
        except Exception:
            greska = traceback.format_exc()
            _zapisi_gresku(greska)
            return _prikazi_gresku_ekran(greska)

    def _globalna_greska(self, exc_type, exc_value, exc_tb):
        greska = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        _zapisi_gresku(greska)
        try:
            popup = Popup(
                title="Greska u aplikaciji",
                content=Label(text=greska[-1500:], color=(1, 1, 1, 1)),
                size_hint=(0.95, 0.8),
            )
            popup.open()
        except Exception:
            pass


if __name__ == "__main__":
    TaksiApp().run()
