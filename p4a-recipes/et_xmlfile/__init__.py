from pythonforandroid.recipe import PythonRecipe


class EtXmlfileRecipe(PythonRecipe):
    version = "2.0.0"
    url = "https://files.pythonhosted.org/packages/source/e/et_xmlfile/et_xmlfile-{version}.tar.gz"
    call_hostpython_via_targetpython = False


recipe = EtXmlfileRecipe()
