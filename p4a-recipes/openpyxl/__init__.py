from pythonforandroid.recipe import PythonRecipe


class OpenpyxlRecipe(PythonRecipe):
    version = "3.1.2"
    url = "https://files.pythonhosted.org/packages/source/o/openpyxl/openpyxl-{version}.tar.gz"
    depends = ["setuptools", "et_xmlfile"]
    call_hostpython_via_targetpython = False


recipe = OpenpyxlRecipe()
