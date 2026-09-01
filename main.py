"""
Taksi App - licna aplikacija za taksistu
Kalkulator cene, evidencija voznji, dnevni/mesecni izvestaj zarade.
"""

import os
import sys
import json
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
# TARIFE (iste kao u Telegram botu) - podrazumevane vrednosti
# Stvarne, trenutno vazece cene se cuvaju u cene.json i mogu
# se menjati direktno u aplikaciji (Podesavanja -> Cene / Tarife).
# ========================
DEFAULT_TARIFE = {
    "Osnovna (07-22h)": 80,
    "Nocna (22-07h)": 100,
    "Vikend": 90,
    "Aerodromski transfer": 120,
}
DEFAULT_START_FEE = 200


class CenePodesavanja:
    """Drzi trenutno vazece cene tarifa, start taksu i status nocne
    tarife, cuva ih u cene.json unutar interne memorije aplikacije."""

    def __init__(self):
        self.tarife = dict(DEFAULT_TARIFE)
        self.start_fee = DEFAULT_START_FEE
        self.nocna_aktivna = False

    def _putanja(self, user_data_dir):
        return os.path.join(user_data_dir, "cene.json")

    def ucitaj(self, user_data_dir):
        putanja = self._putanja(user_data_dir)
        try:
            with open(putanja, "r", encoding="utf-8") as f:
                podaci = json.load(f)
            ucitane_tarife = podaci.get("tarife", {})
            for naziv in self.tarife:
                if naziv in ucitane_tarife:
                    self.tarife[naziv] = float(ucitane_tarife[naziv])
            self.start_fee = float(podaci.get("start_fee", DEFAULT_START_FEE))
            self.nocna_aktivna = bool(podaci.get("nocna_aktivna", False))
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            pass

    def sacuvaj(self, user_data_dir):
        putanja = self._putanja(user_data_dir)
        podaci = {
            "tarife": self.tarife,
            "start_fee": self.start_fee,
            "nocna_aktivna": self.nocna_aktivna,
        }
        with open(putanja, "w", encoding="utf-8") as f:
            json.dump(podaci, f, ensure_ascii=False, indent=2)


class JsonLog:
    """Jednostavna lista stavki (npr. unosi goriva ili servisa) koja
    se cuva u sopstvenom .json fajlu - odvojeno od baze i od cena,
    tako da ne moze doci u sukob sa ostalim delovima aplikacije."""

    def __init__(self, filename):
        self.filename = filename
        self.stavke = []

    def _putanja(self, user_data_dir):
        return os.path.join(user_data_dir, self.filename)

    def ucitaj(self, user_data_dir):
        try:
            with open(self._putanja(user_data_dir), "r", encoding="utf-8") as f:
                self.stavke = json.load(f)
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            self.stavke = []

    def sacuvaj(self, user_data_dir):
        with open(self._putanja(user_data_dir), "w", encoding="utf-8") as f:
            json.dump(self.stavke, f, ensure_ascii=False, indent=2)

    def dodaj(self, user_data_dir, stavka):
        novi_id = max((s["id"] for s in self.stavke), default=0) + 1
        stavka["id"] = novi_id
        self.stavke.insert(0, stavka)
        self.sacuvaj(user_data_dir)
        return novi_id

    def azuriraj(self, user_data_dir, stavka_id, nova_stavka):
        nova_stavka["id"] = stavka_id
        for i, s in enumerate(self.stavke):
            if s["id"] == stavka_id:
                self.stavke[i] = nova_stavka
                break
        self.sacuvaj(user_data_dir)

    def nadji(self, stavka_id):
        for s in self.stavke:
            if s["id"] == stavka_id:
                return s
        return None

    def obrisi(self, user_data_dir, stavka_id):
        self.stavke = [s for s in self.stavke if s["id"] != stavka_id]
        self.sacuvaj(user_data_dir)


