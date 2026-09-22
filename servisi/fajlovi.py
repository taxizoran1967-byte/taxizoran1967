"""
fajlovi.py - Bezbedan upis i citanje JSON fajlova

Problem: kad aplikacija upisuje fajl i telefon se ugasi/aplikacija pukne
usred upisa, fajl ostane pola napisan i podaci se izgube.

Resenje (ovde):
  1. sacuvaj_json() - prvo upise u privremeni fajl (.tmp), proveri da je
     upis stigao na disk, pa ga JEDNIM potezom zameni za pravi fajl.
     Pravi fajl je uvek ili ceo stari ili ceo novi - nikad pola.
  2. Pre zamene, prethodna ispravna verzija se cuva kao .bak.
  3. ucitaj_json() - ako je pravi fajl ipak ostecen, vraca podatke iz .bak.

Ne zavisi od Kivy-a (moze da se testira bez telefona).
"""

import json
import os
import shutil


def _je_ispravan_json(putanja):
    """True ako fajl postoji i moze da se procita kao JSON."""
    try:
        with open(putanja, "r", encoding="utf-8") as f:
            json.load(f)
        return True
    except (OSError, ValueError):
        return False


def sacuvaj_json(putanja, podaci, indent=2):
    """Bezbedno (atomski) upisuje 'podaci' kao JSON u fajl 'putanja'."""
    tmp = putanja + ".tmp"
    bak = putanja + ".bak"

    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(podaci, f, ensure_ascii=False, indent=indent)
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass

        # Prethodna ispravna verzija -> .bak (samo ako je zaista ispravna,
        # da losa verzija ne pregazi dobru rezervnu kopiju)
        if os.path.exists(putanja) and _je_ispravan_json(putanja):
            try:
                shutil.copyfile(putanja, bak)
            except OSError:
                pass

        # Zamena jednim potezom
        os.replace(tmp, putanja)

    except Exception:
        # Ne ostavljaj privremeni fajl da se gomila
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
        raise


def ucitaj_json(putanja):
    """Ucitava JSON iz 'putanja'.

    - Ako fajl ne postoji: baca FileNotFoundError (npr. prvo pokretanje).
    - Ako je fajl ostecen: pokusava rezervnu kopiju (.bak). Ako ni ona ne
      valja, baca ValueError.
    """
    try:
        with open(putanja, "r", encoding="utf-8") as f:
            return json.load(f)

    except FileNotFoundError:
        raise

    except ValueError as greska:
        bak = putanja + ".bak"

        if os.path.exists(bak):
            try:
                with open(bak, "r", encoding="utf-8") as f:
                    podaci = json.load(f)
                print(f"⚠️  {os.path.basename(putanja)} ostecen - "
                      f"vracen iz rezervne kopije.")
                return podaci
            except (OSError, ValueError):
                pass

        raise greska
