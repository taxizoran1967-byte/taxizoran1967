"""
ekran_servis.py
Evidencija servisa vozila + podsetnik za sledeci servis na osnovu
kilometraze (SERVIS_PODSETNIK, potpuno samostalno u ovom fajlu).

Izdvojeno iz main.py - isti obrazac kao grafik_zarade.py.
"""

import os
import json
from datetime import datetime

from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.properties import StringProperty, ListProperty
from kivy.app import App


# ============================================================
# main.py ovo postavlja posle uvoza (izbegava kruzni import)
# ============================================================

_SERVIS_REF = None         # main._SERVIS_REF
_GORIVO_REF = None         # main._GORIVO_REF (za podsetnik - km sa pumpe)
_FORMATIRAJ_CENU = None    # main.formatiraj_cenu
_NAPRAVI_RED_LISTE = None  # main.napravi_red_liste
_PRIKAZI_POPUP = None      # main._prikazi_popup_poruku


def poveži(servis_obj, gorivo_obj, formatiraj_cenu_fn, napravi_red_liste_fn, prikazi_popup_fn):
    """main.py poziva ovo jednom, odmah posle 'import ekran_servis'."""
    global _SERVIS_REF, _GORIVO_REF, _FORMATIRAJ_CENU, _NAPRAVI_RED_LISTE, _PRIKAZI_POPUP
    _SERVIS_REF = servis_obj
    _GORIVO_REF = gorivo_obj
    _FORMATIRAJ_CENU = formatiraj_cenu_fn
    _NAPRAVI_RED_LISTE = napravi_red_liste_fn
    _PRIKAZI_POPUP = prikazi_popup_fn


class ServisPodsetnikPodesavanja:
    """Cuva podeseni interval (u km) za podsetnik o sledecem servisu -
    npr. 'svakih 10000 km'. Koristi se na ekranu Servis da upozori
    vozaca kad se priblizi ili predje taj interval od poslednjeg
    servisa sa upisanom kilometrazom."""

    def __init__(self):
        self.interval_km = 10000

    def _putanja(self, user_data_dir):
        return os.path.join(user_data_dir, "servis_podsetnik.json")

    def ucitaj(self, user_data_dir):
        try:
            with open(self._putanja(user_data_dir), "r", encoding="utf-8") as f:
                podaci = json.load(f)
            self.interval_km = podaci.get("interval_km", 10000)
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            pass

    def sacuvaj(self, user_data_dir):
        podaci = {"interval_km": self.interval_km}
        with open(self._putanja(user_data_dir), "w", encoding="utf-8") as f:
            json.dump(podaci, f, ensure_ascii=False, indent=2)


SERVIS_PODSETNIK = ServisPodsetnikPodesavanja()


SERVIS_PODSETNIK = ServisPodsetnikPodesavanja()

def _izracunaj_stanje_servisa():
    """Vraca recnik sa stanjem podsetnika za servis, na osnovu
    poslednjeg servisa koji ima upisanu kilometrazu (_SERVIS_REF.stavke) i
    najnovije kilometraze sa pumpe (_GORIVO_REF.stavke, km_pumpe) kao
    priblizne trenutne kilometraze vozila. Vraca None ako nema
    dovoljno podataka (nijedan servis sa km, ili nijedno gorivo sa
    upisanom km na pumpi)."""
    servisi_sa_km = [s for s in _SERVIS_REF.stavke if s.get("km")]
    if not servisi_sa_km:
        return None
    poslednji_servis = max(servisi_sa_km, key=lambda s: s["km"])

    gorivo_sa_km = [g for g in _GORIVO_REF.stavke if g.get("km_pumpe")]
    if not gorivo_sa_km:
        return None
    trenutna_km = max(g["km_pumpe"] for g in gorivo_sa_km)

    interval = SERVIS_PODSETNIK.interval_km
    predjeno = trenutna_km - poslednji_servis["km"]
    preostalo = interval - predjeno

    return {
        "poslednji_servis": poslednji_servis,
        "trenutna_km": trenutna_km,
        "predjeno": predjeno,
        "interval": interval,
        "preostalo": preostalo,
    }


