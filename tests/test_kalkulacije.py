"""
test_kalkulacije.py
Jednostavni testovi za servisi/kalkulacije.py - BEZ ikakvog test
frameworka (bez pytest-a), samo obicni Python i "assert". Pokreni ih
ovako, iz glavnog foldera projekta:

    python3 tests/test_kalkulacije.py

Ako sve prodje, na kraju pise "SVI TESTOVI PROSLI." i program se
zavrsi normalno (exit kod 0). Ako nesto ne valja, AssertionError ce
pokazati TACNO koji test i koja linija nije prosla, i program ce se
zavrsiti sa greskom (exit kod 1) - to je bitno ako se ovo ikad doda
u GitHub Actions kao provera pre svakog build-a.

Ne treba Kivy, Android, niti pokrenuta aplikacija - ovo su ciste
Python funkcije, testiraju se potpuno nezavisno.
"""

import os
import sys

# Da bi "from servisi import kalkulacije" radio i kad se test
# pokrene direktno (python3 tests/test_kalkulacije.py), a ne samo
# kao modul - dodajemo koren projekta u putanju za pretragu.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servisi import kalkulacije


# ============================================================
# TESTOVI ZA CENU VOZNJE
# ============================================================

def test_osnovna_cena():
    """10 km po 80 din/km + start taksa 150 = 950."""
    cena = kalkulacije.izracunaj_cenu_voznje(km=10, cena_po_km=80, start_taksa=150)
    assert cena == 950, f"Ocekivano 950, dobijeno {cena}"


def test_cena_bez_kilometara():
    """0 km - cena je samo start taksa."""
    cena = kalkulacije.izracunaj_cenu_voznje(km=0, cena_po_km=80, start_taksa=150)
    assert cena == 150, f"Ocekivano 150, dobijeno {cena}"


def test_cena_bez_start_takse():
    """Start taksa 0 - cena je cisto km * cena_po_km."""
    cena = kalkulacije.izracunaj_cenu_voznje(km=5, cena_po_km=100, start_taksa=0)
    assert cena == 500, f"Ocekivano 500, dobijeno {cena}"


def test_cena_sa_decimalnim_kilometrima():
    """Decimalni km (npr. 7.5 km) moraju da rade ispravno."""
    cena = kalkulacije.izracunaj_cenu_voznje(km=7.5, cena_po_km=80, start_taksa=150)
    assert cena == 750.0, f"Ocekivano 750.0, dobijeno {cena}"


def test_nocna_tarifa_veca_od_osnovne():
    """Sanity-check: ista kilometraza sa vecom cenom po km mora dati
    vecu ukupnu cenu (npr. nocna tarifa > osnovna tarifa)."""
    cena_osnovna = kalkulacije.izracunaj_cenu_voznje(km=10, cena_po_km=80, start_taksa=150)
    cena_nocna = kalkulacije.izracunaj_cenu_voznje(km=10, cena_po_km=100, start_taksa=150)
    assert cena_nocna > cena_osnovna, "Nocna tarifa mora dati vecu cenu od osnovne za isti km"


# ============================================================
# TESTOVI ZA POTROSNJU GORIVA
# ============================================================

def test_potrosnja_dva_sipanja():
    """Dva sipanja, 500 km izmedju njih, drugo sipanje 40 litara
    -> potrosnja = 40 / 500 * 100 = 8.0 l/100km."""
    stavke = [
        {"datum": "2026-09-01", "km_pumpe": 100000, "litara": 35},
        {"datum": "2026-09-10", "km_pumpe": 100500, "litara": 40},
    ]
    intervali = kalkulacije.izracunaj_potrosnju_intervale(stavke)
    assert len(intervali) == 1, f"Ocekivan 1 interval, dobijeno {len(intervali)}"
    assert intervali[0]["km_predjeno"] == 500
    assert intervali[0]["potrosnja"] == 8.0, f"Ocekivano 8.0, dobijeno {intervali[0]['potrosnja']}"


def test_potrosnja_tri_sipanja_dva_intervala():
    """Tri sipanja daju TACNO dva intervala (izmedju 1-2 i 2-3)."""
    stavke = [
        {"datum": "2026-09-01", "km_pumpe": 100000, "litara": 35},
        {"datum": "2026-09-10", "km_pumpe": 100500, "litara": 40},
        {"datum": "2026-09-20", "km_pumpe": 101200, "litara": 50},
    ]
    intervali = kalkulacije.izracunaj_potrosnju_intervale(stavke)
    assert len(intervali) == 2, f"Ocekivana 2 intervala, dobijeno {len(intervali)}"
    # drugi interval: 101200 - 100500 = 700 km, 50 litara
    assert intervali[1]["km_predjeno"] == 700
    assert round(intervali[1]["potrosnja"], 2) == round(50 / 700 * 100, 2)


