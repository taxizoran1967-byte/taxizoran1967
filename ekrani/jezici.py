"""
jezici.py - Sistem za lokalizaciju (i18n)

Učitava tekstove iz JSON fajlova po izabranom jeziku.
Fallback na srpski ako neki ključ nedostaje.
Podržava dinamičku promenu jezika bez restarta.

Primer:
    from servisi.jezici import _t, set_language
    
    tekst = _t("kalkulator.unesi_km")  # "Unesi kilometrazu da vidis cenu"
    tekst_sa_param = _t("profil.reg_istice_za", dani=30)  # "Registracija: istice za 30 dana"
    
    set_language("en")  # Promeni na engleski
    tekst = _t("kalkulator.unesi_km")  # "Enter kilometers to see price"
"""

import json
import os
from pathlib import Path

# Globalne varijable
_CURRENT_LANG = "en"  # Podrazumevani jezik (glavni, prikazuje se pri prvoj instalaciji)
_TRANSLATIONS = {}    # Učitani tekstovi { "sr": {...}, "en": {...} }
_AVAILABLE_LANGS = {} # Dostupni jezici


def _init_languages():
    """Učitava sve dostupne jezike iz assets/jezici/"""
    global _TRANSLATIONS, _AVAILABLE_LANGS
    
    # Pronađi assets folder
    try:
        app_root = Path(__file__).parent.parent
        lang_dir = app_root / "assets" / "jezici"
    except Exception:
        print("⚠️  Greška pri pronalaženju assets foldera")
        return
    
    if not lang_dir.exists():
        print(f"⚠️  Jezički folder ne postoji: {lang_dir}")
        return
    
    # Učitaj sve .json fajlove
    for json_file in sorted(lang_dir.glob("*.json")):
        lang_code = json_file.stem  # "sr", "en", itd
        
        if lang_code == "lang_meta":
            continue  # Preskoči metadata fajl
        
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                _TRANSLATIONS[lang_code] = json.load(f)
            
            _AVAILABLE_LANGS[lang_code] = {
                "code": lang_code,
                "name": _TRANSLATIONS[lang_code].get("_meta", {}).get("name", lang_code.upper()),
            }
            print(f"✅ Učitan jezik: {lang_code}")
        except Exception as e:
            print(f"❌ Greška pri učitavanju {lang_code}: {e}")


def set_language(lang_code):
    """
    Postavi aktivni jezik - korisnik klikne na jezici u podesavanjima
    
    Args:
        lang_code (str): Kod jezika ("sr", "en", itd)
    """
    global _CURRENT_LANG
    
    if lang_code not in _TRANSLATIONS:
        print(f"⚠️  Jezik '{lang_code}' ne postoji. Korišćenje engleskog.")
        _CURRENT_LANG = "en"
    else:
        _CURRENT_LANG = lang_code
        print(f"✅ Jezik promenjen na: {lang_code}")
    
    # Čuvaj izbor u fajl
    _save_language_preference(lang_code)


def get_current_language():
    """Vrati trenutni aktivni jezik"""
    return _CURRENT_LANG


def get_available_languages():
    """Vrati listu dostupnih jezika kao dict-e"""
    return _AVAILABLE_LANGS


def _t(key_path, **kwargs):
    """
    GLAVNA FUNKCIJA - Preuzmi tekst na trenutnom jeziku
    
    Args:
        key_path (str): Putanja do teksta, npr "kalkulator.unesi_km"
        **kwargs: Parametri za zamenu u tekstu, npr dani=30, cena="250 RSD"
    
    Returns:
        str: Tekst na trenutnom jeziku
    
    Primeri:
        >>> _t("kalkulator.unesi_km")  
        'Unesi kilometrazu da vidis cenu'
        
        >>> _t("profil.reg_istice_za", dani=30)
        'Registracija: istice za 30 dana'
        
        >>> set_language("en")
        >>> _t("kalkulator.unesi_km")
        'Enter kilometers to see price'
    """
    
    # Razdvoji putanju: "kalkulator.unesi_km" → ["kalkulator", "unesi_km"]
    keys = key_path.split(".")
    
    # Traži u trenutnom jeziku
    text = _get_nested(
        _TRANSLATIONS.get(_CURRENT_LANG, {}), 
        keys
    )
    
    # Ako ne nađeš u trenutnom jeziku → fallback na srpski
    if text is None and _CURRENT_LANG != "sr":
        text = _get_nested(
            _TRANSLATIONS.get("sr", {}), 
            keys
        )
    
    # Ako i dalje nema → vrati sam ključ (za debug)
    if text is None:
        print(f"⚠️  Ključ ne postoji: {key_path}")
        return key_path
    
    # Zameni parametre ako su prosleđeni
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError as e:
            print(f"⚠️  Nedostaje parametar u '{key_path}': {e}")
    
    return text


def _get_nested(d, keys):
    """
    Traži vrednost u ugneždenom rečniku (dictionary)
    
    Args:
        d (dict): Rečnik za pretragu
        keys (list): Lista ključeva za prolazak kroz nivo po nivo
    
    Returns:
        str or list or None: Vrednost ako je string ili lista (npr.
        nazivi dana/meseci), inače None
    """
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key)
        else:
            return None
    return d if isinstance(d, (str, list)) else None


