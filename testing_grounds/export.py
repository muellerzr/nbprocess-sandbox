# AUTOGENERATED! DO NOT EDIT! File to edit: ../01_export.ipynb.

# %% ../01_export.ipynb 1
from __future__ import annotations

# %% auto 0
__all__ = ['ExportTestProc', 'get_directive', 'convert_pytest', 'construct_imports', 'create_test_modules', 'convert_unittest']

# %% ../01_export.ipynb 4
from nbprocess.process import *
from nbprocess.read import *
from nbprocess.imports import *
from nbprocess.maker import *

from nbprocess.processors import _default_exp

# %% ../01_export.ipynb 7
from collections import defaultdict
from fastcore.foundation import L, ifnone
from execnb.nbio import *

class ExportTestProc:
    "A test proc that watches for `#|default_exp` and `#|test`"
    def __init__(self): self.tests = defaultdict(L)
    def _default_exp_(self, nbp, cell, exp_to): self.default_exp = f'test_{exp_to}'
    def _test_(self, nbp, cell, exp_to=None, nm=None, tst_cls=None): self.tests[self.default_exp].append(nbp.cell)

# %% ../01_export.ipynb 8
_re_test = re.compile(r'#\|\s*test\s*$', re.MULTILINE)
_re_import = re.compile(r'#\|\s*test\s*import\s*$', re.MULTILINE)
_tab = "    "

# %% ../01_export.ipynb 9
def get_directive(cell, key, default=None): 
    "Extract a top level directive from `cell`"
    return cell.directives_.get(key, default)

def _is_test_cell(cell): return cell.cell_type == "code" and get_directive(cell, "test")

# %% ../01_export.ipynb 11
def _mark_test(s):
    ft = exec_new("import fastcore.test as ft")["ft"].__all__
    kinds = [o for o in ft if o.startswith("test")]
    for k in kinds:
        if f"{k}(" in s: 
            s = s.replace(f"{k}(", f"ft.{k}(")
    return s

# %% ../01_export.ipynb 12
def convert_pytest(cell):
    "Wraps cell contents into a pytest function"
    directive = get_directive(cell, "test")
    if _is_test_cell(cell):
        if "import" not in directive:
            content = '\n'.join([f"{_tab}{c}" for c in cell.source.split("\n")])
            content = _mark_test(content)
            cell.source = f'def test_{directive[0]}():\n{content}'
        else:
            cell.source = cell.source.replace("from fastcore.test import *", "import fastcore.test as ft")

# %% ../01_export.ipynb 14
def construct_imports(nb, use_unittest=False):
    "Generates the test imports for the notebook"
    libname = get_config().lib_name
    exp = _default_exp(nb)
    imports = ['#| test import\n', f'from {libname}.{exp} import *\n']
    if use_unittest: imports += ['import unittest']
    nb.cells.insert(1, mk_cell(imports))

# %% ../01_export.ipynb 16
def create_test_modules(path,dest,debug=False,mod_maker=ModuleMaker, unittest=False):
    "Creates test files from `path`, optionally with unittest support"
    exp = ExportTestProc()
    procs = [exp, convert_pytest]
    if unittest: procs.append(convert_unittest)
    nb = NBProcessor(path, procs, preprocs=partial(construct_imports, use_unittest=unittest))
    nb.process()
    is_new = True
    for mod,cells in exp.tests.items():
        mm = mod_maker(dest=dest, name=exp.default_exp, nb_path=path, is_new=is_new)
        mm.make(cells)
        is_new = False

# %% ../01_export.ipynb 19
def convert_unittest(cell):
    "Wraps cell contents into a unittest test suite."
    if _is_test_cell(cell):
        directive = get_directive(cell, "test")
        if "case" in directive:
            tstcls, = directive[2:3] or "unittest.TestCase"
            cell.source = f'class {directive[1]}({tstcls}):'
        elif "import" not in directive:
            cell.source = '\n'.join([f'{_tab}{c}' for c in cell.source.split("\n")])
