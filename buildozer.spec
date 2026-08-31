[app]
title = Taksi App
package.name = taksiapp
package.domain = org.licno

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.1

icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png
icon.adaptive_foreground.filename = %(source.dir)s/icon_fg.png
icon.adaptive_background.filename = %(source.dir)s/icon_bg.png

requirements = python3,kivy,sqlite3

orientation = portrait
fullscreen = 0

android.permissions = INTERNET

android.archs = arm64-v8a

android.api = 33
android.minapi = 21

[buildozer]
log_level = 2
warn_on_root = 1
