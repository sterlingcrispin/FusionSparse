from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools.parse_python_defs import parse_python_defs


SOURCE = """
class DocumentTypes():
    \"\"\"Document type enum.\"\"\"
    def __init__(self):
        pass
    FusionDesignDocumentType = 0


class Application(Base):
    @staticmethod
    def get() -> Application:
        \"\"\"Root application getter.\"\"\"
        return Application()


class ValueInput(Base):
    @property
    def realValue(self) -> float:
        return float()

    @realValue.setter
    def realValue(self, value: float):
        pass
"""


class ParsePythonDefsTests(unittest.TestCase):
    def test_parse_symbols_from_defs_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            defs_root = Path(tmp_dir) / "defs" / "adsk"
            defs_root.mkdir(parents=True)
            (defs_root / "core.py").write_text(SOURCE, encoding="utf-8")

            symbols = parse_python_defs(Path(tmp_dir) / "defs")
            index = {symbol["id"]: symbol for symbol in symbols}

            self.assertIn("adsk.core", index)
            self.assertEqual(index["adsk.core.DocumentTypes"]["kind"], "enum")
            self.assertEqual(index["adsk.core.DocumentTypes.FusionDesignDocumentType"]["kind"], "constant")
            self.assertEqual(index["adsk.core.Application"]["kind"], "class")
            self.assertEqual(index["adsk.core.Application.get"]["flags"]["staticmethod"], True)
            self.assertEqual(index["adsk.core.ValueInput.realValue"]["kind"], "property")
            self.assertEqual(index["adsk.core.ValueInput.realValue"]["flags"]["has_setter"], True)


if __name__ == "__main__":
    unittest.main()
