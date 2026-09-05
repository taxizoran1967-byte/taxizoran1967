"""
grafik_zarade.py
Ekran "Grafikon zarade" - dnevni/nedeljni/mesecni pregled zarade i
kilometraze, sa graficima nacrtanim rucno preko Kivy canvas-a (BEZ
spoljnih biblioteka za grafike - namerno, da ne bi napravilo problem
pri Android (buildozer) build-u koji vec radi besprekorno).

Ovaj fajl NE dira postojecu bazu ni postojecu logiku aplikacije -
koristi iskljucivo vec postojece funkcije iz database.py:
    - voznje_za_datum(datum_str)
    - voznje_za_mesec(godina_mesec_str)
    - voznje_izmedju(pocetak_str, kraj_str)
    - zbir_voznji(rows) -> (broj, prihod, km)

Valuta (RSD/EUR) prikaza se preuzima iz main.py preko poveži_valutu()
koju main.py poziva ODMAH POSLE uvoza ovog fajla - namerno, da se
izbegne kruzni uvoz (main.py uvozi ovaj fajl, pa ovaj fajl ne sme da
uvozi main.py nazad).
"""

import calendar
import re
from datetime import date, timedelta

from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivy.graphics import Color, Line, RoundedRectangle, Rectangle
from kivy.core.text import Label as CoreLabel
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.clock import Clock

import database as db

# ============================================================
# VALUTA - main.py ovo postavlja posle uvoza (izbegava kruzni import)
# ============================================================

_FORMAT_CENA = None  # main.formatiraj_cenu, injektuje main.py


def poveži_valutu(format_cena_fn):
    """main.py poziva ovo jednom, odmah posle 'import grafik_zarade',
    da ovaj ekran prikazuje novac u istoj valuti (RSD/EUR) koju je
    korisnik izabrao u Podesavanja -> Valuta."""
    global _FORMAT_CENA
    _FORMAT_CENA = format_cena_fn


# ============================================================
# GORIVO/SERVISI - main.py ovo postavlja posle uvoza (izbegava kruzni
# import, isti obrazac kao poveži_valutu iznad)
# ============================================================

_STAVKE_IZMEDJU = None
_POTROSNJA_INTERVALI = None
_GORIVO_REF = None
_SERVIS_REF = None


def poveži_gorivo_servis(stavke_izmedju_fn, potrosnja_intervali_fn, gorivo_obj, servis_obj):
    """main.py poziva ovo jednom, odmah posle 'import grafik_zarade', da
    bi ovaj ekran mogao da prikaze gorivo/servise/potrosnju za isti
    period koji je trenutno prikazan (dan/nedelja/mesec) - bez kruznog
    uvoza. stavke_izmedju_fn i potrosnja_intervali_fn su iste funkcije
    koje main.py koristi za PDF izvestaj, gorivo_obj/servis_obj su
    GORIVO/SERVIS objekti (JsonLog) iz main.py."""
    global _STAVKE_IZMEDJU, _POTROSNJA_INTERVALI, _GORIVO_REF, _SERVIS_REF
    _STAVKE_IZMEDJU = stavke_izmedju_fn
    _POTROSNJA_INTERVALI = potrosnja_intervali_fn
    _GORIVO_REF = gorivo_obj
    _SERVIS_REF = servis_obj


# ============================================================
# FORMATIRANJE BROJEVA (tacka kao hiljadni razdvajac, bez suvisnih
# decimala - po specifikaciji ekrana)
# ============================================================

def _format_broj(vrednost, decimals=0):
    if decimals == 0:
        tekst = f"{int(round(vrednost)):,}"
    else:
        tekst = f"{vrednost:,.{decimals}f}"
    return tekst.replace(",", ".")


def _km_tekst(km):
    if abs(km - round(km)) < 0.05:
        return f"{_format_broj(round(km), 0)} km"
    return f"{_format_broj(km, 1)} km"


