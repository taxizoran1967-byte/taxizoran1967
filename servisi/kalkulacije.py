"""
kalkulacije.py - Ciste racunske funkcije (bez ikakve zavisnosti od
Kivy-a), da bi mogle da se testiraju nezavisno od cele aplikacije.

Ovde zivi "prava" matematika app-a: cena voznje i potrosnja goriva.
Ekrani (ekran_kalkulator.py) i main.py samo pozivaju ove funkcije -
sama logika racunanja je ovde, na jednom mestu, umesto da bude
kopirana na vise mesta (sto je bio slucaj ranije).

Testovi za ove funkcije su u tests/test_kalkulacije.py - mogu da se
pokrenu sa "python3 tests/test_kalkulacije.py" bez potrebe da se
instalira Kivy ili pokrene cela aplikacija.
"""


def izracunaj_cenu_voznje(km, cena_po_km, start_taksa):
    """Cena voznje = start taksa + predjeni kilometri * cena po km.

    >>> izracunaj_cenu_voznje(km=10, cena_po_km=80, start_taksa=150)
    950
    """
    return start_taksa + km * cena_po_km


def izracunaj_potrosnju_intervale(sve_stavke_goriva):
    """Racuna potrosnju goriva (l/100km) izmedju uzastopnih sipanja, na
    osnovu kilometraze sa pumpe (km_pumpe). Uzima se CELA istorija
    goriva (ne samo izabrani period) da bi se ispravno uparila dva
    uzastopna sipanja, cak i kad jedno od njih pada van perioda.

    Vraca listu recnika sa kljucevima: datum, km_predjeno, litara,
    potrosnja (l/100km), cena. 'datum' je datum DRUGOG (kasnijeg) od
    dva uzastopna sipanja - to je datum kad je taj interval "zavrsen".

    Sipanja bez upisane kilometraze (km_pumpe) se preskacu - ne mogu
    uci u racunicu jer nemaju tacku od koje bi se merila predjena
    kilometraza."""
    sa_km = [s for s in sve_stavke_goriva if s.get("km_pumpe")]
    sa_km.sort(key=lambda s: (s["km_pumpe"], s.get("datum", "")))

    intervali = []
    for prethodno, trenutno in zip(sa_km, sa_km[1:]):
        km_predjeno = trenutno["km_pumpe"] - prethodno["km_pumpe"]
        if km_predjeno <= 0:
            continue
        litara = trenutno.get("litara", 0)
        intervali.append({
            "datum": trenutno.get("datum", "-"),
            "km_predjeno": km_predjeno,
            "litara": litara,
            "potrosnja": litara / km_predjeno * 100,
            "cena": trenutno.get("cena", 0),
        })
    return intervali
