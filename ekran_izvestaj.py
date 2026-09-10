"""
ekran_izvestaj.py
Dnevni/nedeljni/mesecni pregled zarade, sa gorivom/servisima/ostalim
troskovima i neto zaradom za svaki period.

Izdvojeno iz main.py - isti obrazac kao grafik_zarade.py.
"""

from datetime import datetime, timedelta

from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.properties import StringProperty

import database as db


# ============================================================
# main.py ovo postavlja posle uvoza (izbegava kruzni import)
# ============================================================

_GORIVO_REF = None                     # main._GORIVO_REF
_SERVIS_REF = None                     # main._SERVIS_REF
_TROSKOVI_REF = None                   # main._TROSKOVI_REF
_STAVKE_IZMEDJU = None                 # main._stavke_izmedju
_IZRACUNAJ_POTROSNJU_INTERVALE = None  # main._izracunaj_potrosnju_intervale
_FORMATIRAJ_CENU = None                # main.formatiraj_cenu
_NAPRAVI_RED_LISTE = None              # main.napravi_red_liste


def poveži(gorivo_obj, servis_obj, troskovi_obj, stavke_izmedju_fn,
           potrosnju_intervale_fn, formatiraj_cenu_fn, napravi_red_liste_fn):
    """main.py poziva ovo jednom, odmah posle 'import ekran_izvestaj'."""
    global _GORIVO_REF, _SERVIS_REF, _TROSKOVI_REF
    global _STAVKE_IZMEDJU, _IZRACUNAJ_POTROSNJU_INTERVALE, _FORMATIRAJ_CENU, _NAPRAVI_RED_LISTE
    _GORIVO_REF = gorivo_obj
    _SERVIS_REF = servis_obj
    _TROSKOVI_REF = troskovi_obj
    _STAVKE_IZMEDJU = stavke_izmedju_fn
    _IZRACUNAJ_POTROSNJU_INTERVALE = potrosnju_intervale_fn
    _FORMATIRAJ_CENU = formatiraj_cenu_fn
    _NAPRAVI_RED_LISTE = napravi_red_liste_fn


class IzvestajScreen(Screen):
    tekst_danas = StringProperty("")
    tekst_nedelja = StringProperty("")
    tekst_mesec = StringProperty("")

    def on_pre_enter(self, *args):
        self.osvezi()

    def _dodatne_linije_perioda(self, pocetak, kraj, prihod):
        """Vraca gotov tekst (gorivo, servisi, ostali troskovi,
        potrosnja, neto zarada) za dati period - koristi se ispod
        osnovnih brojeva (broj voznji/km/zarada) na sve tri kartice
        (danas/nedelja/mesec)."""
        gorivo_p = _STAVKE_IZMEDJU(_GORIVO_REF.stavke, pocetak, kraj)
        servisi_p = _STAVKE_IZMEDJU(_SERVIS_REF.stavke, pocetak, kraj)
        troskovi_p = _STAVKE_IZMEDJU(_TROSKOVI_REF.stavke, pocetak, kraj)
        cena_gorivo = sum(s.get("cena", 0) for s in gorivo_p)
        litara_gorivo = sum(s.get("litara", 0) for s in gorivo_p)
        cena_servis = sum(s.get("cena", 0) for s in servisi_p)
        cena_troskovi = sum(s.get("cena", 0) for s in troskovi_p)

        intervali = [
            i for i in _IZRACUNAJ_POTROSNJU_INTERVALE(_GORIVO_REF.stavke)
            if pocetak <= i["datum"] <= kraj
        ]
        if intervali:
            ukupno_km_pot = sum(i["km_predjeno"] for i in intervali)
            ukupno_l_pot = sum(i["litara"] for i in intervali)
            potrosnja_txt = f"{(ukupno_l_pot / ukupno_km_pot * 100):.1f} l/100km" if ukupno_km_pot > 0 else "-"
        else:
            potrosnja_txt = "nema dovoljno podataka"

        neto = prihod - cena_gorivo - cena_servis - cena_troskovi

        return (
            f"Gorivo: {_FORMATIRAJ_CENU(cena_gorivo)} ({litara_gorivo:g} l)\n"
            f"Servisi: {_FORMATIRAJ_CENU(cena_servis)}   |   Ostali troskovi: {_FORMATIRAJ_CENU(cena_troskovi)}\n"
            f"Potrosnja: {potrosnja_txt}\n"
            f"Neto (zarada - gorivo - servisi - troskovi): {_FORMATIRAJ_CENU(neto)}"
        )

    def osvezi(self):
        danas_dt = datetime.now()
        danas = danas_dt.strftime("%Y-%m-%d")
        mesec = danas_dt.strftime("%Y-%m")
        pocetak_nedelje = (danas_dt - timedelta(days=danas_dt.weekday())).strftime("%Y-%m-%d")
        pocetak_meseca = danas_dt.strftime("%Y-%m-01")

        voznje_danas = db.voznje_za_datum(danas)
        broj_d, prihod_d, km_d = db.zbir_voznji(voznje_danas)
        self.tekst_danas = (
            f"DANAS ({danas})\n"
            f"Broj voznji: {broj_d}\n"
            f"Ukupno km: {km_d:.1f}\n"
            f"Ukupna zarada: {_FORMATIRAJ_CENU(prihod_d)}\n\n"
            + self._dodatne_linije_perioda(danas, danas, prihod_d)
        )
        self._prikazi_voznje_danas(voznje_danas)

        voznje_nedelje = db.voznje_izmedju(pocetak_nedelje, danas)
        broj_n, prihod_n, km_n = db.zbir_voznji(voznje_nedelje)
        self.tekst_nedelja = (
            f"OVA NEDELJA ({pocetak_nedelje} - {danas})\n"
            f"Broj voznji: {broj_n}\n"
            f"Ukupno km: {km_n:.1f}\n"
            f"Ukupna zarada: {_FORMATIRAJ_CENU(prihod_n)}\n\n"
            + self._dodatne_linije_perioda(pocetak_nedelje, danas, prihod_n)
        )

        voznje_mesec = db.voznje_za_mesec(mesec)
        broj_m, prihod_m, km_m = db.zbir_voznji(voznje_mesec)
        self.tekst_mesec = (
            f"OVAJ MESEC ({mesec})\n"
            f"Broj voznji: {broj_m}\n"
            f"Ukupno km: {km_m:.1f}\n"
            f"Ukupna zarada: {_FORMATIRAJ_CENU(prihod_m)}\n\n"
            + self._dodatne_linije_perioda(pocetak_meseca, danas, prihod_m)
        )

    def _prikazi_voznje_danas(self, voznje):
        kontejner = self.ids.lista_danas_voznje
        kontejner.clear_widgets()

        if not voznje:
            kontejner.add_widget(Label(
                text="Jos uvek nema voznji danas.",
                size_hint_y=None, height=32,
                color=(1, 1, 1, 1),
            ))
            return

        for v in voznje:
            vreme_pocetka = v["vreme_pocetka"] if "vreme_pocetka" in v.keys() else None
            vreme_txt = f"{vreme_pocetka} -> {v['vreme']}" if vreme_pocetka else f"Kraj {v['vreme']}"
            opis = f"{vreme_txt}   |   [b]{_FORMATIRAJ_CENU(v['ukupna_cena'])}[/b]"
            kontejner.add_widget(_NAPRAVI_RED_LISTE(
                opis,
                tint=(0.30, 0.40, 0.36, 0.85),
                boja_teksta=(0.92, 0.98, 0.94, 1),
                dugmad=[],
            ))