def _novac_tekst(iznos_rsd):
    """Vraca (broj_sa_tackama, oznaka_valute) - koristi POSTOJECI
    main.formatiraj_cenu za pravu vrednost/valutu, samo doda tacke
    kao hiljadni razdvajac."""
    if _FORMAT_CENA is not None:
        sirovo = _FORMAT_CENA(iznos_rsd)
    else:
        sirovo = f"{iznos_rsd:.0f} RSD"
    try:
        broj_str, oznaka = sirovo.rsplit(" ", 1)
    except ValueError:
        return sirovo, ""
    if "." in broj_str:
        ceo_str, dec_str = broj_str.split(".", 1)
        try:
            broj_str = f"{_format_broj(int(ceo_str), 0)}.{dec_str}"
        except ValueError:
            pass
    else:
        try:
            broj_str = _format_broj(int(float(broj_str)), 0)
        except ValueError:
            pass
    return broj_str, oznaka


def _novac_puno(iznos_rsd):
    broj, oznaka = _novac_tekst(iznos_rsd)
    return f"{broj} {oznaka}".strip()


def _prosek_km_tekst(ukupna_zarada_rsd, ukupno_km):
    if ukupno_km <= 0:
        return "-"
    prosek_rsd = ukupna_zarada_rsd / ukupno_km
    if _FORMAT_CENA is not None:
        sirovo = _FORMAT_CENA(prosek_rsd)
    else:
        sirovo = f"{prosek_rsd:.0f} RSD"
    try:
        broj_str, oznaka = sirovo.rsplit(" ", 1)
        return f"{float(broj_str):.2f} {oznaka}/km"
    except ValueError:
        return f"{sirovo}/km"


# ============================================================
# DATUMI
# ============================================================

DANI_KRATKI = ["Pon", "Uto", "Sre", "Čet", "Pet", "Sub", "Ned"]
MESECI = ["JANUAR", "FEBRUAR", "MART", "APRIL", "MAJ", "JUN", "JUL",
          "AVGUST", "SEPTEMBAR", "OKTOBAR", "NOVEMBAR", "DECEMBAR"]


def _pocetak_nedelje(d):
    return d - timedelta(days=d.weekday())


# ============================================================
# AGREGACIJA PODATAKA - koristi SAMO postojece funkcije iz database.py
# ============================================================

def izracunaj_dan(datum):
    datum_str = datum.strftime("%Y-%m-%d")
    rows = db.voznje_za_datum(datum_str)
    broj, prihod, km = db.zbir_voznji(rows)

    sati_prihod = [0.0] * 24
    sati_km = [0.0] * 24
    for r in rows:
        try:
            h = int(str(r["vreme"]).split(":")[0])
        except Exception:
            continue
        if 0 <= h < 24:
            sati_prihod[h] += r["ukupna_cena"]
            sati_km[h] += r["km"]

    graf_zarada = [(f"{h:02d}h", sati_prihod[h]) for h in range(24)
                   if sati_prihod[h] > 0 or sati_km[h] > 0]
    graf_km = [(f"{h:02d}h", sati_km[h]) for h in range(24)
               if sati_prihod[h] > 0 or sati_km[h] > 0]

    najbolja = max(rows, key=lambda r: r["ukupna_cena"]) if rows else None
    najduza = max(rows, key=lambda r: r["km"]) if rows else None

    return {
        "prazno": broj == 0,
        "naslov": datum.strftime("%d.%m.%Y"),
        "ukupno_broj": broj,
        "ukupno_prihod": prihod,
        "ukupno_km": km,
        "graf_zarada": graf_zarada,
        "graf_km": graf_km,
        "najbolja_voznja": najbolja,
        "najduza_voznja": najduza,
    }