def test_potrosnja_preskace_sipanja_bez_kilometraze():
    """Sipanje bez upisane km_pumpe (0, None ili nedostaje) se
    preskace - ne sme da uleti u racunicu niti da izazove gresku."""
    stavke = [
        {"datum": "2026-09-01", "km_pumpe": 100000, "litara": 35},
        {"datum": "2026-09-05", "litara": 20},  # bez km_pumpe - preskace se
        {"datum": "2026-09-10", "km_pumpe": 100500, "litara": 40},
    ]
    intervali = kalkulacije.izracunaj_potrosnju_intervale(stavke)
    assert len(intervali) == 1, f"Ocekivan 1 interval (sipanje bez km se preskace), dobijeno {len(intervali)}"
    assert intervali[0]["km_predjeno"] == 500


def test_potrosnja_prazna_lista():
    """Prazna lista goriva -> prazna lista intervala, bez greske."""
    intervali = kalkulacije.izracunaj_potrosnju_intervale([])
    assert intervali == [], f"Ocekivana prazna lista, dobijeno {intervali}"


def test_potrosnja_samo_jedno_sipanje():
    """Samo jedno sipanje - nema sa cim da se uporedi, pa mora da
    vrati praznu listu (ne sme da pukne)."""
    stavke = [{"datum": "2026-09-01", "km_pumpe": 100000, "litara": 35}]
    intervali = kalkulacije.izracunaj_potrosnju_intervale(stavke)
    assert intervali == [], f"Ocekivana prazna lista, dobijeno {intervali}"


def test_potrosnja_ne_zavisi_od_redosleda_unosa():
    """Funkcija SORTIRA unose po kilometrazi pre racunanja, pa redosled
    kojim su sipanja upisana u listu ne sme da utice na rezultat -
    isti primer kao test_potrosnja_dva_sipanja, samo obrnut redosled
    u ulaznoj listi, mora dati IDENTICAN rezultat."""
    stavke_obrnuto = [
        {"datum": "2026-09-10", "km_pumpe": 100500, "litara": 40},
        {"datum": "2026-09-01", "km_pumpe": 100000, "litara": 35},
    ]
    intervali = kalkulacije.izracunaj_potrosnju_intervale(stavke_obrnuto)
    assert len(intervali) == 1, f"Ocekivan 1 interval, dobijeno {len(intervali)}"
    assert intervali[0]["km_predjeno"] == 500
    assert intervali[0]["potrosnja"] == 8.0, f"Ocekivano 8.0, dobijeno {intervali[0]['potrosnja']}"


def test_potrosnja_preskace_identicnu_kilometrazu():
    """Ako dva sipanja imaju TACNO istu upisanu kilometrazu (npr.
    oba slucajno upisana kao ista vrednost), km_predjeno bi bio 0 -
    taj interval se preskace umesto da izazove deljenje nulom ili
    besmislenu (beskonacnu) potrosnju."""
    stavke = [
        {"datum": "2026-09-01", "km_pumpe": 100000, "litara": 35},
        {"datum": "2026-09-10", "km_pumpe": 100000, "litara": 40},
    ]
    intervali = kalkulacije.izracunaj_potrosnju_intervale(stavke)
    assert intervali == [], f"Ocekivana prazna lista za identicnu kilometrazu, dobijeno {intervali}"


# ============================================================
# POKRETANJE SVIH TESTOVA
# ============================================================

def _pokreni_sve_testove():
    testovi = [
        test_osnovna_cena,
        test_cena_bez_kilometara,
        test_cena_bez_start_takse,
        test_cena_sa_decimalnim_kilometrima,
        test_nocna_tarifa_veca_od_osnovne,
        test_potrosnja_dva_sipanja,
        test_potrosnja_tri_sipanja_dva_intervala,
        test_potrosnja_preskace_sipanja_bez_kilometraze,
        test_potrosnja_prazna_lista,
        test_potrosnja_samo_jedno_sipanje,
        test_potrosnja_ne_zavisi_od_redosleda_unosa,
        test_potrosnja_preskace_identicnu_kilometrazu,
    ]

    broj_uspesnih = 0
    for test_fn in testovi:
        try:
            test_fn()
            print(f"  OK   {test_fn.__name__}")
            broj_uspesnih += 1
        except AssertionError as e:
            print(f"  PAO  {test_fn.__name__}: {e}")

    print()
    if broj_uspesnih == len(testovi):
        print(f"SVI TESTOVI PROSLI. ({broj_uspesnih}/{len(testovi)})")
        return 0
    else:
        print(f"NEKI TESTOVI NISU PROSLI. ({broj_uspesnih}/{len(testovi)} uspesnih)")
        return 1


if __name__ == "__main__":
    sys.exit(_pokreni_sve_testove())