CENE = CenePodesavanja()
GORIVO = JsonLog("gorivo.json")
SERVIS = JsonLog("servis.json")

# Kad korisnik klikne "Izmeni" na voznji u Evidenciji, podaci te
# voznje se privremeno stave ovde da bi ih Kalkulator ekran
# pokupio i popunio formu za ispravku.
EDIT_VOZNJA = None


BACKGROUND_IMG = "assets/backgrounds/background.png"

KV = """
#:import dp kivy.metrics.dp

ScreenManager:
    HomeScreen:
    KalkulatorScreen:
    EvidencijaScreen:
    IzvestajScreen:
    PodesavanjaScreen:
    CenovnikScreen:
    NocnaTarifaScreen:
    GorivoScreen:
    ServisScreen:
    PlaceholderScreen:
        name: "grafik"
        naslov: "Grafik zarade"
    PlaceholderScreen:
        name: "navigacija"
        naslov: "Navigacija"
    PlaceholderScreen:
        name: "profil"
        naslov: "Profil vozaca"
    PlaceholderScreen:
        name: "poziv"
        naslov: "Poziv / Dispecer"

# ============================================================
# ZAJEDNICKI STIL - pastelne kartice, zaobljeni uglovi, tipografija
# ============================================================

<ScreenRoot@BoxLayout>:
    orientation: "vertical"
    padding: dp(18)
    spacing: dp(16)
    canvas.before:
        Rectangle:
            source: app.background_img
            pos: self.pos
            size: self.size
        Color:
            rgba: 0.04, 0.03, 0.09, 0.35
        Rectangle:
            pos: self.pos
            size: self.size

<TitleLabel@Label>:
    size_hint_y: None
    height: dp(42)
    font_size: '24sp'
    bold: True
    color: 1, 1, 1, 1
    halign: "left"
    text_size: self.size
    valign: "middle"

<FieldLabel@Label>:
    size_hint_y: None
    height: dp(22)
    halign: "left"
    valign: "middle"
    text_size: self.size
    font_size: '14sp'
    color: 0.85, 0.85, 0.95, 1

<PastelCard@BoxLayout>:
    tint: (0.97, 0.96, 1, 0.94)
    canvas.before:
        Color:
            rgba: 0, 0, 0, 0.14
        RoundedRectangle:
            pos: self.x, self.y - dp(3)
            size: self.size
            radius: [dp(20)]
        Color:
            rgba: root.tint
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(20)]

<RoundButton@ButtonBehavior+BoxLayout>:
    tint: (0.80, 0.87, 1, 1)
    text_color: 0.12, 0.14, 0.30, 1
    label_text: ""
    canvas.before:
        Color:
            rgba: root.tint
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(16)]
    Label:
        text: root.label_text
        color: root.text_color
        bold: True
        font_size: '15sp'

<NavBar@BoxLayout>:
    size_hint_y: None
    height: dp(46)
    spacing: dp(10)

<MenuButton>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(72)
    spacing: dp(16)
    padding: dp(12)
    canvas.before:
        Color:
            rgba: 0, 0, 0, 0.16
        RoundedRectangle:
            pos: self.x, self.y - dp(3)
            size: self.size
            radius: [dp(22)]
        Color:
            rgba: 0.96, 0.95, 1, 0.90
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(22)]
    BoxLayout:
        size_hint_x: None
        width: dp(48)
        canvas.before:
            StencilPush
            Ellipse:
                pos: self.pos
                size: self.size
            StencilUse
        canvas.after:
            StencilUnUse
            Ellipse:
                pos: self.pos
                size: self.size
            StencilPop
        Image:
            source: root.icon_src
            allow_stretch: True
            keep_ratio: False
    Label:
        text: root.tekst
        font_size: '17sp'
        bold: True
        color: 0.14, 0.14, 0.28, 1
        halign: "left"
        valign: "middle"
        text_size: self.size

<PastelTextInput@TextInput>:
    background_color: 0.97, 0.97, 1, 0.95
    foreground_color: 0.12, 0.12, 0.22, 1
    hint_text_color: 0.55, 0.55, 0.65, 1
    cursor_color: 0.3, 0.3, 0.7, 1
    padding: dp(14), dp(12)
    size_hint_y: None
    height: dp(48)
    multiline: False

# ============================================================
# POCETNI EKRAN
# ============================================================

<HomeScreen>:
    name: "home"
    ScreenRoot:

        TitleLabel:
            text: "Taksi App"
            font_size: '28sp'
            height: dp(48)

        ScrollView:
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(14)
                padding: dp(2), dp(4)

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
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Evidencija"
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "evidencija"
            RoundButton:
                label_text: "Izvestaj"
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "izvestaj"

        ScrollView:
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
                    background_color: 0.90, 0.93, 1, 1
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
                    tint: 0.87, 0.97, 0.88, 0.95
                    size_hint_y: None
                    height: dp(96)
                    padding: dp(14)
                    Label:
                        id: label_cena
                        text: root.tekst_cene
                        font_size: '20sp'
                        bold: True
                        color: 0.08, 0.35, 0.12, 1
                        halign: "center"
                        valign: "middle"
                        text_size: self.size

                RoundButton:
                    label_text: root.dugme_tekst
                    tint: 0.70, 0.90, 0.72, 1
                    text_color: 0.06, 0.28, 0.10, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.sacuvaj_voznju()

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
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Kalkulator"
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "kalkulator"
            RoundButton:
                label_text: "Izvestaj"
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "izvestaj"

        ScrollView:
            BoxLayout:
                id: lista_voznji
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(10)
                padding: dp(4)

# ============================================================
# IZVESTAJ
# ============================================================

<IzvestajScreen>:
    name: "izvestaj"
    ScreenRoot:

        TitleLabel:
            text: "Izvestaj zarade"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Kalkulator"
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "kalkulator"
            RoundButton:
                label_text: "Evidencija"
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "evidencija"

        PastelCard:
            tint: 1, 0.93, 0.86, 0.95
            size_hint_y: None
            height: dp(128)
            padding: dp(14)
            Label:
                id: label_danas
                text: root.tekst_danas
                font_size: '16sp'
                halign: "left"
                valign: "top"
                text_size: self.size
                color: 0.30, 0.16, 0.05, 1

        PastelCard:
            tint: 0.90, 0.87, 1, 0.95
            size_hint_y: None
            height: dp(128)
            padding: dp(14)
            Label:
                id: label_mesec
                text: root.tekst_mesec
                font_size: '16sp'
                halign: "left"
                valign: "top"
                text_size: self.size
                color: 0.20, 0.14, 0.35, 1

        Widget:

# ============================================================
# PODESAVANJA
# ============================================================

<PodesavanjaScreen>:
    name: "podesavanja"
    ScreenRoot:

        TitleLabel:
            text: "Podesavanja"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "home"

        ScrollView:
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(14)
                padding: dp(2), dp(4)

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

                MenuButton:
                    icon_src: "assets/icons/calculator.png"
                    tekst: "Kalkulator"
                    on_release: app.root.current = "kalkulator"

                MenuButton:
                    icon_src: "assets/icons/profil.png"
                    tekst: "Profil vozaca"
                    on_release: app.root.current = "profil"

                MenuButton:
                    icon_src: "assets/icons/poziv.png"
                    tekst: "Poziv / Dispecer"
                    on_release: app.root.current = "poziv"

                MenuButton:
                    icon_src: "assets/icons/settings.png"
                    tekst: "Cene / Tarife"
                    on_release: app.root.current = "cene"

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
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Podesavanja"
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "podesavanja"

        ScrollView:
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
                    tint: 0.70, 0.90, 0.72, 1
                    text_color: 0.06, 0.28, 0.10, 1
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
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Podesavanja"
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "podesavanja"

        PastelCard:
            tint: 0.90, 0.87, 1, 0.95
            size_hint_y: None
            height: dp(74)
            padding: dp(14)
            Label:
                id: label_status
                text: root.tekst_status
                font_size: '18sp'
                bold: True
                color: 0.18, 0.12, 0.35, 1

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

# ============================================================
# GORIVO
# ============================================================

<GorivoScreen>:
    name: "gorivo"
    ScreenRoot:

        TitleLabel:
            text: "Gorivo"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Podesavanja"
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "podesavanja"

        ScrollView:
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: dp(4)

                PastelCard:
                    tint: 1, 0.93, 0.86, 0.95
                    size_hint_y: None
                    height: dp(72)
                    padding: dp(12)
                    Label:
                        id: label_ukupno_gorivo
                        text: root.tekst_ukupno
                        font_size: '14sp'
                        bold: True
                        color: 0.30, 0.16, 0.05, 1

                FieldLabel:
                    text: "Vrsta goriva"

                Spinner:
                    id: spinner_tip_goriva
                    text: "Benzin"
                    values: ["Benzin", "TNG"]
                    size_hint_y: None
                    height: dp(48)
                    background_color: 0.90, 0.93, 1, 1
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
                    text: "Napomena (opciono)"

                PastelTextInput:
                    id: input_napomena_gorivo
                    hint_text: "npr. NIS pumpa"

                RoundButton:
                    label_text: root.dugme_tekst
                    tint: 0.70, 0.90, 0.72, 1
                    text_color: 0.06, 0.28, 0.10, 1
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

# ============================================================
# SERVIS VOZILA
# ============================================================

<ServisScreen>:
    name: "servis"
    ScreenRoot:

        TitleLabel:
            text: "Servis vozila"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Podesavanja"
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "podesavanja"

        ScrollView:
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: dp(4)

                PastelCard:
                    tint: 0.90, 0.87, 1, 0.95
                    size_hint_y: None
                    height: dp(56)
                    padding: dp(12)
                    Label:
                        id: label_ukupno_servis
                        text: root.tekst_ukupno
                        font_size: '15sp'
                        bold: True
                        color: 0.20, 0.14, 0.35, 1

                FieldLabel:
                    text: "Vrsta servisa"

                PastelTextInput:
                    id: input_vrsta
                    hint_text: "npr. zamena ulja"

                FieldLabel:
                    text: "Cena (RSD)"

                PastelTextInput:
                    id: input_cena_servisa
                    hint_text: "npr. 4500"
                    input_filter: "float"

                FieldLabel:
                    text: "Kilometraza (opciono)"

                PastelTextInput:
                    id: input_km_servis
                    hint_text: "npr. 152340"
                    input_filter: "float"

                FieldLabel:
                    text: "Napomena (opciono)"

                PastelTextInput:
                    id: input_napomena_servis
                    hint_text: "npr. ime servisa"

                RoundButton:
                    label_text: root.dugme_tekst
                    tint: 0.70, 0.90, 0.72, 1
                    text_color: 0.06, 0.28, 0.10, 1
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.sacuvaj_servis()

                BoxLayout:
                    id: lista_servis
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(10)
                    padding: dp(4), dp(10)

# ============================================================
# PLACEHOLDER ("Uskoro")
# ============================================================

<PlaceholderScreen>:
    naslov: ""
    ScreenRoot:

        TitleLabel:
            text: root.naslov

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Podesavanja"
                tint: 0.86, 0.90, 1, 1
                on_release: root.manager.current = "podesavanja"

        PastelCard:
            tint: 0.95, 0.95, 1, 0.9
            size_hint_y: None
            height: dp(70)
            padding: dp(14)
            Label:
                text: "Uskoro..."
                font_size: '17sp'
                bold: True
                color: 0.2, 0.2, 0.3, 1

        Widget:
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


class CenovnikScreen(Screen):
    def on_pre_enter(self, *args):
        self.ids.input_start.text = f"{CENE.start_fee:g}"
        self.ids.input_osnovna.text = f"{CENE.tarife['Osnovna (07-22h)']:g}"
        self.ids.input_nocna.text = f"{CENE.tarife['Nocna (22-07h)']:g}"
        self.ids.input_vikend.text = f"{CENE.tarife['Vikend']:g}"
        self.ids.input_aerodromski.text = f"{CENE.tarife['Aerodromski transfer']:g}"

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

        CENE.start_fee = start
        CENE.tarife["Osnovna (07-22h)"] = osnovna
        CENE.tarife["Nocna (22-07h)"] = nocna
        CENE.tarife["Vikend"] = vikend
        CENE.tarife["Aerodromski transfer"] = aerodromski

        app = App.get_running_app()
        CENE.sacuvaj(app.user_data_dir)

        self._poruka("Cene su sacuvane.")

    def _poruka(self, tekst):
        popup = Popup(
            title="Info",
            content=Label(text=tekst),
            size_hint=(0.8, 0.3),
        )
        popup.open()


class NocnaTarifaScreen(Screen):
    tekst_status = StringProperty("")
    tekst_dugme = StringProperty("")
    tint_dugme = (0.7, 0.9, 0.72, 1)

    def on_pre_enter(self, *args):
        self._osvezi()

    def _osvezi(self):
        if CENE.nocna_aktivna:
            self.tekst_status = "Nocna tarifa: UKLJUCENA"
            self.tekst_dugme = "Iskljuci nocnu tarifu"
            self.tint_dugme = (0.96, 0.78, 0.80, 1)
        else:
            self.tekst_status = "Nocna tarifa: ISKLJUCENA"
            self.tekst_dugme = "Ukljuci nocnu tarifu"
            self.tint_dugme = (0.70, 0.90, 0.72, 1)

    def promeni(self):
        CENE.nocna_aktivna = not CENE.nocna_aktivna
        app = App.get_running_app()
        CENE.sacuvaj(app.user_data_dir)
        self._osvezi()


class GorivoScreen(Screen):
    tekst_ukupno = StringProperty("Ukupno potroseno: 0 RSD")
    dugme_tekst = StringProperty("Sacuvaj unos")
    izmena_id = None

    def on_pre_enter(self, *args):
        self.ucitaj_gorivo()

    def ucitaj_gorivo(self):
        kontejner = self.ids.lista_gorivo
        kontejner.clear_widgets()

        ukupno = sum(s.get("cena", 0) for s in GORIVO.stavke)
        ukupno_benzin = sum(
            s.get("cena", 0) for s in GORIVO.stavke if s.get("tip") == "Benzin"
        )
        ukupno_tng = sum(
            s.get("cena", 0) for s in GORIVO.stavke if s.get("tip") == "TNG"
        )
        self.tekst_ukupno = (
            f"Ukupno: {ukupno:.0f} RSD\n"
            f"Benzin: {ukupno_benzin:.0f} RSD   |   TNG: {ukupno_tng:.0f} RSD"
        )

        if not GORIVO.stavke:
            kontejner.add_widget(Label(
                text="Jos uvek nema unosa goriva.",
                size_hint_y=None, height=40,
                color=(1, 1, 1, 1),
            ))
            return

        for s in GORIVO.stavke:
            kontejner.add_widget(self._napravi_red(s))

    def _napravi_red(self, s):
        from kivy.factory import Factory
        from kivy.metrics import dp

        napomena = s.get("napomena") or "-"
        tip = s.get("tip", "Benzin")
        opis = (
            f"[b]{s.get('datum', '-')}[/b]  |  {tip}  |  {s.get('litara', 0):g} l\n"
            f"{napomena}\n"
            f"[color=6b3d0d][b]{s.get('cena', 0):.0f} RSD[/b][/color]"
        )
        red = Factory.PastelCard(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(84),
            padding=dp(12),
            spacing=dp(6),
            tint=(1, 0.95, 0.90, 0.92),
        )
        red.add_widget(Label(
            text=opis, markup=True, halign="left", valign="middle",
            text_size=(None, None),
            color=(0.20, 0.14, 0.06, 1),
        ))
        izmeni_dugme = Factory.RoundButton(
            label_text="Izmeni",
            tint=(0.80, 0.87, 1, 1),
            text_color=(0.10, 0.14, 0.30, 1),
            size_hint_x=None,
            width=dp(76),
        )
        izmeni_dugme.bind(on_release=lambda inst, sid=s["id"]: self._izmeni(sid))
        red.add_widget(izmeni_dugme)
        obrisi_dugme = Factory.RoundButton(
            label_text="Obrisi",
            tint=(0.96, 0.78, 0.80, 1),
            text_color=(0.35, 0.05, 0.08, 1),
            size_hint_x=None,
            width=dp(76),
        )
        obrisi_dugme.bind(on_release=lambda inst, sid=s["id"]: self._obrisi(sid))
        red.add_widget(obrisi_dugme)
        return red

    def _izmeni(self, stavka_id):
        s = GORIVO.nadji(stavka_id)
        if not s:
            return
        self.izmena_id = stavka_id
        self.ids.input_litara.text = f"{s.get('litara', 0):g}"
        self.ids.input_cena_goriva.text = f"{s.get('cena', 0):g}"
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

        app = App.get_running_app()
        stavka = {
            "datum": datetime.now().strftime("%Y-%m-%d"),
            "tip": self.ids.spinner_tip_goriva.text,
            "litara": litara,
            "cena": cena,
            "napomena": self.ids.input_napomena_gorivo.text.strip(),
        }

        if self.izmena_id is not None:
            GORIVO.azuriraj(app.user_data_dir, self.izmena_id, stavka)
            self.izmena_id = None
            self.dugme_tekst = "Sacuvaj unos"
            self._poruka("Izmena sacuvana.")
        else:
            GORIVO.dodaj(app.user_data_dir, stavka)
            self._poruka("Unos sacuvan.")

        self.ids.input_litara.text = ""
        self.ids.input_cena_goriva.text = ""
        self.ids.input_napomena_gorivo.text = ""
        self.ids.spinner_tip_goriva.text = "Benzin"

        self.ucitaj_gorivo()

    def _obrisi(self, stavka_id):
        app = App.get_running_app()
        GORIVO.obrisi(app.user_data_dir, stavka_id)
        if self.izmena_id == stavka_id:
            self.izmena_id = None
            self.dugme_tekst = "Sacuvaj unos"
        self.ucitaj_gorivo()

    def _poruka(self, tekst):
        popup = Popup(
            title="Info",
            content=Label(text=tekst),
            size_hint=(0.8, 0.3),
        )
        popup.open()


class ServisScreen(Screen):
    tekst_ukupno = StringProperty("Ukupno na servisima: 0 RSD")
    dugme_tekst = StringProperty("Sacuvaj servis")
    izmena_id = None

    def on_pre_enter(self, *args):
        self.ucitaj_servis()

    def ucitaj_servis(self):
        kontejner = self.ids.lista_servis
        kontejner.clear_widgets()

        ukupno = sum(s.get("cena", 0) for s in SERVIS.stavke)
        self.tekst_ukupno = f"Ukupno na servisima: {ukupno:.0f} RSD"

        if not SERVIS.stavke:
            kontejner.add_widget(Label(
                text="Jos uvek nema unosa servisa.",
                size_hint_y=None, height=40,
                color=(1, 1, 1, 1),
            ))
            return

        for s in SERVIS.stavke:
            kontejner.add_widget(self._napravi_red(s))

    def _napravi_red(self, s):
        from kivy.factory import Factory
        from kivy.metrics import dp

        km = s.get("km")
        km_deo = f"  |  {km:g} km" if km else ""
        napomena = s.get("napomena") or "-"
        opis = (
            f"[b]{s.get('datum', '-')}[/b]  |  {s.get('vrsta', '-')}{km_deo}\n"
            f"{napomena}\n"
            f"[color=3a2570][b]{s.get('cena', 0):.0f} RSD[/b][/color]"
        )
        red = Factory.PastelCard(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(84),
            padding=dp(12),
            spacing=dp(6),
            tint=(0.93, 0.90, 1, 0.92),
        )
        red.add_widget(Label(
            text=opis, markup=True, halign="left", valign="middle",
            text_size=(None, None),
            color=(0.16, 0.12, 0.24, 1),
        ))
        izmeni_dugme = Factory.RoundButton(
            label_text="Izmeni",
            tint=(0.80, 0.87, 1, 1),
            text_color=(0.10, 0.14, 0.30, 1),
            size_hint_x=None,
            width=dp(76),
        )
        izmeni_dugme.bind(on_release=lambda inst, sid=s["id"]: self._izmeni(sid))
        red.add_widget(izmeni_dugme)
        obrisi_dugme = Factory.RoundButton(
            label_text="Obrisi",
            tint=(0.96, 0.78, 0.80, 1),
            text_color=(0.35, 0.05, 0.08, 1),
            size_hint_x=None,
            width=dp(76),
        )
        obrisi_dugme.bind(on_release=lambda inst, sid=s["id"]: self._obrisi(sid))
        red.add_widget(obrisi_dugme)
        return red

    def _izmeni(self, stavka_id):
        s = SERVIS.nadji(stavka_id)
        if not s:
            return
        self.izmena_id = stavka_id
        self.ids.input_vrsta.text = s.get("vrsta") or ""
        self.ids.input_cena_servisa.text = f"{s.get('cena', 0):g}"
        km = s.get("km")
        self.ids.input_km_servis.text = f"{km:g}" if km else ""
        self.ids.input_napomena_servis.text = s.get("napomena") or ""
        self.dugme_tekst = "Sacuvaj izmenu"

    def sacuvaj_servis(self):
        vrsta = self.ids.input_vrsta.text.strip()
        if not vrsta:
            self._poruka("Unesi vrstu servisa.")
            return
        try:
            cena = float(self.ids.input_cena_servisa.text.replace(",", "."))
        except (ValueError, AttributeError):
            self._poruka("Unesi ispravnu cenu servisa.")
            return

        km_tekst = self.ids.input_km_servis.text.strip()
        km = None
        if km_tekst:
            try:
                km = float(km_tekst.replace(",", "."))
            except ValueError:
                self._poruka("Kilometraza mora biti broj (ili ostavi prazno).")
                return

        app = App.get_running_app()
        stavka = {
            "datum": datetime.now().strftime("%Y-%m-%d"),
            "vrsta": vrsta,
            "cena": cena,
            "km": km,
            "napomena": self.ids.input_napomena_servis.text.strip(),
        }

        if self.izmena_id is not None:
            SERVIS.azuriraj(app.user_data_dir, self.izmena_id, stavka)
            self.izmena_id = None
            self.dugme_tekst = "Sacuvaj servis"
            self._poruka("Izmena sacuvana.")
        else:
            SERVIS.dodaj(app.user_data_dir, stavka)
            self._poruka("Servis sacuvan.")

        self.ids.input_vrsta.text = ""
        self.ids.input_cena_servisa.text = ""
        self.ids.input_km_servis.text = ""
        self.ids.input_napomena_servis.text = ""

        self.ucitaj_servis()

    def _obrisi(self, stavka_id):
        app = App.get_running_app()
        SERVIS.obrisi(app.user_data_dir, stavka_id)
        if self.izmena_id == stavka_id:
            self.izmena_id = None
            self.dugme_tekst = "Sacuvaj servis"
        self.ucitaj_servis()

    def _poruka(self, tekst):
        popup = Popup(
            title="Info",
            content=Label(text=tekst),
            size_hint=(0.8, 0.3),
        )
        popup.open()


class KalkulatorScreen(Screen):
    tekst_cene = StringProperty("Unesi kilometrazu da vidis cenu")
    dugme_tekst = StringProperty("Sacuvaj voznju")
    tarife_lista = list(DEFAULT_TARIFE.keys())
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
            if CENE.nocna_aktivna and "spinner_tarifa" in self.ids:
                self.ids.spinner_tarifa.text = "Nocna (22-07h)"
                self.izracunaj()

    def izracunaj(self):
        try:
            km = float(self.ids.input_km.text.replace(",", "."))
        except (ValueError, AttributeError):
            self.tekst_cene = "Unesi kilometrazu da vidis cenu"
            return
        tarifa_naziv = self.ids.spinner_tarifa.text
        cena_po_km = CENE.tarife.get(tarifa_naziv, CENE.tarife["Osnovna (07-22h)"])
        ukupno = CENE.start_fee + km * cena_po_km
        self.tekst_cene = (
            f"Cena: {ukupno:.0f} RSD\n"
            f"(start {CENE.start_fee:.0f} + {km:g} km x {cena_po_km:.0f} RSD)"
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
        cena_po_km = CENE.tarife.get(tarifa_naziv, CENE.tarife["Osnovna (07-22h)"])
        ukupno = CENE.start_fee + km * cena_po_km

        if self.editing_id is not None:
            db.obrisi_voznju(self.editing_id)

        db.dodaj_voznju(
            od_adresa=self.ids.input_od.text.strip(),
            do_adresa=self.ids.input_do.text.strip(),
            km=km,
            tarifa_naziv=tarifa_naziv,
            cena_po_km=cena_po_km,
            start_taksa=CENE.start_fee,
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
            self._poruka(f"Izmena sacuvana! Cena voznje: {ukupno:.0f} RSD")
        else:
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
        from kivy.factory import Factory
        from kivy.metrics import dp

        od = v["od_adresa"] or "-"
        do = v["do_adresa"] or "-"
        opis = (
            f"[b]{v['datum']} {v['vreme']}[/b]  |  {v['km']:g} km  |  "
            f"{v['tarifa_naziv']}\n{od} -> {do}\n"
            f"[color=0d6b1f][b]{v['ukupna_cena']:.0f} RSD[/b][/color]"
        )
        red = Factory.PastelCard(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(84),
            padding=dp(12),
            spacing=dp(8),
            tint=(0.96, 0.95, 1, 0.92),
        )
        red.add_widget(Label(
            text=opis, markup=True, halign="left", valign="middle",
            text_size=(None, None),
            color=(0.14, 0.14, 0.24, 1),
        ))
        obrisi_dugme = Factory.RoundButton(
            label_text="Obrisi",
            tint=(0.96, 0.78, 0.80, 1),
            text_color=(0.35, 0.05, 0.08, 1),
            size_hint_x=None,
            width=dp(76),
        )
        obrisi_dugme.bind(on_release=lambda inst, vid=v["id"]: self._obrisi(vid))
        izmeni_dugme = Factory.RoundButton(
            label_text="Izmeni",
            tint=(0.80, 0.87, 1, 1),
            text_color=(0.10, 0.14, 0.30, 1),
            size_hint_x=None,
            width=dp(76),
        )
        izmeni_dugme.bind(on_release=lambda inst, v=v: self._izmeni(v))
        red.add_widget(izmeni_dugme)
        red.add_widget(obrisi_dugme)
        return red

    def _izmeni(self, v):
        global EDIT_VOZNJA
        EDIT_VOZNJA = dict(v)
        self.manager.current = "kalkulator"

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
            CENE.ucitaj(self.user_data_dir)
            GORIVO.ucitaj(self.user_data_dir)
            SERVIS.ucitaj(self.user_data_dir)
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
