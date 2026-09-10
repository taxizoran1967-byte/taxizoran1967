"""
Android foreground servis za GPS pracenje voznje u pozadini.
"""

import time

from servisi.gps_tracking import (
    AndroidLocationTracker,
    AktivnaVoznjaState,
    obradi_lokaciju_i_sacuvaj,
    dijagnostika_lokacije,
    obrisi_running_fajl,
    dodaj_dijagnozu,
    ocisti_stop_fajl,
    odredi_user_data_dir,
    postavi_status,
    treba_zaustaviti_servis,
    upisi_running_fajl,
)


NOTIFIKACIJA_ID = 731
KANAL_ID = "taksiapp_gps_voznja"


def _pokreni_foreground_notifikaciju():
    from jnius import autoclass

    PythonService = autoclass("org.kivy.android.PythonService")
    service = PythonService.mService
    Context = autoclass("android.content.Context")
    Intent = autoclass("android.content.Intent")
    PendingIntent = autoclass("android.app.PendingIntent")
    NotificationBuilder = autoclass("android.app.Notification$Builder")
    BuildVersion = autoclass("android.os.Build$VERSION")
    NotificationManager = autoclass("android.app.NotificationManager")
    PythonActivity = autoclass("org.kivy.android.PythonActivity")

    app_context = service.getApplicationContext()

    if BuildVersion.SDK_INT >= 26:
        NotificationChannel = autoclass("android.app.NotificationChannel")
        manager = service.getSystemService(Context.NOTIFICATION_SERVICE)
        kanal = NotificationChannel(
            KANAL_ID,
            "GPS voznja",
            NotificationManager.IMPORTANCE_LOW,
        )
        kanal.setDescription("Pozadinsko pracenje aktivne GPS voznje")
        manager.createNotificationChannel(kanal)
        builder = NotificationBuilder(app_context, KANAL_ID)
    else:
        builder = NotificationBuilder(app_context)

    try:
        Drawable = autoclass(f"{service.getPackageName()}.R$drawable")
        icon_id = getattr(Drawable, "icon")
    except Exception:
        icon_id = autoclass("android.R$drawable").ic_menu_mylocation

    intent = Intent(app_context, PythonActivity)
    intent.setAction(Intent.ACTION_MAIN)
    intent.addCategory(Intent.CATEGORY_LAUNCHER)
    flags = PendingIntent.FLAG_UPDATE_CURRENT
    if BuildVersion.SDK_INT >= 23:
        flags |= PendingIntent.FLAG_IMMUTABLE
    pending_intent = PendingIntent.getActivity(app_context, 0, intent, flags)

    builder.setContentTitle("Taksi App - GPS voznja")
    builder.setContentText("Voznja je aktivna i nastavlja da prati kilometrazu u pozadini.")
    builder.setSmallIcon(icon_id)
    builder.setOngoing(True)
    builder.setAutoCancel(False)
    builder.setOnlyAlertOnce(True)
    builder.setContentIntent(pending_intent)

    if BuildVersion.SDK_INT >= 16:
        notifikacija = builder.build()
    else:
        notifikacija = builder.getNotification()

    service.startForeground(NOTIFIKACIJA_ID, notifikacija)
    return service


def _zaustavi_foreground_notifikaciju(service):
    try:
        service.stopForeground(True)
    except Exception:
        pass
    try:
        service.stopSelf()
    except Exception:
        pass


def main():
    user_data_dir = odredi_user_data_dir()
    ocisti_stop_fajl(user_data_dir)
    service = _pokreni_foreground_notifikaciju()

    postavi_status(
        gps_status="Foreground servis aktivan, trazim GPS signal...",
        dijagnoza=dijagnostika_lokacije(),
        izvor_pracenja="foreground_service",
        user_data_dir=user_data_dir,
    )

    tracker = AndroidLocationTracker(
        na_lokaciju=lambda podaci: obradi_lokaciju_i_sacuvaj(
            podaci,
            user_data_dir=user_data_dir,
        ),
        na_dijagnozu=lambda tekst: dodaj_dijagnozu(tekst, user_data_dir=user_data_dir),
        na_gresku=lambda tekst: postavi_status(
            gps_status=f"Greska pri pokretanju GPS-a: {tekst}",
            user_data_dir=user_data_dir,
        ),
    )

    pokrenut = tracker.pokreni()
    upisi_running_fajl(user_data_dir)
    if not pokrenut:
        postavi_status(
            gps_status="Greska pri pokretanju GPS-a.",
            user_data_dir=user_data_dir,
        )
        return

    sekundi_bez_signala = 0

    try:
        while True:
            stanje = AktivnaVoznjaState()
            stanje.ucitaj(user_data_dir)
            if treba_zaustaviti_servis(user_data_dir) or not stanje.aktivna:
                break

            upisi_running_fajl(user_data_dir)
            tracker.pull_lokaciju()

            stanje.ucitaj(user_data_dir)
            if stanje.pocetak_lat is None:
                sekundi_bez_signala += 2
                if sekundi_bez_signala == 16:
                    postavi_status(
                        gps_status=(
                            "Jos uvek nema GPS signala. Voznja je pokrenuta i ceka "
                            "prvi signal - km i cena ce poceti da se racunaju cim "
                            "GPS uhvati poziciju."
                        ),
                        user_data_dir=user_data_dir,
                    )
                elif sekundi_bez_signala > 15 and sekundi_bez_signala % 10 == 0:
                    postavi_status(
                        gps_status=f"Jos uvek tražim signal... ({sekundi_bez_signala}s)",
                        user_data_dir=user_data_dir,
                    )
            else:
                sekundi_bez_signala = 0

            time.sleep(2)
    finally:
        tracker.zaustavi()
        obrisi_running_fajl(user_data_dir)
        _zaustavi_foreground_notifikaciju(service)


if __name__ == "__main__":
    main()
