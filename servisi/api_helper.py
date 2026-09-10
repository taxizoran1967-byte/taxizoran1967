"""
api_helper.py - Sigurni API pozivi sa error handling-om

Spečava da aplikacija padne kada nema interneta ili API failuje.
Svi pozivi imaju timeout i fallback opcije.
"""

import urllib.request
import urllib.error
import json
import ssl

# SSL kontekst za HTTPS zahteve
try:
    import certifi
    SSL_KONTEKST = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_KONTEKST = ssl.create_default_context()


def poveži_google_geocoding(google_kljuc, lat, lon, timeout=5):
    """
    Pronalazi adresu od GPS koordinata pomoću Google Geocoding API.
    
    Ako Google API failuje ili nema ključa, koristi OpenStreetMap (besplatan fallback).
    
    Args:
        google_kljuc (str): Google Geocoding API ključ (opciono)
        lat (float): Geografska širina
        lon (float): Geografska dužina
        timeout (int): Timeout u sekundama
    
    Returns:
        tuple: (uspeh, adresa, poruka_greške)
            - uspeh (bool): True ako je pronađena adresa
            - adresa (str): Pronađena adresa ili prazan string
            - poruka_greške (str): None ako OK, inače opis greške
    
    Primeri:
        >>> ok, addr, err = poveži_google_geocoding("", 44.8176, 20.4633)
        >>> print(addr)  # "Kneza Mihaila, Beograd..."
    """
    if google_kljuc:
        return _poveži_google_api(google_kljuc, lat, lon, timeout)
    else:
        return _poveži_osm(lat, lon, timeout)


def _poveži_google_api(google_kljuc, lat, lon, timeout):
    """
    Interni - pronalaženje adrese preko Google Geocoding API.
    """
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={google_kljuc}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "TaksiApp/1.0"}
        )
        
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_KONTEKST) as resp:
            podaci = json.loads(resp.read().decode("utf-8"))
        
        if podaci.get("results"):
            adresa = podaci["results"][0]["formatted_address"]
            return True, adresa, None
        else:
            # Google API nije pronašao, probaj OSM kao fallback
            return _poveži_osm(lat, lon, timeout)
    
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return False, "", "Google API ključ je nevalidan (403)"
        elif e.code == 400:
            return False, "", "Nevalidan GPS koordinat"
        else:
            return False, "", f"Google API greška: HTTP {e.code}"
    
    except urllib.error.URLError as e:
        # Nema interneta ili network greška
        return _poveži_osm(lat, lon, timeout)
    
    except json.JSONDecodeError:
        return False, "", "Google API vratio nevalidan JSON"
    
    except Exception as e:
        return False, "", f"Greška Google API: {str(e)}"


def _poveži_osm(lat, lon, timeout):
    """
    Fallback - pronalaženje adrese preko OpenStreetMap Nominatim servisa (besplatan).
    """
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "TaksiApp/1.0"}
        )
        
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_KONTEKST) as resp:
            podaci = json.loads(resp.read().decode("utf-8"))
        
        # Pokušaj da pronađeš ulicu (road), inače koristi bilo šta dostupno
        adresa_dict = podaci.get("address", {})
        adresa = adresa_dict.get("road") or adresa_dict.get("city") or "Nepoznata lokacija"
        
        return True, adresa, None
    
    except urllib.error.URLError as e:
        return False, "", "Nema interneta - ne mogu da pronađem adresu"
    
    except json.JSONDecodeError:
        return False, "", "OSM vratio nevalidan JSON"
    
    except Exception as e:
        return False, "", f"Greška OSM: {str(e)}"


def preuzmi_kurs_eur_rsd(timeout=8):
    """
    Preuzima EUR→RSD kurs sa besplatnog javnog API-ja.
    
    Args:
        timeout (int): Timeout u sekundama
    
    Returns:
        tuple: (uspeh, kurs, poruka_greške)
            - uspeh (bool): True ako je preuzet
            - kurs (float): EUR→RSD kurs (npr. 117.5)
            - poruka_greške (str): None ako OK
    
    Primeri:
        >>> ok, kurs, err = preuzmi_kurs_eur_rsd()
        >>> if ok:
        ...     print(f"1 EUR = {kurs} RSD")
    """
    try:
        url = "https://open.er-api.com/v6/latest/EUR"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "TaksiApp/1.0"}
        )
        
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_KONTEKST) as resp:
            podaci = json.loads(resp.read().decode("utf-8"))
        
        kurs = podaci.get("rates", {}).get("RSD")
        if not kurs:
            return False, 0, "RSD kurs nije pronađen u odgovoru API-ja"
        
        return True, float(kurs), None
    
    except urllib.error.URLError:
        return False, 0, "Nema interneta - ne mogu da preuzem kurs"
    
    except json.JSONDecodeError:
        return False, 0, "API vratio nevalidan JSON"
    
    except Exception as e:
        return False, 0, f"Greška pri preuzimanju kursa: {str(e)}"