def izracunaj_nedelju(pocetak):
    kraj = pocetak + timedelta(days=6)
    rows = db.voznje_izmedju(pocetak.strftime("%Y-%m-%d"), kraj.strftime("%Y-%m-%d"))
    broj, prihod, km = db.zbir_voznji(rows)

    po_danu = {}
    for i in range(7):
        d = pocetak + timedelta(days=i)
        po_danu[d.strftime("%Y-%m-%d")] = {"prihod": 0.0, "km": 0.0}
    for r in rows:
        if r["datum"] in po_danu:
            po_danu[r["datum"]]["prihod"] += r["ukupna_cena"]
            po_danu[r["datum"]]["km"] += r["km"]

    graf_zarada, graf_km = [], []
    najbolji_dan, najbolji_iznos = None, -1
    najkm_dan, najkm_vrednost = None, -1
    for i in range(7):
        d = pocetak + timedelta(days=i)
        p = po_danu[d.strftime("%Y-%m-%d")]
        graf_zarada.append((DANI_KRATKI[i], p["prihod"]))
        graf_km.append((DANI_KRATKI[i], p["km"]))
        if p["prihod"] > najbolji_iznos:
            najbolji_iznos = p["prihod"]
            najbolji_dan = (DANI_KRATKI[i], p["prihod"])
        if p["km"] > najkm_vrednost:
            najkm_vrednost = p["km"]
            najkm_dan = (DANI_KRATKI[i], p["km"])

    return {
        "prazno": broj == 0,
        "naslov": f"{pocetak.strftime('%d.%m')} - {kraj.strftime('%d.%m.%Y')}",
        "ukupno_broj": broj,
        "ukupno_prihod": prihod,
        "ukupno_km": km,
        "prosecna_dnevna": prihod / 7,
        "najbolji_dan": najbolji_dan,
        "najkm_dan": najkm_dan,
        "graf_zarada": graf_zarada,
        "graf_km": graf_km,
    }


def izracunaj_mesec(godina, mesec):
    godina_mesec_str = f"{godina:04d}-{mesec:02d}"
    rows = db.voznje_za_mesec(godina_mesec_str)
    broj, prihod, km = db.zbir_voznji(rows)

    broj_dana = calendar.monthrange(godina, mesec)[1]
    po_danu_prihod = [0.0] * (broj_dana + 1)
    po_danu_km = [0.0] * (broj_dana + 1)
    po_danu_broj = [0] * (broj_dana + 1)
    for r in rows:
        try:
            dan = int(r["datum"].split("-")[2])
        except Exception:
            continue
        if 1 <= dan <= broj_dana:
            po_danu_prihod[dan] += r["ukupna_cena"]
            po_danu_km[dan] += r["km"]
            po_danu_broj[dan] += 1

    graf_zarada = [(str(d), po_danu_prihod[d]) for d in range(1, broj_dana + 1)]
    graf_km = [(str(d), po_danu_km[d]) for d in range(1, broj_dana + 1)]

    dani_sa_voznjama = [d for d in range(1, broj_dana + 1) if po_danu_broj[d] > 0]
    najbolji_dan = najslabiji_dan = najkm_dan = None
    if dani_sa_voznjama:
        nb = max(dani_sa_voznjama, key=lambda d: po_danu_prihod[d])
        ns = min(dani_sa_voznjama, key=lambda d: po_danu_prihod[d])
        nk = max(dani_sa_voznjama, key=lambda d: po_danu_km[d])
        najbolji_dan = (nb, po_danu_prihod[nb])
        najslabiji_dan = (ns, po_danu_prihod[ns])
        najkm_dan = (nk, po_danu_km[nk])

    return {
        "prazno": broj == 0,
        "naslov": f"{MESECI[mesec - 1]} {godina}",
        "ukupno_broj": broj,
        "ukupno_prihod": prihod,
        "ukupno_km": km,
        "prosecna_dnevna": prihod / broj_dana,
        "najbolji_dan": najbolji_dan,
        "najslabiji_dan": najslabiji_dan,
        "najkm_dan": najkm_dan,
        "graf_zarada": graf_zarada,
        "graf_km": graf_km,
    }


# ============================================================
# TOOLTIP (mali popup kad korisnik dodirne stub/tacku na grafiku)
# ============================================================

def _prikazi_tooltip(oznaka, vrednost_tekst):
    sadrzaj = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(6))
    sadrzaj.add_widget(Label(
        text=oznaka, font_size='15sp', bold=True, color=(0.85, 0.85, 0.95, 1),
        size_hint_y=None, height=dp(26),
    ))
    sadrzaj.add_widget(Label(
        text=vrednost_tekst, font_size='20sp', bold=True, color=(0.75, 0.85, 1, 1),
        size_hint_y=None, height=dp(30),
    ))
    popup = Popup(title="", separator_height=0, content=sadrzaj, size_hint=(0.62, 0.24))
    popup.open()
    return popup


# ============================================================
# GRAFIKON - canvas widget (bar ILI line mod), bez spoljnih biblioteka
# ============================================================

