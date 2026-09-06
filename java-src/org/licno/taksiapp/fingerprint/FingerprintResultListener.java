package org.licno.taksiapp.fingerprint;

/**
 * Jednostavan interfejs (namerno interfejs, a ne apstraktna klasa) -
 * pyjnius iz Pythona moze direktno da implementira Java interfejse
 * preko PythonJavaClass, sto omogucava da FingerprintBridge (koji
 * nasledjuje pravi Android AuthenticationCallback) prosledi rezultat
 * nazad u Python kod bez ikakvog dodatnog Java koda po strani.
 */
public interface FingerprintResultListener {
    void onUspeh();

    void onGreska(String poruka, int kod);

    void onNeuspesnoSkeniranje();
}
