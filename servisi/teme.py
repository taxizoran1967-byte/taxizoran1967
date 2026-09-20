"""
teme.py - Teme boja (izgled aplikacije)

Ovde su definisane gotove teme boja, funkcija koja "pomera" boje
dugmadi i kartica ka izabranoj temi i tekstovi za ekran "Izgled" na
svim jezicima aplikacije. Ne zavisi od Kivy-a (moze da se testira
bez telefona).

Kako radi:
    Originalna boja dugmadi i kartica je plavo-ljubicasta (nijansa
    oko 0.63). Tema samo pomera tu nijansu (i malo saturaciju/svetlinu).
    Boje koje imaju drugo znacenje (zelena za "Sacuvaj", crvena za
    "Obrisi"...) se NE diraju.

    Parametri teme: [pomeraj_nijanse, mnozilac_saturacije,
                     dodatak_saturaciji, mnozilac_svetline]
"""

import colorsys

from servisi import jezici

# Boja dugmadi u originalnom izgledu (koristi se za preview u izboru teme)
BAZNA_DUGMAD = [0.36, 0.46, 0.64, 1.0]

# Samo boje ciji je hue u ovom opsegu (plavo-ljubicasto) se pomeraju
HUE_OD = 0.50
HUE_DO = 0.88

TEME = {
    "original": {
        "param": [0.0, 1.0, 0.0, 1.0],
        "pozadina": [0.04, 0.03, 0.09, 0.35],
        "akcent": [0.55, 0.65, 0.95, 1.0],
    },
    "okean": {
        "param": [-0.11, 1.2, 0.10, 1.0],
        "pozadina": [0.00, 0.06, 0.12, 0.42],
        "akcent": [0.30, 0.85, 0.95, 1.0],
    },
    "suma": {
        "param": [-0.25, 1.1, 0.10, 0.95],
        "pozadina": [0.02, 0.08, 0.04, 0.44],
        "akcent": [0.45, 0.90, 0.55, 1.0],
    },
    "zalazak": {
        "param": [-0.56, 1.3, 0.15, 1.15],
        "pozadina": [0.14, 0.05, 0.02, 0.44],
        "akcent": [1.00, 0.65, 0.30, 1.0],
    },
    "rubin": {
        "param": [0.35, 1.3, 0.12, 1.0],
        "pozadina": [0.12, 0.02, 0.04, 0.44],
        "akcent": [1.00, 0.40, 0.50, 1.0],
    },
    "kraljevska": {
        "param": [0.15, 1.15, 0.12, 1.0],
        "pozadina": [0.08, 0.02, 0.14, 0.44],
        "akcent": [0.80, 0.55, 1.00, 1.0],
    },
    "ponoc": {
        "param": [-0.51, 0.9, 0.10, 0.75],
        "pozadina": [0.00, 0.00, 0.00, 0.58],
        "akcent": [1.00, 0.82, 0.30, 1.0],
    },
}

# Redosled na ekranu
REDOSLED = [
    "original", "okean", "suma", "zalazak", "rubin", "kraljevska", "ponoc",
]

OSNOVNA_TEMA = "original"


def pomeri_boju(rgba, param):
    """Vraca [r, g, b, a] - boju pomerenu ka temi. Boje van
    plavo-ljubicastog opsega (zelena, crvena, siva...) ostaju iste."""
    try:
        pomeraj, mn_sat, dod_sat, mn_sv = param
        r, g, b = float(rgba[0]), float(rgba[1]), float(rgba[2])
        a = float(rgba[3]) if len(rgba) > 3 else 1.0

        h, s, v = colorsys.rgb_to_hsv(r, g, b)

        if HUE_OD <= h <= HUE_DO and s > 0.10:
            h = (h + pomeraj) % 1.0
            s = max(0.0, min(0.95, s * mn_sat + dod_sat))
            v = max(0.0, min(1.0, v * mn_sv))
            r, g, b = colorsys.hsv_to_rgb(h, s, v)

        return [r, g, b, a]
    except Exception:
        return list(rgba)


def boja_teme(tema_id):
    """Reprezentativna boja teme (za preview kartice u izboru)."""
    tema = TEME.get(tema_id, TEME[OSNOVNA_TEMA])
    return pomeri_boju(BAZNA_DUGMAD, tema["param"])


# ============================================================
# TEKSTOVI (ekran "Izgled") - svi jezici na jednom mestu
# ============================================================

