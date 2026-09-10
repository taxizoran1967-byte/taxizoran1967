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
_CURRENT_LANG = "sr"  # Podrazumevani jezik
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
        print(f"⚠️  Jezik '{lang_code}' ne postoji. Korišćenje srpskog.")
        _CURRENT_LANG = "sr"
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
        str or None: Vrednost ako je string, inače None
    """
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key)
        else:
            return None
    return d if isinstance(d, str) else None


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
                lang = data.get("language", "sr")
                if lang in _TRANSLATIONS:
                    _CURRENT_LANG = lang
                    print(f"✅ Učitan sačuvan jezik: {lang}")
    except Exception as e:
        print(f"⚠️  Greška pri učitavanju jezika: {e}")


# Inicijalizuj pri prvi import
_init_languages()
