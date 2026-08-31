"""Linux must be able to open info.rte / the RTE editor without ctypes.windll.

HoloPatcher 1.5.1 imported utility.tkinter.rte_editor whenever a namespace
InfoName was a .rte file (or Tools > Create info.rte was used). That module
called ctypes.windll.shcore.SetProcessDpiAwareness at import time, which
raises AttributeError on Linux and pops a blocking GUI dialog.
"""

from __future__ import annotations

import ast
import importlib
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock


REPO_SRC = Path(__file__).resolve().parents[1] / "src"
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

APP_PY = REPO_SRC / "holopatcher" / "app.py"


def _module_source(relative_name: str) -> str:
    return (REPO_SRC / "holopatcher" / f"{relative_name}.py").read_text(encoding="utf-8")


def _imported_modules(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class AppImportPathTests(unittest.TestCase):
    def test_app_does_not_import_utility_rte_editor(self):
        source = APP_PY.read_text(encoding="utf-8")
        imported = _imported_modules(source)
        self.assertNotIn("utility.gui.tkinter.rte_editor", imported)
        self.assertNotIn("utility.tkinter.rte_editor", imported)
        self.assertNotIn("utility.gui.tkinter.rte_editor", source)
        self.assertNotIn("utility.tkinter.rte_editor", source)
        self.assertIn("holopatcher.rte_editor", source)


class DisplayScalingTests(unittest.TestCase):
    def test_module_does_not_import_ctypes(self):
        source = _module_source("display_scaling")
        imported = _imported_modules(source)
        self.assertNotIn("ctypes", imported)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "windll":
                self.fail("display_scaling must not reference ctypes.windll")

    def test_apply_display_scaling_uses_tk_scaling(self):
        from holopatcher.display_scaling import apply_display_scaling

        root = MagicMock()
        root.winfo_fpixels.return_value = 144.0
        apply_display_scaling(root)
        root.tk.call.assert_called_once_with("tk", "scaling", 2.0)

    def test_apply_display_scaling_skips_invalid_dpi(self):
        from holopatcher.display_scaling import apply_display_scaling

        root = MagicMock()
        root.winfo_fpixels.return_value = 0
        apply_display_scaling(root)
        root.tk.call.assert_not_called()


class RteEditorImportTests(unittest.TestCase):
    def test_rte_editor_source_has_no_ctypes_or_windll(self):
        source = _module_source("rte_editor")
        imported = _imported_modules(source)
        self.assertNotIn("ctypes", imported)
        self.assertNotIn("windll", source)

    def test_rte_editor_imports_on_linux_without_windll(self):
        import ctypes

        try:
            import tkinter  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("this Python build has no Tk (_tkinter)")

        self.assertFalse(hasattr(ctypes, "windll"))
        if "holopatcher.rte_editor" in sys.modules:
            del sys.modules["holopatcher.rte_editor"]
        module = importlib.import_module("holopatcher.rte_editor")
        self.assertTrue(callable(module.main))


if __name__ == "__main__":
    unittest.main()
