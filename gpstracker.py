"""
gpstracker.py
Pozadinski Android foreground servis - nastavlja GPS pracenje vožnje
DOK JE GLAVNA APP U POZADINI (npr. korisnik gleda Google Maps
navigaciju). Pokrece se iz ekrani/ekran_gps_voznja.py kad korisnik
klikne "Počni vožnju", i gasi se kad klikne "Završi vožnju".

Ovo je POSEBAN Python proces (ne deo glavne Kivy app-e) - zato NE
importuje nista iz Kivy-ja niti iz glavne app-e (ekrani/, main.py).
Jedino sto deli sa glavnom app-om je:
  1. servisi/gps_logika.py - ista logika za racunanje km/filtriranje
     GPS gresaka (da se ne razmimoidje sa glavnom app-om).
  2. Fajl <user_data_dir>/aktivna_voznja.json - oba procesa citaju i
     pisu ISTI fajl. Bezbedno je jer Kivy na Androidu racuna
     user_data_dir kao Context.getFilesDir() bez ikakvog podfoldera,
     a getFilesDir() vraca ISTU putanju bez obzira da li se poziva iz
     Activity (glavna app) ili iz Service (ovaj fajl) konteksta - oba
     pripadaju istoj Android aplikaciji.

Ako ovaj fajl NIJE pokrenut na Androidu (npr. neko ga slucajno
importuje na desktopu), sve pyjnius operacije ce baciti izuzetak koji
se hvata i servis se tiho gasi - ne pokusava da radi nista van
Androida.
"""

import time
import traceback

from servisi.gps_logika import AktivnaVoznjaState, obradi_tacku


# Na svakih ovoliko sekundi servis "pull-uje" poslednju poznatu
# lokaciju kao rezervu, pored push (LocationListener) mehanizma -
# isti dvostruki pristup kao u glavnoj app-i, jer se pokazalo da neki
# telefoni (narocito MIUI/Xiaomi) umeju da preskacu push obavestenja.
INTERVAL_PROVERE_SEC = 5


def _dobij_kontekst():
    """Vraca (context, user_data_dir) za ovaj Android servis, ili
    (None, None) ako nismo na Androidu."""
    from jnius import autoclass, cast

    PythonService = autoclass("org.kivy.android.PythonService")
    context = cast("android.content.Context", PythonService.mService)
    file_p = cast("java.io.File", context.getFilesDir())
    user_data_dir = file_p.getAbsolutePath()
    return context, user_data_dir


def _pokusaj_dobij_lokaciju(context):
    """Isti pristup kao _pull_lokaciju u glavnoj app-i - pita
    LocationManager za POSLEDNJU POZNATU lokaciju (ne registruje novi
    listener ovde, jer to vec radi _registruj_listener nize; ovo je
    samo rezerva za slucaj da push ne stigne)."""
    from jnius import autoclass

    LocationManager = autoclass("android.location.LocationManager")
    lm = context.getSystemService(Context_LOCATION_SERVICE)

    najbolja = None
    for provider in (LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER):
        try:
            if not lm.isProviderEnabled(provider):
                continue
            loc = lm.getLastKnownLocation(provider)
            if loc is None:
                continue
            if najbolja is None or loc.getAccuracy() < najbolja.getAccuracy():
                najbolja = loc
        except Exception:
            continue
    return najbolja


def _registruj_listener(context, aktivna_voznja, user_data_dir):
    """Registruje Android LocationListener preko pyjnius - isti
    obrazac kao _android_gps_start u ekran_gps_voznja.py, samo sto
    ovde radi u kontekstu Service-a umesto Activity-a."""
    from jnius import autoclass, PythonJavaClass, java_method

    LocationManager = autoclass("android.location.LocationManager")

    class _Listener(PythonJavaClass):
        __javainterfaces__ = ["android/location/LocationListener"]
        __javacontext__ = "app"

        @java_method("(Landroid/location/Location;)V")
        def onLocationChanged(self, location):
            try:
                obradi_tacku(
                    aktivna_voznja, user_data_dir,
                    location.getLatitude(), location.getLongitude(),
                    location.getAccuracy(), time.time(),
                )
            except Exception:
                pass

        @java_method("(Ljava/lang/String;)V")
        def onProviderEnabled(self, provider):
            pass

        @java_method("(Ljava/lang/String;)V")
        def onProviderDisabled(self, provider):
            pass

        @java_method("(Ljava/lang/String;ILandroid/os/Bundle;)V")
        def onStatusChanged(self, provider, status, extras):
            pass

    lm = context.getSystemService(Context_LOCATION_SERVICE)
    listener = _Listener()

    for provider in (LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER):
        try:
            if lm.isProviderEnabled(provider):
                lm.requestLocationUpdates(provider, 3000, 5.0, listener)
        except Exception:
            continue

    return listener  # cuvamo referencu - Java drzi samo slabu vezu, PA MORA da ostane ziva u Pythonu


def main():
    try:
        from jnius import autoclass

        Context = autoclass("android.content.Context")
        global Context_LOCATION_SERVICE
        Context_LOCATION_SERVICE = Context.LOCATION_SERVICE

        context, user_data_dir = _dobij_kontekst()
    except Exception:
        # Nismo na Androidu (ili nesto nije dostupno) - servis nema
        # sta da radi, samo se tiho zavrsava.
        traceback.print_exc()
        return

    aktivna_voznja = AktivnaVoznjaState()
    aktivna_voznja.ucitaj(user_data_dir)

    if not aktivna_voznja.aktivna:
        # Servis je pokrenut a voznja vec nije aktivna (npr. korisnik
        # je stigao da zavrsi voznju pre nego sto je servis stigao da
        # se pokrene) - nema svrhe da nastavlja da radi.
        return

    listener = _registruj_listener(context, aktivna_voznja, user_data_dir)

    # Glavna petlja servisa - dok je voznja aktivna, periodicno
    # proveravamo i poslednju poznatu lokaciju kao rezervu (isti
    # dvostruki pristup - push + pull - kao u glavnoj app-i), i
    # osvezavamo aktivna_voznja iz fajla (za slucaj da je glavna app,
    # dok je u prvom planu, i sama upisala novije podatke).
    while True:
        time.sleep(INTERVAL_PROVERE_SEC)

        # ponovo ucitaj stanje - moglo je da se promeni iz glavne app-e
        aktivna_voznja.ucitaj(user_data_dir)
        if not aktivna_voznja.aktivna:
            break  # korisnik je zavrsio voznju dok je app bila u prvom planu

        try:
            loc = _pokusaj_dobij_lokaciju(context)
            if loc is not None:
                obradi_tacku(
                    aktivna_voznja, user_data_dir,
                    loc.getLatitude(), loc.getLongitude(),
                    loc.getAccuracy(), time.time(),
                )
        except Exception:
            pass


if __name__ == "__main__":
    main()
