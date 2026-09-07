package org.licno.taksiapp.fingerprint;

import android.annotation.TargetApi;
import android.hardware.fingerprint.FingerprintManager;
import android.os.Build;

/**
 * Tanak Java "most" izmedju Android FingerprintManager API-ja i
 * Python koda (main.py / biometrics.py).
 *
 * FingerprintManager.AuthenticationCallback je APSTRAKTNA KLASA (ne
 * interfejs), pa pyjnius ne moze direktno da je implementira iz
 * Pythona - PythonJavaClass radi samo sa Java interfejsima (koristi
 * java.lang.reflect.Proxy ispod haube, a Proxy ne moze da naslijedi
 * konkretnu/apstraktnu klasu). Ova klasa resava to tako sto se ovde,
 * u Javi, nasledjuje prava apstraktna klasa, a rezultat se samo
 * prosledjuje jednostavnom interfejsu (FingerprintResultListener)
 * koji Python IMPLEMENTIRA preko PythonJavaClass.
 */
@TargetApi(Build.VERSION_CODES.M)
public class FingerprintBridge extends FingerprintManager.AuthenticationCallback {

    private final FingerprintResultListener listener;

    public FingerprintBridge(FingerprintResultListener listener) {
        this.listener = listener;
    }

    @Override
    public void onAuthenticationError(int errorCode, CharSequence errString) {
        listener.onGreska(errString == null ? "" : errString.toString(), errorCode);
    }

    @Override
    public void onAuthenticationHelp(int helpCode, CharSequence helpString) {
        // Privremena poruka sistema (npr. "Pomeri prst sporije") - ne
        // prekida skeniranje, pa je ovde namerno ignorisemo radi
        // jednostavnosti. Korisnik i dalje moze da nastavi da skenira.
    }

    @Override
    public void onAuthenticationSucceeded(FingerprintManager.AuthenticationResult result) {
        listener.onUspeh();
    }

    @Override
    public void onAuthenticationFailed() {
        listener.onNeuspesnoSkeniranje();
    }
}