class GrafikCanvas(Widget):
    podaci = ListProperty([])       # [(label, vrednost), ...]
    mod = StringProperty("bar")     # "bar" ili "line"
    boja_glavna = ListProperty([0.55, 0.62, 0.95, 1])
    _progres = NumericProperty(0.0)

    def __init__(self, **kwargs):
        self.register_event_type("on_izabrana_tacka")
        super().__init__(**kwargs)
        self._tacke = []
        self.bind(
            pos=self._pokreni_animaciju,
            size=self._pokreni_animaciju,
            podaci=self._pokreni_animaciju,
            mod=self._pokreni_animaciju,
            _progres=lambda *a: self._nacrtaj(),
        )

    def on_izabrana_tacka(self, *args):
        pass

    def _pokreni_animaciju(self, *args):
        Animation.cancel_all(self, "_progres")
        self._progres = 0.0
        Animation(_progres=1.0, d=0.45, t="out_cubic").start(self)

    def _nacrtaj_tekst(self, tekst, cx, cy, veličina=10, boja=(1, 1, 1, 0.7)):
        core = CoreLabel(text=tekst, font_size=dp(veličina))
        core.refresh()
        tex = core.texture
        Color(*boja)
        Rectangle(texture=tex, pos=(cx - tex.size[0] / 2, cy - tex.size[1] / 2), size=tex.size)

    def _nacrtaj(self):
        self.canvas.clear()
        self._tacke = []
        if not self.podaci or self.width <= 0 or self.height <= 0:
            return

        vrednosti = [v for _, v in self.podaci]
        maxv = max(vrednosti) if vrednosti else 0
        if maxv <= 0:
            maxv = 1

        pad_l, pad_r = dp(6), dp(10)
        pad_t, pad_b = dp(16), dp(26)
        x0 = self.x + pad_l
        y0 = self.y + pad_b
        w = self.width - pad_l - pad_r
        h = self.height - pad_t - pad_b
        if w <= 0 or h <= 0:
            return

        progres = self._progres
        n = len(self.podaci)

        with self.canvas:
            Color(1, 1, 1, 0.08)
            for i in range(1, 4):
                gy = y0 + h * i / 4
                Line(points=[x0, gy, x0 + w, gy], width=1)

            self._nacrtaj_tekst(_format_broj(maxv, 0), x0 + dp(20), y0 + h + dp(8),
                                 veličina=9, boja=(1, 1, 1, 0.5))

            if n == 0:
                return

            if self.mod == "bar":
                razmak = dp(6) if n <= 10 else dp(3)
                sirina = max((w - razmak * (n - 1)) / n, dp(3))
                preskoci = max(1, n // 8)
                for i, (label, vrednost) in enumerate(self.podaci):
                    bx = x0 + i * (sirina + razmak)
                    bh = (vrednost / maxv) * h * progres
                    Color(*self.boja_glavna)
                    RoundedRectangle(pos=(bx, y0), size=(sirina, max(bh, dp(2))), radius=[dp(4)])
                    self._tacke.append((bx + sirina / 2, label, vrednost))
                    if i % preskoci == 0 or n <= 10:
                        self._nacrtaj_tekst(label, bx + sirina / 2, y0 - dp(12), veličina=9)
            else:
                if n == 1:
                    label, vrednost = self.podaci[0]
                    py = y0 + (vrednost / maxv) * h * progres
                    Color(*self.boja_glavna)
                    RoundedRectangle(pos=(x0 + w / 2 - dp(4), py - dp(4)), size=(dp(8), dp(8)), radius=[dp(4)])
                    self._tacke.append((x0 + w / 2, label, vrednost))
                else:
                    korak = w / (n - 1)
                    preskoci = max(1, n // 6)
                    tacke_linije = []
                    for i, (label, vrednost) in enumerate(self.podaci):
                        px = x0 + i * korak
                        py = y0 + (vrednost / maxv) * h * progres
                        tacke_linije += [px, py]
                        self._tacke.append((px, label, vrednost))
                        Color(*self.boja_glavna[:3], 0.12)
                        Line(points=[px, y0, px, py], width=dp(1))
                        if i % preskoci == 0 or i == n - 1:
                            self._nacrtaj_tekst(label, px, y0 - dp(12), veličina=9)

                    Color(*self.boja_glavna)
                    Line(points=tacke_linije, width=dp(2.2), joint="round", cap="round")
                    for i, (label, vrednost) in enumerate(self.podaci):
                        px = x0 + i * korak
                        py = y0 + (vrednost / maxv) * h * progres
                        Color(1, 1, 1, 1)
                        RoundedRectangle(pos=(px - dp(2.5), py - dp(2.5)), size=(dp(5), dp(5)), radius=[dp(2.5)])

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos) or not self._tacke:
            return super().on_touch_down(touch)
        najbliza = min(self._tacke, key=lambda t: abs(t[0] - touch.x))
        _, label, vrednost = najbliza
        self.dispatch("on_izabrana_tacka", label, vrednost)
        return True


# ============================================================
# EKRAN
# ============================================================

class GrafikZaradeScreen(Screen):
    period = StringProperty("dan")      # "dan" | "nedelja" | "mesec"
    prikaz = StringProperty("zarada")   # "zarada" | "km"

    naslov_perioda = StringProperty("")
    prazno_stanje = BooleanProperty(False)
    moze_napred = BooleanProperty(True)

    tekst_zarada_karta = StringProperty("0 RSD")
    tekst_km_karta = StringProperty("0 km")
    tekst_prosek_karta = StringProperty("-")

    graf_podaci = ListProperty([])
    graf_mod = StringProperty("bar")

    tekst_extra_1 = StringProperty("")
    tekst_extra_2 = StringProperty("")
    tekst_extra_3 = StringProperty("")
    tekst_extra_4 = StringProperty("")

    tekst_gorivo_servis = StringProperty("")

    def on_pre_enter(self, *args):
        danas = date.today()
        self._dnevni_datum = danas
        self._nedeljni_pocetak = _pocetak_nedelje(danas)
        self._mesecni_godina = danas.year
        self._mesecni_mesec = danas.month
        self._ucitaj()

    # ---------- period / prikaz ----------

    def izaberi_period(self, novi_period):
        if self.period == novi_period:
            return
        self.period = novi_period
        self._ucitaj()

    def izaberi_prikaz(self, novi_prikaz):
        if self.prikaz == novi_prikaz:
            return
        self.prikaz = novi_prikaz
        self._ucitaj()

    # ---------- navigacija kroz datume ----------

    def prethodni(self):
        if self.period == "dan":
            self._dnevni_datum -= timedelta(days=1)
        elif self.period == "nedelja":
            self._nedeljni_pocetak -= timedelta(days=7)
        else:
            self._mesecni_mesec -= 1
            if self._mesecni_mesec < 1:
                self._mesecni_mesec = 12
                self._mesecni_godina -= 1
        self._ucitaj()

    def sledeci(self):
        if not self.moze_napred:
            return
        if self.period == "dan":
            self._dnevni_datum += timedelta(days=1)
        elif self.period == "nedelja":
            self._nedeljni_pocetak += timedelta(days=7)
        else:
            self._mesecni_mesec += 1
            if self._mesecni_mesec > 12:
                self._mesecni_mesec = 1
                self._mesecni_godina += 1
        self._ucitaj()

    # ---------- ucitavanje ----------

    def _ucitaj(self):
        danas = date.today()
        if self.period == "dan":
            podaci = izracunaj_dan(self._dnevni_datum)
            self.moze_napred = self._dnevni_datum < danas
            self.graf_mod = "bar"
        elif self.period == "nedelja":
            podaci = izracunaj_nedelju(self._nedeljni_pocetak)
            self.moze_napred = (self._nedeljni_pocetak + timedelta(days=7)) <= danas
            self.graf_mod = "bar"
        else:
            podaci = izracunaj_mesec(self._mesecni_godina, self._mesecni_mesec)
            self.moze_napred = (self._mesecni_godina, self._mesecni_mesec) < (danas.year, danas.month)
            self.graf_mod = "line"

        self.naslov_perioda = podaci["naslov"]
        self.prazno_stanje = podaci["prazno"]

        self.tekst_zarada_karta = _novac_puno(podaci["ukupno_prihod"])
        self.tekst_km_karta = _km_tekst(podaci["ukupno_km"])
        self.tekst_prosek_karta = _prosek_km_tekst(podaci["ukupno_prihod"], podaci["ukupno_km"])

        kljuc = "graf_zarada" if self.prikaz == "zarada" else "graf_km"
        self.graf_podaci = podaci.get(kljuc, [])

        self._popuni_extra(podaci)
        self._popuni_gorivo_servis(podaci["ukupno_prihod"])

    def _opseg_perioda(self):
        """Vraca (pocetak_str, kraj_str) za trenutno prikazani period
        (dan/nedelja/mesec), format GGGG-MM-DD, oba kraja ukljucena -
        koristi se da se gorivo/servisi filtriraju za isti period koji
        je trenutno prikazan na grafiku."""
        if self.period == "dan":
            p = self._dnevni_datum
            return p.strftime("%Y-%m-%d"), p.strftime("%Y-%m-%d")
        elif self.period == "nedelja":
            p = self._nedeljni_pocetak
            k = p + timedelta(days=6)
            return p.strftime("%Y-%m-%d"), k.strftime("%Y-%m-%d")
        else:
            p = date(self._mesecni_godina, self._mesecni_mesec, 1)
            poslednji_dan = calendar.monthrange(self._mesecni_godina, self._mesecni_mesec)[1]
            k = date(self._mesecni_godina, self._mesecni_mesec, poslednji_dan)
            return p.strftime("%Y-%m-%d"), k.strftime("%Y-%m-%d")

    def _popuni_gorivo_servis(self, ukupan_prihod):
        if _STAVKE_IZMEDJU is None or _GORIVO_REF is None or _SERVIS_REF is None:
            # main.py jos nije pozvao poveži_gorivo_servis() - karticu
            # jednostavno ne prikazujemo (vidi height/opacity u KV-u).
            self.tekst_gorivo_servis = ""
            return

        pocetak, kraj = self._opseg_perioda()
        gorivo_p = _STAVKE_IZMEDJU(_GORIVO_REF.stavke, pocetak, kraj)
        servisi_p = _STAVKE_IZMEDJU(_SERVIS_REF.stavke, pocetak, kraj)
        cena_gorivo = sum(s.get("cena", 0) for s in gorivo_p)
        litara_gorivo = sum(s.get("litara", 0) for s in gorivo_p)
        cena_servis = sum(s.get("cena", 0) for s in servisi_p)

        intervali = [
            i for i in _POTROSNJA_INTERVALI(_GORIVO_REF.stavke)
            if pocetak <= i["datum"] <= kraj
        ]
        if intervali:
            ukupno_km_pot = sum(i["km_predjeno"] for i in intervali)
            ukupno_l_pot = sum(i["litara"] for i in intervali)
            potrosnja_txt = f"{(ukupno_l_pot / ukupno_km_pot * 100):.1f} l/100km" if ukupno_km_pot > 0 else "-"
        else:
            potrosnja_txt = "nema podataka"

        neto = ukupan_prihod - cena_gorivo - cena_servis

        self.tekst_gorivo_servis = (
            f"Gorivo: {_novac_puno(cena_gorivo)} ({litara_gorivo:g} l)   |   Servisi: {_novac_puno(cena_servis)}\n"
            f"Potrosnja: {potrosnja_txt}   |   Neto zarada: {_novac_puno(neto)}"
        )

    def _popuni_extra(self, podaci):
        if self.period == "dan":
            nb = podaci.get("najbolja_voznja")
            nd = podaci.get("najduza_voznja")
            self.tekst_extra_1 = (f"🏆 Najbolja voznja\n{_novac_puno(nb['ukupna_cena'])}"
                                   if nb else "🏆 Najbolja voznja\n-")
            self.tekst_extra_2 = (f"🚕 Najduza voznja\n{_km_tekst(nd['km'])}"
                                   if nd else "🚕 Najduza voznja\n-")
            self.tekst_extra_3 = f"🕒 Broj voznji\n{podaci['ukupno_broj']}"
            self.tekst_extra_4 = ""
        elif self.period == "nedelja":
            nb = podaci.get("najbolji_dan")
            nk = podaci.get("najkm_dan")
            self.tekst_extra_1 = f"📊 Prosecna dnevna zarada\n{_novac_puno(podaci['prosecna_dnevna'])}"
            self.tekst_extra_2 = (f"🏆 Najbolji dan\n{nb[0]} - {_novac_puno(nb[1])}"
                                   if nb else "🏆 Najbolji dan\n-")
            self.tekst_extra_3 = (f"🚕 Najvise kilometara\n{nk[0]} - {_km_tekst(nk[1])}"
                                   if nk else "🚕 Najvise kilometara\n-")
            self.tekst_extra_4 = ""
        else:
            nb = podaci.get("najbolji_dan")
            ns = podaci.get("najslabiji_dan")
            nk = podaci.get("najkm_dan")
            self.tekst_extra_1 = (f"🏆 Najbolji dan\n{nb[0]}. - {_novac_puno(nb[1])}"
                                   if nb else "🏆 Najbolji dan\n-")
            self.tekst_extra_2 = (f"📉 Najslabiji dan\n{ns[0]}. - {_novac_puno(ns[1])}"
                                   if ns else "📉 Najslabiji dan\n-")
            self.tekst_extra_3 = (f"🚕 Najvise kilometara\n{nk[0]}. - {_km_tekst(nk[1])}"
                                   if nk else "🚕 Najvise kilometara\n-")
            self.tekst_extra_4 = f"📊 Prosecna dnevna zarada\n{_novac_puno(podaci['prosecna_dnevna'])}"

    # ---------- tooltip ----------

    def prikazi_tooltip(self, label, vrednost):
        if self.prikaz == "km":
            vrednost_tekst = _km_tekst(vrednost)
        else:
            vrednost_tekst = _novac_puno(vrednost)
        _prikazi_tooltip(f"{self.naslov_perioda} - {label}", vrednost_tekst)


# ============================================================
# KV
# ============================================================

GRAFIK_KV = """
<SegmentDugme@ButtonBehavior+BoxLayout>:
    label_text: ""
    aktivno: False
    canvas.before:
        Color:
            rgba: (0.42, 0.52, 0.88, 1) if root.aktivno else (0.26, 0.26, 0.36, 0.55)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(14)]
    Label:
        text: root.label_text
        bold: True
        color: (1, 1, 1, 1) if root.aktivno else (0.78, 0.78, 0.88, 1)
        font_size: '13sp'
        text_size: self.width - dp(4), None
        halign: 'center'
        valign: 'middle'

<StatCard@BoxLayout>:
    orientation: "vertical"
    ikonica: ""
    opis: ""
    vrednost: ""
    tint: 0.32, 0.30, 0.50, 0.85
    padding: dp(8)
    spacing: dp(1)
    canvas.before:
        Color:
            rgba: 0, 0, 0, 0.14
        RoundedRectangle:
            pos: self.x, self.y - dp(2)
            size: self.size
            radius: [dp(16)]
        Color:
            rgba: root.tint
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(16)]
    Label:
        text: root.ikonica
        font_size: '19sp'
        size_hint_y: None
        height: dp(24)
    Label:
        text: root.vrednost
        font_size: '14sp'
        bold: True
        color: 1, 1, 1, 1
        size_hint_y: None
        height: dp(20)
        text_size: self.width, None
        halign: 'center'
        shorten: True
        shorten_from: 'right'
    Label:
        text: root.opis
        font_size: '9.5sp'
        color: 0.82, 0.82, 0.92, 1
        size_hint_y: None
        height: dp(15)
        text_size: self.width, None
        halign: 'center'

<ExtraCard@BoxLayout>:
    tekst: ""
    tint: 0.30, 0.34, 0.48, 0.85
    padding: dp(12)
    canvas.before:
        Color:
            rgba: 0, 0, 0, 0.12
        RoundedRectangle:
            pos: self.x, self.y - dp(2)
            size: self.size
            radius: [dp(16)]
        Color:
            rgba: root.tint
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(16)]
    Label:
        text: root.tekst
        font_size: '13sp'
        color: 0.94, 0.94, 1, 1
        text_size: self.width, None
        halign: 'left'
        valign: 'middle'

<GrafikZaradeScreen>:
    name: "grafik"
    ScreenRoot:

        BoxLayout:
            size_hint_y: None
            height: dp(42)
            spacing: dp(10)
            RoundButton:
                size_hint_x: None
                width: dp(42)
                label_text: "<"
                tint: 0.30, 0.34, 0.48, 1
                on_release: root.manager.current = "podesavanja"
            TitleLabel:
                text: "Grafikon zarade"

        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(14)
                padding: dp(2), dp(6)

                BoxLayout:
                    size_hint_y: None
                    height: dp(82)
                    spacing: dp(8)
                    StatCard:
                        ikonica: "💰"
                        vrednost: root.tekst_zarada_karta
                        opis: "Ukupna zarada"
                        tint: 0.26, 0.42, 0.30, 0.9
                    StatCard:
                        ikonica: "🚕"
                        vrednost: root.tekst_km_karta
                        opis: "Ukupno kilometara"
                        tint: 0.24, 0.34, 0.52, 0.9
                    StatCard:
                        ikonica: "📈"
                        vrednost: root.tekst_prosek_karta
                        opis: "Prosek"
                        tint: 0.40, 0.30, 0.48, 0.9

                BoxLayout:
                    size_hint_y: None
                    height: dp(40)
                    spacing: dp(6)
                    SegmentDugme:
                        label_text: "Dnevni"
                        aktivno: root.period == "dan"
                        on_release: root.izaberi_period("dan")
                    SegmentDugme:
                        label_text: "Nedeljni"
                        aktivno: root.period == "nedelja"
                        on_release: root.izaberi_period("nedelja")
                    SegmentDugme:
                        label_text: "Mesecni"
                        aktivno: root.period == "mesec"
                        on_release: root.izaberi_period("mesec")

                BoxLayout:
                    size_hint_y: None
                    height: dp(36)
                    spacing: dp(6)
                    SegmentDugme:
                        label_text: "💰 Zarada"
                        aktivno: root.prikaz == "zarada"
                        on_release: root.izaberi_prikaz("zarada")
                    SegmentDugme:
                        label_text: "🚕 Kilometri"
                        aktivno: root.prikaz == "km"
                        on_release: root.izaberi_prikaz("km")

                BoxLayout:
                    size_hint_y: None
                    height: dp(40)
                    spacing: dp(8)
                    RoundButton:
                        size_hint_x: None
                        width: dp(48)
                        label_text: "<"
                        tint: 0.30, 0.34, 0.48, 1
                        on_release: root.prethodni()
                    Label:
                        text: root.naslov_perioda
                        bold: True
                        font_size: '15sp'
                        color: 1, 1, 1, 1
                        halign: "center"
                        valign: "middle"
                        text_size: self.size
                    RoundButton:
                        size_hint_x: None
                        width: dp(48)
                        label_text: ">"
                        tint: 0.30, 0.34, 0.48, 1
                        opacity: 1 if root.moze_napred else 0.35
                        disabled: not root.moze_napred
                        on_release: root.sledeci()

                PastelCard:
                    tint: 0.22, 0.20, 0.32, 0.92
                    size_hint_y: None
                    height: dp(220)
                    padding: dp(10)
                    FloatLayout:
                        Label:
                            text: "📊\\n\\nNema podataka za ovaj period\\n\\nDodaj nekoliko voznji da bi se ovde\\nprikazala statistika zarade."
                            opacity: 1 if root.prazno_stanje else 0
                            halign: "center"
                            valign: "middle"
                            text_size: self.width - dp(20), None
                            color: 0.85, 0.85, 0.95, 1
                            font_size: '14sp'
                        GrafikCanvas:
                            id: platno
                            opacity: 0 if root.prazno_stanje else 1
                            podaci: root.graf_podaci
                            mod: root.graf_mod
                            on_izabrana_tacka: root.prikazi_tooltip(*args[1:])

                ExtraCard:
                    tekst: root.tekst_extra_1
                    size_hint_y: None
                    height: dp(52)

                ExtraCard:
                    tekst: root.tekst_extra_2
                    size_hint_y: None
                    height: dp(52)

                ExtraCard:
                    tekst: root.tekst_extra_3
                    size_hint_y: None
                    height: dp(52)

                ExtraCard:
                    tekst: root.tekst_extra_4
                    size_hint_y: None
                    height: dp(48) if root.tekst_extra_4 else 0
                    opacity: 1 if root.tekst_extra_4 else 0

                ExtraCard:
                    tint: 0.46, 0.34, 0.24, 0.9
                    tekst: root.tekst_gorivo_servis
                    size_hint_y: None
                    height: dp(64) if root.tekst_gorivo_servis else 0
                    opacity: 1 if root.tekst_gorivo_servis else 0

                Widget:
                    size_hint_y: None
                    height: dp(6)
"""
