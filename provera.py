#!/usr/bin/env python3
"""
provera.py - Brze automatske provere pre buildovanja aplikacije.

Cilj: uhvati istu vrstu gresaka koje su nam vec pravile probleme
(nedostajuci fajl, jezik dodat u JSON ali zaboravljen u dugmadima/PDF-u,
razlicit broj {parametara} izmedju jezika...) za par sekundi, umesto da
se to otkrije tek posle 20-30 minuta build-a, ili gore - tek na telefonu.

Ne zahteva Kivy ni buildozer - samo cist Python. Pokrece ga
.github/workflows/provera.yml pri svakom otpremanju u granu dev.

Zavrsava se gre[s]kom (exit kod 1) i ispisuje jasnu poruku ako nadje
problem - GitHub Actions to prikazuje crvenim X pored komita.
"""

import ast
import json
import os
import re
import sys

GRESKE = []
UPOZORENJA = []


def greska(poruka):
    """Ozbiljan problem - zaustavlja build (crveni X)."""
    GRESKE.append(poruka)
    print(f"❌ {poruka}")


def upozorenje(poruka):
    """Nedostaje prevod i slicno - aplikacija radi (pada nazad na
    srpski), samo se to javlja da bi se znalo da nesto treba prevesti.
    Ne zaustavlja build."""
    UPOZORENJA.append(poruka)
    print(f"⚠️  {poruka}")


def ok(poruka):
    print(f"✅ {poruka}")


# ============================================================
# 1) SINTAKSA - svaki .py fajl u repou mora da se ucita bez greske
# ============================================================

def proveri_sintaksu(koren):
    broj = 0
    for dirpath, dirnames, filenames in os.walk(koren):
        dirnames[:] = [
            d for d in dirnames
            if d not in (".git", ".buildozer", "bin", "__pycache__")
        ]
        for naziv in filenames:
            if not naziv.endswith(".py"):
                continue
            putanja = os.path.join(dirpath, naziv)
            broj += 1
            try:
                with open(putanja, "r", encoding="utf-8") as f:
                    izvor = f.read()
                ast.parse(izvor, filename=putanja)
            except SyntaxError as e:
                greska(
                    f"Sintaksna greska u {os.path.relpath(putanja, koren)}: "
                    f"linija {e.lineno} - {e.msg}"
                )
    ok(f"Sintaksa proverena na {broj} .py fajlova")


# ============================================================
# 2) assets/jezici/*.json - isti kljucevi i {parametri} na svim jezicima
# ============================================================

def _skupi_kljuceve(recnik, prefiks=""):
    kljucevi = set()
    for k, v in recnik.items():
        if k == "_meta":
            continue
        putanja = f"{prefiks}{k}"
        if isinstance(v, dict):
            kljucevi |= _skupi_kljuceve(v, putanja + ".")
        else:
            kljucevi.add(putanja)
    return kljucevi


def _skupi_parametre(recnik, prefiks=""):
    parametri = {}
    for k, v in recnik.items():
        if k == "_meta":
            continue
        putanja = f"{prefiks}{k}"
        if isinstance(v, dict):
            parametri.update(_skupi_parametre(v, putanja + "."))
        elif isinstance(v, str):
            parametri[putanja] = set(re.findall(r"\{(\w+)\}", v))
        elif isinstance(v, list):
            pass
    return parametri


def proveri_jezike_json(koren):
    lang_dir = os.path.join(koren, "assets", "jezici")
    if not os.path.isdir(lang_dir):
        greska(f"Ne postoji folder {lang_dir}")
        return set()

    fajlovi = sorted(
        f for f in os.listdir(lang_dir)
        if f.endswith(".json") and f != "lang_meta.json"
    )
    if not fajlovi:
        greska("Nema nijednog JSON fajla u assets/jezici")
        return set()

    podaci = {}
    for naziv in fajlovi:
        lang = naziv[:-5]
        putanja = os.path.join(lang_dir, naziv)
        try:
            with open(putanja, "r", encoding="utf-8") as f:
                podaci[lang] = json.load(f)
        except json.JSONDecodeError as e:
            greska(f"{naziv} nije ispravan JSON: {e}")

    if "sr" in podaci:
        osnova = "sr"
    elif "en" in podaci:
        osnova = "en"
    else:
        osnova = sorted(podaci)[0]

    osnovni_kljucevi = _skupi_kljuceve(podaci[osnova])
    osnovni_param = _skupi_parametre(podaci[osnova])

    for lang, sadrzaj in podaci.items():
        if lang == osnova:
            continue

        kljucevi = _skupi_kljuceve(sadrzaj)
        nedostaje = osnovni_kljucevi - kljucevi
        visak = kljucevi - osnovni_kljucevi

        if nedostaje:
            upozorenje(
                f"{lang}.json: nedostaje prevod za {len(nedostaje)} kljuc(eva) "
                f"koje '{osnova}.json' ima (prikazace se na srpskom): "
                f"{', '.join(sorted(nedostaje)[:8])}"
                + (" ..." if len(nedostaje) > 8 else "")
            )
        if visak:
            upozorenje(
                f"{lang}.json: ima kljuceve kojih nema u '{osnova}.json' "
                f"(nije opasno, samo neiskorisceno): "
                f"{', '.join(sorted(visak)[:8])}"
                + (" ..." if len(visak) > 8 else "")
            )

        parametri = _skupi_parametre(sadrzaj)
        for kljuc, ocekivano in osnovni_param.items():
            stvarno = parametri.get(kljuc)
            if stvarno is not None and stvarno != ocekivano:
                upozorenje(
                    f"{lang}.json['{kljuc}']: {{parametri}} se ne poklapaju "
                    f"sa '{osnova}.json' (ocekivano {sorted(ocekivano)}, "
                    f"nadjeno {sorted(stvarno)}) - taj deo teksta ce ostati "
                    f"neupotpunjen na ekranu"
                )

    ok(f"assets/jezici: {len(podaci)} jezika ({', '.join(sorted(podaci))}), "
       f"provereno prema '{osnova}.json'")

    return set(podaci)


