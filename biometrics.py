"""
biometrics.py
Otkljucavanje aplikacije otiskom prsta (Android).

Koristi ugradjeni android.hardware.fingerprint.FingerprintManager API
(dostupan od Android 6.0 / API 23) preko pyjnius, uz pomoc male Java
"premosnice" (vidi java-src/org/licno/taksiapp/fingerprint/).

Zasto premosnica u Javi, a ne cist pyjnius iz Pythona?
FingerprintManager.authenticate() trazi AuthenticationCallback, a to je
APSTRAKTNA JAVA KLASA, ne interfejs. pyjnius (PythonJavaClass) moze iz
Pythona direktno da implementira samo Java INTERFEJSE (koristi
java.lang.reflect.Proxy ispod haube), ne i da naslijedi apstraktnu
klasu. Zato postoji FingerprintBridge.java - on nasledjuje
AuthenticationCallback (u Javi) i samo prosledjuje rezultat jednostavnom
interfejsu FingerprintResultListener, koji MI vec implementiramo u
Pythonu ispod.

Napomena o "deprecated" upozorenju: FingerprintManager je oznacen kao
zastareo od Android 9 (API 28) u korist androidx.biometric.BiometricPrompt.
Medjutim BiometricPrompt zahteva da Activity nasledjuje FragmentActivity,
a Kivy/python-for android-ova PythonActivity to ne radi (nasledjuje
obicnu SDLActivity/Activity) - ta integracija bi zahtevala potpuno
custom Activity klasu i mnogo veci rizik za build. FingerprintManager i
dalje punovazno radi na svim Android verzijama koje ovaj app podrzava
(android.minapi = 21, android.api = 33) i sasvim je dovoljan za licnu
app ovog obima.
"""

_zivi_listener = None  # cuva referencu da Python GC ne obrise listener
                        # objekat dok Android ceka da pozove callback


def _na_androidu():
    try:
        import jnius  # noqa: F401
        return True
    except Exception:
        return False


def hardver_dostupan():
    """Proverava da li uredjaj ima citac otiska I da li je bar jedan
    otisak vec registrovan u sistemskim podesavanjima telefona.
    Vraca (dostupno: bool, poruka: str)."""
    if not _na_androidu():
        return False, "Otisak prsta radi samo na Android uredjaju."

    try:
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context = autoclass("android.content.Context")
        activity = PythonActivity.mActivity

        fm = activity.getSystemService(Context.FINGERPRINT_SERVICE)
        if fm is None:
            return False, "Uredjaj nema citac otiska prsta."
        if not fm.isHardwareDetected():
            return False, "Uredjaj nema citac otiska prsta."
        if not fm.hasEnrolledFingerprints():
            return False, (
                "Nijedan otisak nije registrovan na ovom telefonu "
                "(Podesavanja telefona -> Bezbednost -> Otisak prsta)."
            )
        return True, "OK"
    except Exception as e:
        return False, f"Ne mogu da proverim citac otiska: {e}"


def pokreni_autentifikaciju(on_uspeh, on_greska, on_neuspesno=None):
    """Pokrece skeniranje otiska prsta.

    Callback-ovi:
      on_uspeh()            - otisak je prepoznat, korisnik je potvrdjen
      on_greska(poruka)     - hardverska/sistemska greska, previse
                               pokusaja, korisnik je otkazao itd.
      on_neuspesno()        - otisak je skeniran ali NIJE prepoznat
                               (opciono - korisnik moze odmah ponovo)

    Callback-ovi mogu stici na Android/JNI nit koja nije Kivy-jeva
    glavna nit, pa ih pozivalac (main.py) treba da provuce kroz
    Clock.schedule_once() pre nego sto njima azurira UI.
    """
    global _zivi_listener

    if not _na_androidu():
        on_greska("Otisak prsta radi samo na Android uredjaju.")
        return

    try:
        from jnius import autoclass, PythonJavaClass, java_method

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context = autoclass("android.content.Context")
        CancellationSignal = autoclass("android.os.CancellationSignal")
        FingerprintBridge = autoclass(
            "org.licno.taksiapp.fingerprint.FingerprintBridge"
        )
        activity = PythonActivity.mActivity

        fm = activity.getSystemService(Context.FINGERPRINT_SERVICE)
        if fm is None:
            on_greska("Uredjaj nema citac otiska prsta.")
            return

        class Listener(PythonJavaClass):
            __javainterfaces__ = [
                "org/licno/taksiapp/fingerprint/FingerprintResultListener"
            ]
            __javacontext__ = "app"

            @java_method("()V")
            def onUspeh(self):
                on_uspeh()

            @java_method("(Ljava/lang/String;I)V")
            def onGreska(self, poruka, kod):
                on_greska(poruka if poruka else "Greska pri skeniranju otiska.")

            @java_method("()V")
            def onNeuspesnoSkeniranje(self):
                if on_neuspesno:
                    on_neuspesno()

        listener = Listener()
        _zivi_listener = listener

        bridge = FingerprintBridge(listener)
        cancel = CancellationSignal()

        # flags=0, handler=None -> koristi Looper trenutne niti (glavna
        # UI nit, jer se ova funkcija poziva iz Kivy/Android UI niti).
        fm.authenticate(None, cancel, 0, bridge, None)
    except Exception as e:
        on_greska(f"Ne mogu da pokrenem skeniranje otiska: {e}")
