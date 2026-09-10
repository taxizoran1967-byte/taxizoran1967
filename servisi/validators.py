"""
validators.py - Validacija ulaza pre nego što uđe u bazu ili API

Obezbedi da aplikacija ne pada na lošim vrednostima od korisnika.
Sve funkcije vraćaju: (uspeh: bool, vrednost, poruka_greške: str)
"""


def validiraj_kilometrazu(km_str):
    """
    Provera da li je km ispravna vrednost.
    
    Args:
        km_str (str): Uneta kilometraža (npr. "8.5" ili "8,5")
    
    Returns:
        tuple: (uspeh, vrednost, poruka_greške)
            - uspeh (bool): True ako je validna
            - vrednost (float): Parsirana kilometraža
            - poruka_greške (str): None ako OK, inače poruka
    
    Primeri:
        >>> validiraj_kilometrazu("8.5")
        (True, 8.5, None)
        >>> validiraj_kilometrazu("0")
        (False, 0, "Kilometraža mora biti > 0")
        >>> validiraj_kilometrazu("1000")
        (False, 0, "Kilometraža čini se prevelika (max 500)")
    """
    try:
        km = float(km_str.replace(",", "."))
    except (ValueError, AttributeError, TypeError):
        return False, 0, "Kilometraža mora biti broj (npr. 8.5)"
    
    if km <= 0:
        return False, 0, "Kilometraža mora biti veća od 0"
    
    if km > 500:
        return False, 0, "Kilometraža čini se prevelika (max 500 km)"
    
    return True, km, None


def validiraj_cenu(cena_str):
    """
    Provera da li je cena ispravna vrednost.
    
    Args:
        cena_str (str): Uneta cena (npr. "250.50" ili "250,50")
    
    Returns:
        tuple: (uspeh, vrednost, poruka_greške)
    
    Primeri:
        >>> validiraj_cenu("250.50")
        (True, 250.5, None)
        >>> validiraj_cenu("-50")
        (False, 0, "Cena ne može biti negativna")
    """
    try:
        cena = float(cena_str.replace(",", "."))
    except (ValueError, AttributeError, TypeError):
        return False, 0, "Cena mora biti broj"
    
    if cena < 0:
        return False, 0, "Cena ne može biti negativna"
    
    if cena > 100000:
        return False, 0, "Cena čini se prevelika (max 100.000 RSD)"
    
    return True, cena, None


def validiraj_adresu(adresa):
    """
    Provera da li je adresa ispravna - ne sme biti previše dugačka ili prazna.
    
    Args:
        adresa (str): Adresa
    
    Returns:
        tuple: (uspeh, poruka_greške)
    
    Primeri:
        >>> validiraj_adresu("Novi Beograd")
        (True, None)
        >>> validiraj_adresu("")
        (True, None)  # Adresa je opciona
    """
    if not isinstance(adresa, str):
        return False, "Adresa mora biti tekst"
    
    if len(adresa) > 500:
        return False, "Adresa je previše dugačka (max 500 karaktera)"
    
    return True, None


def validiraj_napomenu(napomena):
    """
    Provera napomene - opciono polje, ali ako postoji mora biti razumne dužine.
    
    Args:
        napomena (str): Napomena
    
    Returns:
        tuple: (uspeh, poruka_greške)
    """
    if not isinstance(napomena, str):
        return False, "Napomena mora biti tekst"
    
    if len(napomena) > 1000:
        return False, "Napomena je previše dugačka (max 1000 karaktera)"
    
    return True, None


def validiraj_tarifu(tarifa_naziv, dostupne_tarife):
    """
    Provera da li je izabrana tarifa validna.
    
    Args:
        tarifa_naziv (str): Naziv tarife
        dostupne_tarife (dict): Dostupne tarife {naziv: cena_po_km}
    
    Returns:
        tuple: (uspeh, poruka_greške)
    
    Primeri:
        >>> tarife = {"Osnovna (07-22h)": 80}
        >>> validiraj_tarifu("Osnovna (07-22h)", tarife)
        (True, None)
        >>> validiraj_tarifu("Nepostojeća", tarife)
        (False, "Tarifa nije pronađena")
    """
    if not tarifa_naziv or tarifa_naziv not in dostupne_tarife:
        return False, "Tarifa nije pronađena. Raspoložive: " + ", ".join(dostupne_tarife.keys())
    
    return True, None