SR = {
    "naslov": "Izgled aplikacije",
    "opis": "Izaberi temu boja - promena se odmah vidi u celoj aplikaciji.",
    "osnovna": "Osnovna tema",
    "t_original": "Osnovna",
    "t_okean": "Okean",
    "t_suma": "Suma",
    "t_zalazak": "Zalazak sunca",
    "t_rubin": "Rubin",
    "t_kraljevska": "Kraljevska",
    "t_ponoc": "Ponoc i zlato",
}

EN = {
    "naslov": "Appearance",
    "opis": "Choose a color theme - the change shows immediately across the whole app.",
    "osnovna": "Default theme",
    "t_original": "Original",
    "t_okean": "Ocean",
    "t_suma": "Forest",
    "t_zalazak": "Sunset",
    "t_rubin": "Ruby",
    "t_kraljevska": "Royal",
    "t_ponoc": "Midnight gold",
}

IT = {
    "naslov": "Aspetto",
    "opis": "Scegli un tema colore - la modifica si vede subito in tutta l'app.",
    "osnovna": "Tema base",
    "t_original": "Originale",
    "t_okean": "Oceano",
    "t_suma": "Foresta",
    "t_zalazak": "Tramonto",
    "t_rubin": "Rubino",
    "t_kraljevska": "Reale",
    "t_ponoc": "Mezzanotte e oro",
}

FR = {
    "naslov": "Apparence",
    "opis": "Choisissez un thème de couleurs - le changement s'applique aussitôt dans toute l'application.",
    "osnovna": "Thème de base",
    "t_original": "Original",
    "t_okean": "Océan",
    "t_suma": "Forêt",
    "t_zalazak": "Coucher de soleil",
    "t_rubin": "Rubis",
    "t_kraljevska": "Royal",
    "t_ponoc": "Minuit et or",
}

DE = {
    "naslov": "Erscheinungsbild",
    "opis": "Wählen Sie ein Farbthema - die Änderung wirkt sofort in der ganzen App.",
    "osnovna": "Standardthema",
    "t_original": "Original",
    "t_okean": "Ozean",
    "t_suma": "Wald",
    "t_zalazak": "Sonnenuntergang",
    "t_rubin": "Rubin",
    "t_kraljevska": "Königlich",
    "t_ponoc": "Mitternacht & Gold",
}

RU = {
    "naslov": "Внешний вид",
    "opis": "Выберите цветовую тему - изменения сразу применяются во всём приложении.",
    "osnovna": "Тема по умолчанию",
    "t_original": "Оригинал",
    "t_okean": "Океан",
    "t_suma": "Лес",
    "t_zalazak": "Закат",
    "t_rubin": "Рубин",
    "t_kraljevska": "Королевская",
    "t_ponoc": "Полночь и золото",
}

PL = {
    "naslov": "Wygląd",
    "opis": "Wybierz motyw kolorystyczny - zmiana od razu widoczna w całej aplikacji.",
    "osnovna": "Motyw domyślny",
    "t_original": "Oryginalny",
    "t_okean": "Ocean",
    "t_suma": "Las",
    "t_zalazak": "Zachód słońca",
    "t_rubin": "Rubin",
    "t_kraljevska": "Królewski",
    "t_ponoc": "Północ i złoto",
}

TR = {
    "naslov": "Görünüm",
    "opis": "Bir renk teması seçin - değişiklik uygulamanın tamamında hemen görünür.",
    "osnovna": "Varsayılan tema",
    "t_original": "Orijinal",
    "t_okean": "Okyanus",
    "t_suma": "Orman",
    "t_zalazak": "Gün batımı",
    "t_rubin": "Yakut",
    "t_kraljevska": "Kraliyet",
    "t_ponoc": "Gece yarısı ve altın",
}

ES = {
    "naslov": "Apariencia",
    "opis": "Elige un tema de color: el cambio se ve al instante en toda la aplicación.",
    "osnovna": "Tema base",
    "t_original": "Original",
    "t_okean": "Océano",
    "t_suma": "Bosque",
    "t_zalazak": "Atardecer",
    "t_rubin": "Rubí",
    "t_kraljevska": "Real",
    "t_ponoc": "Medianoche y oro",
}

TEKSTOVI = {
    "sr": SR,
    "en": EN,
    "it": IT,
    "fr": FR,
    "de": DE,
    "ru": RU,
    "pl": PL,
    "tr": TR,
    "es": ES,
}


def t(kljuc):
    """Tekst za dati kljuc na trenutnom jeziku (ako ga nema - srpski)."""
    tekst = TEKSTOVI.get(jezici.get_current_language(), {}).get(kljuc)
    if tekst is None:
        tekst = SR.get(kljuc, kljuc)
    return tekst


def naziv_teme(tema_id):
    """Prevedeni naziv teme na trenutnom jeziku."""
    return t("t_" + tema_id)