class ServisScreen(Screen):
    tekst_ukupno = StringProperty("Ukupno na servisima: 0 RSD")
    dugme_tekst = StringProperty("Sacuvaj servis")
    tekst_podsetnik = StringProperty("")
    boja_podsetnik = ListProperty([0.35, 0.35, 0.45, 0.92])
    izmena_id = None

    def on_pre_enter(self, *args):
        self.ucitaj_servis()
        self._osvezi_podsetnik()
        self.ids.input_interval_servis.text = f"{SERVIS_PODSETNIK.interval_km:g}"

    def _osvezi_podsetnik(self):
        stanje = _izracunaj_stanje_servisa()

        if stanje is None:
            self.tekst_podsetnik = (
                "Podsetnik za servis: nema jos dovoljno podataka.\n"
                "Potreban je bar jedan uneti servis SA kilometrazom, i "
                "bar jedno sipanje goriva sa upisanom kilometrazom sa pumpe."
            )
            self.boja_podsetnik = [0.35, 0.35, 0.45, 0.92]
            return

        poslednji = stanje["poslednji_servis"]
        predjeno = stanje["predjeno"]
        preostalo = stanje["preostalo"]
        interval = stanje["interval"]

        osnova = (
            f"Poslednji servis: {poslednji.get('vrsta', '-')} na {poslednji['km']:g} km"
            f" ({poslednji.get('datum', '-')})\n"
            f"Trenutna kilometraza (iz goriva): {stanje['trenutna_km']:g} km\n"
            f"Predjeno od servisa: {predjeno:g} km (interval: {interval:g} km)\n"
        )

        if preostalo <= 0:
            self.tekst_podsetnik = osnova + f"VREME JE ZA _SERVIS_REF! Predjeno {abs(preostalo):g} km preko intervala."
            self.boja_podsetnik = [0.62, 0.24, 0.24, 0.95]
        elif interval > 0 and preostalo <= interval * 0.2:
            self.tekst_podsetnik = osnova + f"Uskoro treba servis - jos {preostalo:g} km."
            self.boja_podsetnik = [0.60, 0.48, 0.16, 0.95]
        else:
            self.tekst_podsetnik = osnova + f"Sve OK - jos {preostalo:g} km do sledeceg servisa."
            self.boja_podsetnik = [0.24, 0.46, 0.30, 0.95]

    def sacuvaj_interval(self):
        try:
            novi_interval = float(self.ids.input_interval_servis.text.replace(",", "."))
            if novi_interval <= 0:
                raise ValueError
        except (ValueError, AttributeError):
            _PRIKAZI_POPUP(
                "Greska", "Unesi ispravan broj kilometara (vece od 0).", size_hint=(0.85, 0.35)
            )
            return

        app = App.get_running_app()
        SERVIS_PODSETNIK.interval_km = novi_interval
        SERVIS_PODSETNIK.sacuvaj(app.user_data_dir)
        self._osvezi_podsetnik()
        _PRIKAZI_POPUP(
            "Sacuvano", f"Interval za podsetnik je sad {novi_interval:g} km.", size_hint=(0.85, 0.3)
        )

    def ucitaj_servis(self):
        kontejner = self.ids.lista_servis
        kontejner.clear_widgets()

        ukupno = sum(s.get("cena", 0) for s in _SERVIS_REF.stavke)
        self.tekst_ukupno = f"Ukupno na servisima: {_FORMATIRAJ_CENU(ukupno)}"

        if not _SERVIS_REF.stavke:
            kontejner.add_widget(Label(
                text="Jos uvek nema unosa servisa.",
                size_hint_y=None, height=40,
                color=(1, 1, 1, 1),
            ))
            return

        for s in _SERVIS_REF.stavke:
            kontejner.add_widget(self._napravi_red(s))

    def _napravi_red(self, s):
        km = s.get("km")
        km_deo = f"  |  {km:g} km" if km else ""
        napomena = s.get("napomena") or "-"
        opis = (
            f"[b]{s.get('datum', '-')}[/b]\n"
            f"{s.get('vrsta', '-')}{km_deo}\n"
            f"{napomena}\n"
            f"[color=3a2570][b]{_FORMATIRAJ_CENU(s.get('cena', 0))}[/b][/color]"
        )
        return _NAPRAVI_RED_LISTE(
            opis,
            tint=(0.38, 0.32, 0.52, 0.92),
            boja_teksta=(0.93, 0.90, 1, 1),
            dugmad=[
                ("Izmeni", (0.36, 0.46, 0.64, 1), (0.95, 0.96, 1, 1),
                 lambda inst, sid=s["id"]: self._izmeni(sid)),
                ("Obrisi", (0.66, 0.30, 0.34, 1), (1, 0.95, 0.95, 1),
                 lambda inst, sid=s["id"]: self._obrisi(sid)),
            ],
        )

    def _izmeni(self, stavka_id):
        s = _SERVIS_REF.nadji(stavka_id)
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
            _SERVIS_REF.azuriraj(app.user_data_dir, self.izmena_id, stavka)
            self.izmena_id = None
            self.dugme_tekst = "Sacuvaj servis"
            self._poruka("Izmena sacuvana.")
        else:
            _SERVIS_REF.dodaj(app.user_data_dir, stavka)
            self._poruka("Servis sacuvan.")

        self.ids.input_vrsta.text = ""
        self.ids.input_cena_servisa.text = ""
        self.ids.input_km_servis.text = ""
        self.ids.input_napomena_servis.text = ""

        self.ucitaj_servis()
        self._osvezi_podsetnik()

    def _obrisi(self, stavka_id):
        app = App.get_running_app()
        _SERVIS_REF.obrisi(app.user_data_dir, stavka_id)
        if self.izmena_id == stavka_id:
            self.izmena_id = None
            self.dugme_tekst = "Sacuvaj servis"
        self.ucitaj_servis()
        self._osvezi_podsetnik()

    def _poruka(self, tekst):
        _PRIKAZI_POPUP("Info", tekst, size_hint=(0.8, 0.3))