# ============================================================
# 3) servisi/izvoz_tekstovi.py i servisi/uputstvo_tekstovi.py -
#    ucitavaju se direktno (ne zavise od Kivy-a), pa se proveravaju
#    isto kao i JSON jezici.
# ============================================================

def _ucitaj_modul(koren, relativna_putanja, ime_modula):
    putanja = os.path.join(koren, relativna_putanja)
    if not os.path.isfile(putanja):
        greska(f"Ne postoji fajl {relativna_putanja}")
        return None

    import importlib.util
    spec = importlib.util.spec_from_file_location(ime_modula, putanja)
    modul = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(modul)
    except Exception as e:
        greska(f"{relativna_putanja} ne moze da se ucita: {e}")
        return None
    return modul


def proveri_izvoz_tekstove(koren):
    modul = _ucitaj_modul(
        koren, os.path.join("servisi", "izvoz_tekstovi.py"), "provera_izvoz"
    )
    if modul is None or not hasattr(modul, "TEKSTOVI"):
        greska("servisi/izvoz_tekstovi.py nema recnik TEKSTOVI")
        return set()

    tekstovi = modul.TEKSTOVI
    osnova = "sr" if "sr" in tekstovi else sorted(tekstovi)[0]
    osnovni_kljucevi = set(tekstovi[osnova].keys())

    def parametri_iz(recnik):
        out = {}
        for k, v in recnik.items():
            if isinstance(v, str):
                out[k] = set(re.findall(r"\{(\w+)\}", v))
        return out

    osnovni_param = parametri_iz(tekstovi[osnova])

    for lang, recnik in tekstovi.items():
        if lang == osnova:
            continue
        kljucevi = set(recnik.keys())
        nedostaje = osnovni_kljucevi - kljucevi
        if nedostaje:
            upozorenje(
                f"izvoz_tekstovi.py['{lang}']: nedostaje prevod za "
                f"{', '.join(sorted(nedostaje)[:8])} (pašce nazad na srpski)"
            )
        param = parametri_iz(recnik)
        for k, ocekivano in osnovni_param.items():
            if k in param and param[k] != ocekivano:
                upozorenje(
                    f"izvoz_tekstovi.py['{lang}']['{k}']: {{parametri}} se "
                    f"ne poklapaju (ocekivano {sorted(ocekivano)}, "
                    f"nadjeno {sorted(param[k])})"
                )

    ok(f"servisi/izvoz_tekstovi.py: {len(tekstovi)} jezika "
       f"({', '.join(sorted(tekstovi))})")

    return set(tekstovi)