# ============================================================
# PREVOD NAZIVA TARIFA I SACUVANIH TEKSTOVA (samo za PRIKAZ)
# ============================================================
#
# Nazivi tarifa se u bazi voznji i u cene.json cuvaju UVEK na srpskom
# (npr. "Osnovna (07-22h)") - to je interni "kljuc" i on se NE menja,
# da bi stare voznje i cene i dalje radile. Ovde se ti nazivi samo
# PREVODE kad se prikazuju korisniku.

_NAZIVI_TARIFA = {
    "sr": {
        "Osnovna (07-22h)": "Osnovna (07-22h)",
        "Nocna (22-07h)": "Nocna (22-07h)",
        "Vikend": "Vikend",
        "Aerodromski transfer": "Aerodromski transfer",
    },
    "en": {
        "Osnovna (07-22h)": "Standard (07-22h)",
        "Nocna (22-07h)": "Night (22-07h)",
        "Vikend": "Weekend",
        "Aerodromski transfer": "Airport transfer",
    },
    "it": {
        "Osnovna (07-22h)": "Standard (07-22h)",
        "Nocna (22-07h)": "Notturna (22-07h)",
        "Vikend": "Weekend",
        "Aerodromski transfer": "Transfer aeroporto",
    },
    "fr": {
        "Osnovna (07-22h)": "Standard (07-22h)",
        "Nocna (22-07h)": "Nuit (22-07h)",
        "Vikend": "Week-end",
        "Aerodromski transfer": "Transfert aéroport",
    },
    "de": {
        "Osnovna (07-22h)": "Standard (07-22 Uhr)",
        "Nocna (22-07h)": "Nacht (22-07 Uhr)",
        "Vikend": "Wochenende",
        "Aerodromski transfer": "Flughafentransfer",
    },
    "ru": {
        "Osnovna (07-22h)": "Стандартный (07-22 ч)",
        "Nocna (22-07h)": "Ночной (22-07 ч)",
        "Vikend": "Выходные",
        "Aerodromski transfer": "Трансфер в аэропорт",
    },
}


def prevedi_tarifu(naziv):
    """Vraca naziv tarife na TRENUTNOM jeziku. 'naziv' je interni
    (srpski) naziv iz baze ili iz cene.json. Ako za taj jezik ili naziv
    nema prevoda, vraca naziv nepromenjen."""
    return _NAZIVI_TARIFA.get(_CURRENT_LANG, {}).get(naziv, naziv)


def tarifa_iz_prikaza(prikaz):
    """Obrnuto od prevedi_tarifu: iz prevedenog naziva (kako pise u
    Spinner-u na ekranu) vraca interni srpski naziv tarife. Trazi u
    prevodima SVIH jezika, pa radi ispravno i odmah posle promene
    jezika, dok Spinner jos prikazuje naziv na prethodnom jeziku."""
    for tabela in _NAZIVI_TARIFA.values():
        for interni_naziv, prevod in tabela.items():
            if prevod == prikaz:
                return interni_naziv
    return prikaz


def prevedi_sacuvano(tekst, key_path):
    """Za tekstove koje je app sama upisala u bazu na jeziku koji je
    tad bio izabran (npr. 'Adresa nije dostupna'): ako je 'tekst'
    identican prevodu kljuca 'key_path' na BILO KOM jeziku, vraca prevod
    tog kljuca na TRENUTNOM jeziku. Inace vraca tekst nepromenjen."""
    if not tekst:
        return tekst
    keys = key_path.split(".")
    for jezik_recnik in _TRANSLATIONS.values():
        if _get_nested(jezik_recnik, keys) == tekst:
            return _t(key_path)
    return tekst


def _save_language_preference(lang_code):
    """
    Čuva izbor jezika u JSON fajl u app data direktorijumu
    
    Args:
        lang_code (str): Kod jezika koji se čuva
    """
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app is None:
            return
        
        pref_file = os.path.join(app.user_data_dir, "language.json")
        
        with open(pref_file, "w", encoding="utf-8") as f:
            json.dump({"language": lang_code}, f, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️  Greška pri čuvanju jezika: {e}")


def _load_language_preference():
    """
    Učitaj prethodno izbran jezik iz JSON-a
    Poziva se pri pokretanju app-e
    """
    global _CURRENT_LANG
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app is None:
            return
        
        pref_file = os.path.join(app.user_data_dir, "language.json")
        
        if os.path.exists(pref_file):
            with open(pref_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                lang = data.get("language", "en")
                if lang in _TRANSLATIONS:
                    _CURRENT_LANG = lang
                    print(f"✅ Učitan sačuvan jezik: {lang}")
    except Exception as e:
        print(f"⚠️  Greška pri učitavanju jezika: {e}")


# Javni alias - main.py poziva ovo pri pokretanju aplikacije da vrati
# prethodno izabran jezik (funkcija iznad je zadrzana zbog postojecih
# poziva/dokumentacije unutar ovog fajla).
load_language_preference = _load_language_preference


# Inicijalizuj pri prvi import
_init_languages()