IZVESTAJ_KV = """
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
                tint: 0.36, 0.46, 0.64, 1
                font_size: '11sp'
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Kalkulator"
                tint: 0.36, 0.46, 0.64, 1
                font_size: '11sp'
                on_release: root.manager.current = "kalkulator"
            RoundButton:
                label_text: "Evidencija"
                tint: 0.36, 0.46, 0.64, 1
                font_size: '11sp'
                on_release: root.manager.current = "evidencija"
            RoundButton:
                label_text: "Izvoz PDF"
                tint: 0.55, 0.38, 0.26, 1
                font_size: '11sp'
                on_release: root.manager.current = "izvoz_pdf"

        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(10)
                padding: dp(2), dp(4)

                PastelCard:
                    orientation: "vertical"
                    tint: 0.55, 0.38, 0.26, 0.92
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(14)
                    Label:
                        id: label_danas
                        text: root.tekst_danas
                        font_size: '16sp'
                        halign: "left"
                        valign: "top"
                        size_hint_y: None
                        text_size: self.width, None
                        height: self.texture_size[1]
                        color: 1, 0.90, 0.80, 1

                FieldLabel:
                    text: "Voznje danas (pocetak - kraj, cena):"
                    size_hint_y: None
                    height: dp(28)

                BoxLayout:
                    id: lista_danas_voznje
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(8)

                PastelCard:
                    orientation: "vertical"
                    tint: 0.26, 0.48, 0.44, 0.92
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(14)
                    Label:
                        id: label_nedelja
                        text: root.tekst_nedelja
                        font_size: '16sp'
                        halign: "left"
                        valign: "top"
                        size_hint_y: None
                        text_size: self.width, None
                        height: self.texture_size[1]
                        color: 0.86, 1, 0.96, 1

                PastelCard:
                    orientation: "vertical"
                    tint: 0.38, 0.32, 0.52, 0.92
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(14)
                    Label:
                        id: label_mesec
                        text: root.tekst_mesec
                        font_size: '16sp'
                        halign: "left"
                        valign: "top"
                        size_hint_y: None
                        text_size: self.width, None
                        height: self.texture_size[1]
                        color: 0.92, 0.88, 1, 1


"""