SERVIS_KV = """
# ============================================================
# _SERVIS_REF VOZILA
# ============================================================

<ServisScreen>:
    name: "servis"
    ScreenRoot:

        TitleLabel:
            text: "Servis vozila"

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
                    tint: root.boja_podsetnik
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(12)
                    orientation: "vertical"
                    Label:
                        id: label_podsetnik
                        text: root.tekst_podsetnik
                        font_size: '13sp'
                        color: 1, 1, 1, 1
                        halign: "left"
                        valign: "top"
                        size_hint_y: None
                        text_size: self.width, None
                        height: self.texture_size[1]

                FieldLabel:
                    text: "Interval za podsetnik (km izmedju servisa)"

                BoxLayout:
                    size_hint_y: None
                    height: dp(48)
                    spacing: dp(8)
                    PastelTextInput:
                        id: input_interval_servis
                        hint_text: "npr. 10000"
                        input_filter: "float"
                    RoundButton:
                        label_text: "Sacuvaj"
                        tint: 0.36, 0.46, 0.64, 1
                        text_color: 1, 1, 1, 1
                        size_hint_x: None
                        width: dp(100)
                        on_release: root.sacuvaj_interval()

                PastelCard:
                    tint: 0.38, 0.32, 0.52, 0.92
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(12)
                    Label:
                        id: label_ukupno_servis
                        text: root.tekst_ukupno
                        font_size: '15sp'
                        bold: True
                        color: 0.92, 0.88, 1, 1
                        halign: "left"
                        valign: "middle"
                        size_hint_y: None
                        text_size: self.width, None
                        height: self.texture_size[1]

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
                    tint: 0.30, 0.52, 0.36, 1
                    text_color: 0.92, 1, 0.94, 1
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


"""
