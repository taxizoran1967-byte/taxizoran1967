# Lokalni p4a recept koji GAZI ugradjeni "reportlab" recept.
#
# ZASTO POSTOJI OVAJ FAJL:
# Ugradjeni p4a recept skida reportlab izvorni kod sa
# https://hg.reportlab.com/... - taj server sada vraca "403 Forbidden"
# za automatizovane download-e (blokira botove/CI), sto je uzrok
# padanja build-a na koraku "Downloading reportlab".
#
# STA OVAJ FAJL RADI:
# 1) Skida ISTU verziju reportlab-a (3.6.12), ali sa zvanicnog PyPI
#    servera (files.pythonhosted.org) - isti kod, pouzdan server.
# 2) Reportlab ima OPCIONE "C accelerator" delove (rl_accel, renderPM)
#    koji malo ubrzavaju rad, ali NISU neophodni - reportlab ima
#    "cist Python" fallback za njih. Kompajliranje tih delova za
#    Android bi trazilo freetype/libart podesavanja i puno je
#    rizicnije. Ovaj recept ih jednostavno uklanja pre instalacije,
#    pa se reportlab instalira kao cist Python paket - bez
#    kompajlera. Ovo NE UTICE na PDF izvestaje u app-u (fontovi,
#    tabele, tekst) - samo je (neprimetno) sporiji render, sto se
#    ne oseti kod obicnih izvestaja od par stranica.

import os
import shutil

from pythonforandroid.recipe import PythonRecipe
from pythonforandroid.logger import info


class ReportLabRecipe(PythonRecipe):

    version = "3.6.12"

    # Zvanicni fajl sa PyPI (isto kao "pip install reportlab==3.6.12"),
    # samo sto ga p4a sam ne bi nasao jer trazi svoj ugradjeni recept.
    url = (
        "https://files.pythonhosted.org/packages/b8/ac/"
        "10d68a650b321bd8c4d8cbefd9994e7727d57b381c9bdb0a013273011e62/"
        "reportlab-{version}.tar.gz"
    )

    depends = ["python3"]

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        build_dir = self.get_build_dir(arch.arch)
        addons_dir = os.path.join(build_dir, "src", "rl_addons")
        if os.path.isdir(addons_dir):
            info(
                "reportlab (lokalni recept): uklanjam C-accelerator "
                "izvorni kod (rl_accel, renderPM) - koristice se "
                "cist Python nacin rada umesto kompajliranja"
            )
            shutil.rmtree(addons_dir)


recipe = ReportLabRecipe()
