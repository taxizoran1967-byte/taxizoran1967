"""
servisi/gps_logika.py
Cista logika za obradu GPS tacaka - NEMA Kivy zavisnosti namerno, jer
ovo koristi i glavna app (ekrani/ekran_gps_voznja.py) I pozadinski
servis (gpstracker.py, koji se pokrece kao POSEBAN Python proces bez
Kivy/App konteksta). Drzanje ove logike na jednom mestu garantuje da
oba mesta racunaju kilometrazu/filtriraju GPS greske NA POTPUNO ISTI
NACIN.
"""

import os
import json


MIN_TACNOST_M = 50       # ignorisi GPS tacke losije preciznosti od ovoga (metri)
MIN_POMERAJ_KM = 0.01    # ignorisi mikro-skokove manje od 10m (GPS sum)
MAX_BRZINA_KMH = 180     # ignorisi nerealne skokove (losa GPS tacka)


def haversine_km(lat1, lon1, lat2, lon2):
    """Racuna udaljenost izmedju dve GPS tacke (u kilometrima) preko
    haversine formule (uzima u obzir zakrivljenost Zemlje)."""
    import math
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class AktivnaVoznjaState:
    """Cuva stanje trenutno aktivne GPS voznje u fajl, da se ne
    izgubi ako se app (ili pozadinski servis) ugasi usred voznje.
    Fajl je ISTI za glavnu app i za pozadinski servis (oba pisu/citaju
    <user_data_dir>/aktivna_voznja.json - vidi gpstracker.py za
    objasnjenje zasto je to bezbedno)."""

    def __init__(self):
        self.aktivna = False
        self.pocetak_vreme = None
        self.pocetak_lat = None
        self.pocetak_lon = None
        self.pocetak_adresa = ""
        self.zadnja_lat = None
        self.zadnja_lon = None
        self.zadnje_vreme = None  # time.time() kad je zadnja_lat/lon primljena
        self.km = 0.0

    def _putanja(self, user_data_dir):
        return os.path.join(user_data_dir, "aktivna_voznja.json")

    def ucitaj(self, user_data_dir):
        try:
            with open(self._putanja(user_data_dir), "r", encoding="utf-8") as f:
                podaci = json.load(f)
            self.aktivna = podaci.get("aktivna", False)
            self.pocetak_vreme = podaci.get("pocetak_vreme")
            self.pocetak_lat = podaci.get("pocetak_lat")
            self.pocetak_lon = podaci.get("pocetak_lon")
            self.pocetak_adresa = podaci.get("pocetak_adresa", "")
            self.zadnja_lat = podaci.get("zadnja_lat")
            self.zadnja_lon = podaci.get("zadnja_lon")
            self.zadnje_vreme = podaci.get("zadnje_vreme")
            self.km = podaci.get("km", 0.0)
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            pass

    def sacuvaj(self, user_data_dir):
        podaci = {
            "aktivna": self.aktivna,
            "pocetak_vreme": self.pocetak_vreme,
            "pocetak_lat": self.pocetak_lat,
            "pocetak_lon": self.pocetak_lon,
            "pocetak_adresa": self.pocetak_adresa,
            "zadnja_lat": self.zadnja_lat,
            "zadnja_lon": self.zadnja_lon,
            "zadnje_vreme": self.zadnje_vreme,
            "km": self.km,
        }
        with open(self._putanja(user_data_dir), "w", encoding="utf-8") as f:
            json.dump(podaci, f, ensure_ascii=False, indent=2)

    def resetuj(self, user_data_dir):
        self.__init__()
        self.sacuvaj(user_data_dir)


def obradi_tacku(aktivna_voznja, user_data_dir, lat, lon, tacnost, vreme_sada):
    """Obradjuje jednu novu GPS tacku - filtrira lose precizne skokove
    i nerealne brzine, pa azurira kilometrazu u aktivna_voznja i
    ODMAH je cuva na disk. Vraca (prihvaceno: bool, razlog: str) -
    razlog objasnjava zasto je tacka odbijena, korisno za prikaz u UI.

    Ovo je JEDINO mesto gde se ova logika racuna - i glavna app i
    pozadinski servis pozivaju TACNO ovu funkciju, da ne bi doslo do
    razmimoilazenja (npr. da servis koristi stariji/drugaciji filter
    od glavne app-e).
    """
    if aktivna_voznja.pocetak_lat is None:
        # prva tacka - pocetak voznje, ne filtriramo je po preciznosti
        aktivna_voznja.pocetak_lat = lat
        aktivna_voznja.pocetak_lon = lon
        aktivna_voznja.zadnja_lat = lat
        aktivna_voznja.zadnja_lon = lon
        aktivna_voznja.zadnje_vreme = vreme_sada
        aktivna_voznja.sacuvaj(user_data_dir)
        return True, "pocetna tacka"

    if tacnost and tacnost > MIN_TACNOST_M:
        return False, f"slab signal (+/-{tacnost:.0f}m)"

    udaljenost = haversine_km(
        aktivna_voznja.zadnja_lat, aktivna_voznja.zadnja_lon, lat, lon
    )

    if udaljenost < MIN_POMERAJ_KM:
        return False, "mikro-sum"

    proteklo_sec = vreme_sada - (aktivna_voznja.zadnje_vreme or vreme_sada)
    proteklo_sec = max(proteklo_sec, 1.0)

    brzina_kmh = udaljenost / (proteklo_sec / 3600.0)
    if brzina_kmh > MAX_BRZINA_KMH:
        return False, "nerealan skok (losa GPS tacka)"

    aktivna_voznja.km += udaljenost
    aktivna_voznja.zadnja_lat = lat
    aktivna_voznja.zadnja_lon = lon
    aktivna_voznja.zadnje_vreme = vreme_sada
    aktivna_voznja.sacuvaj(user_data_dir)
    return True, "prihvaceno"
