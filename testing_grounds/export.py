# AUTOGENERATED! DO NOT EDIT! File to edit: ../01_export.ipynb.

# %% auto 0
__all__ = ['ExportTestProc', 'write_test_cells', 'TestMaker', 'create_test_modules']

# %% ../01_export.ipynb 3
from nbprocess.process import *
from nbprocess.read import *
from nbprocess.imports import *
from nbprocess.maker import *

# %% ../01_export.ipynb 5
from collections import defaultdict
from fastcore.foundation import L, ifnone
from execnb.nbio import *

class ExportTestProc:
    "A test proc that watches for `#|default_exp` and `#|test`"
    def __init__(self): self.tests = defaultdict(L)
    def _default_exp_(self, nbp, cell, exp_to): self.default_exp = f'test_{exp_to}'
    def _test_(self, nbp, cell, exp_to=None): self.tests[f'test_{ifnone(exp_to, "#")}'].append(nbp.cell)

# %% ../01_export.ipynb 6
def write_test_cells(cells, hdr, file, offset=0, name=""):
    "Takes cells and either formats them for import statments, or writes out test functions"
    for cell in cells:
        if cell.source.strip():
            if "import" in cell["directives_"]["test"]:
                # Expected, this should be at the top. What happens is its never written
                content = f'\n\t\t{hdr} {cell.idx_+offset}\n\t\t{cell.source}'
            else:
                test_name = cell["directives_"]["test"][0]
                content = '\n'.join([f"\t{c}" for c in cell.source.split("\n")])
                content = f'\n\t{hdr} {cell.idx_+offset}\n\tdef test_{test_name}(self):\n{content}'
            file.write(content)

# %% ../01_export.ipynb 7
import ast
class TestMaker(ModuleMaker):
    "Module maker that will write test cells depending on a flag"
    def make_all(self, cells): pass
    def _make_exists(self, cells, all_cells=None):
        with self.fname.open("a") as f: 
            write_test_cells(cells, self.hdr, f, 0, self.name.replace("test_","").capitalize())
    
    def make(self, cells, all_cells=None, lib_name=None, write_start=False):
        if lib_name is None: lib_name = get_config().lib_name
        if all_cells is None: all_cells = cells
        for cell in all_cells: cell.import2relative(lib_name)
        if not self.is_new: return self._make_exists(cells, all_cells)
        
        self.fname.parent.mkdir(exist_ok=True, parents=True)
        trees = cells.map(NbCell.parsed_)
        try: last_future = max(i for i,tree in enumerate(trees) if tree and any(
             isinstance(t,ast.ImportFrom) and t.module=='__future__' for t in tree))+1
        except ValueError: last_future=0
        with self.fname.open('w') as f:
            f.write(f"# AUTOGENERATED! DO NOT EDIT! File to edit: {self.dest2nb}.")
            write_cells(cells[:last_future], self.hdr, f, 0)
            write_test_cells(cells, self.hdr, f, 0, self.name.replace("test_","").capitalize())
            f.write('\n')

# %% ../01_export.ipynb 8
def create_test_modules(path, dest, debug=False):
    "Creates test module(s) from notebook and saves them to a tests/ folder"
    exp = ExportTestProc()
    nb = NBProcessor(path, exp, debug=debug)
    nb.process()
    for i,(mod, cells) in enumerate(exp.tests.items()):
        name = exp.default_exp
        mm = TestMaker(dest=dest, name=name, nb_path=path, is_new=i==0)
        mm.make(cells, write_start=i==0)
        if i == 0:
            with mm.fname.open("a") as f:
                name = name.lower().replace("test_", "")
                f.write(f'\nfrom {get_config().lib_name}.{name} import *')
                f.write(f'\nimport unittest\n')
                f.write(f'\nclass {name.title()}Tester(unittest.TestCase):')