def proveri_uputstvo_tekstove(koren):
    modul = _ucitaj_modul(
        koren, os.path.join("servisi", "uputstvo_tekstovi.py"), "provera_uputstvo"
    )
    if modul is None or not hasattr(modul, "SADRZAJ"):
        greska("servisi/uputstvo_tekstovi.py nema recnik SADRZAJ")
        return set()

    sadrzaj = modul.SADRZAJ
    podnaslov = getattr(modul, "PODNASLOV", {})

    osnova = "sr" if "sr" in sadrzaj else sorted(sadrzaj)[0]
    osnovne_sekcije = sadrzaj[osnova]

    for lang, sekcije in sadrzaj.items():
        if lang == osnova:
            continue
        if len(sekcije) != len(osnovne_sekcije):
            greska(
                f"uputstvo_tekstovi.py['{lang}']: ima {len(sekcije)} sekcija, "
                f"a '{osnova}' ima {len(osnovne_sekcije)}"
            )
            continue
        for i, ((_, pasusi_osn), (_, pasusi)) in enumerate(
            zip(osnovne_sekcije, sekcije)
        ):
            if len(pasusi) != len(pasusi_osn):
                greska(
                    f"uputstvo_tekstovi.py['{lang}'] sekcija {i + 1}: "
                    f"{len(pasusi)} pasusa, a '{osnova}' ima {len(pasusi_osn)}"
                )

    nedostaje_podnaslov = set(sadrzaj) - set(podnaslov)
    if nedostaje_podnaslov:
        upozorenje(
            f"uputstvo_tekstovi.py: PODNASLOV nema unos za: "
            f"{', '.join(sorted(nedostaje_podnaslov))}"
        )

    ok(f"servisi/uputstvo_tekstovi.py: {len(sadrzaj)} jezika "
       f"({', '.join(sorted(sadrzaj))}), {len(osnovne_sekcije)} sekcija")

    return set(sadrzaj)


# ============================================================
# 4) Da li SVAKI jezik iz assets/jezici ima i dugme u ekran_jezici.py?
#    (ovo je tacno bug koji smo imali - jezik dodat u JSON, a dugme
#    zaboravljeno)
# ============================================================

def proveri_dugmad_jezika(koren, jezici_json):
    putanja = os.path.join(koren, "ekrani", "ekran_jezici.py")
    if not os.path.isfile(putanja):
        greska("Ne postoji ekrani/ekran_jezici.py")
        return

    with open(putanja, "r", encoding="utf-8") as f:
        izvor = f.read()

    nedostaje = []
    for lang in sorted(jezici_json):
        # Trazi npr. promeni_jezici("pl") ili lang_code == "pl"
        if f'"{lang}"' not in izvor:
            nedostaje.append(lang)

    if nedostaje:
        greska(
            f"ekrani/ekran_jezici.py: nema dugme/granu za jezik(e): "
            f"{', '.join(nedostaje)} (postoje u assets/jezici, ali ih "
            f"ekran_jezici.py uopste ne pominje)"
        )
    else:
        ok(f"ekrani/ekran_jezici.py pominje sve jezike iz assets/jezici "
           f"({len(jezici_json)})")


# ============================================================
# GLAVNI TOK
# ============================================================

def main():
    koren = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, koren)

    print("== 1) Sintaksa svih .py fajlova ==")
    proveri_sintaksu(koren)

    print("\n== 2) Jezici (assets/jezici/*.json) ==")
    jezici_json = proveri_jezike_json(koren)

    print("\n== 3) Tekstovi za PDF/Excel (servisi/izvoz_tekstovi.py) ==")
    jezici_izvoz = proveri_izvoz_tekstove(koren)

    print("\n== 4) Tekstovi za uputstvo (servisi/uputstvo_tekstovi.py) ==")
    jezici_uputstvo = proveri_uputstvo_tekstove(koren)

    print("\n== 5) Dugmad za jezike (ekrani/ekran_jezici.py) ==")
    if jezici_json:
        proveri_dugmad_jezika(koren, jezici_json)

    print("\n== 6) Isti jezici svuda? ==")
    if jezici_json and jezici_izvoz and jezici_json != jezici_izvoz:
        greska(
            "Jezici u assets/jezici se ne poklapaju sa jezicima u "
            f"izvoz_tekstovi.py.\n   assets/jezici: {sorted(jezici_json)}\n"
            f"   izvoz_tekstovi.py: {sorted(jezici_izvoz)}"
        )
    if jezici_json and jezici_uputstvo and jezici_json != jezici_uputstvo:
        greska(
            "Jezici u assets/jezici se ne poklapaju sa jezicima u "
            f"uputstvo_tekstovi.py.\n   assets/jezici: {sorted(jezici_json)}\n"
            f"   uputstvo_tekstovi.py: {sorted(jezici_uputstvo)}"
        )
    if not GRESKE:
        ok("Isti skup jezika svuda")

    print("\n" + "=" * 60)
    if UPOZORENJA:
        print(f"⚠️  {len(UPOZORENJA)} upozorenje(a) - nedostaju pojedinacni "
              f"prevodi, ali aplikacija radi (pada nazad na srpski). "
              f"Nije hitno, ali vredi jednom prevesti.")
    if GRESKE:
        print(f"❌ Pronadjeno {len(GRESKE)} ozbiljan(ih) problem(a) - "
              f"pogledaj crvene redove iznad. Build je zaustavljen.")
        sys.exit(1)
    else:
        print("✅ Sve provere prosle. Build moze da krene.")
        sys.exit(0)


if __name__ == "__main__":
    main()
