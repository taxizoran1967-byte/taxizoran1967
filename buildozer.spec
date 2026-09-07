[app]
title = Taksi App
package.name = taksiapp
package.domain = org.licno

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 0.1

icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png
icon.adaptive_foreground.filename = %(source.dir)s/icon_fg.png
icon.adaptive_background.filename = %(source.dir)s/icon_bg.png

requirements = python3,kivy,sqlite3,plyer,certifi,reportlab,pillow

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,MANAGE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES,READ_MEDIA_VIDEO,READ_MEDIA_AUDIO,READ_EXTERNAL_STORAGE,USE_FINGERPRINT,USE_BIOMETRIC

android.archs = arm64-v8a

android.api = 33
android.minapi = 21

# Lokalni p4a recepti - koristi se da se freetype skida sa SourceForge
# mirrora umesto sa nepouzdanog download.savannah.gnu.org servera.
p4a.local_recipes = ./p4a-recipes

# Java "premosnica" za otkljucavanje otiskom prsta (FingerprintBridge,
# FingerprintResultListener) - vidi biometrics.py za objasnjenje zasto
# je ovo potrebno.
android.add_src = java-src

[buildozer]
log_level = 2
warn_on_root = 1

