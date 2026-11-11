"""Füllt die Marken der README: die Tabellen aus den Daten und dem Kern (`<!-- tabelle:NAME -->`), den Text der Annahmen (`<!-- annahmen -->`, aus `bdl_texts.py`) und die Testzahl
(`<!-- testzahl -->`, aus `pytest --collect-only -q tests`). Die Marken bleiben stehen; der Aufruf ist wiederholbar.

    python tools/readme_fuellen.py"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import readme_tabellen  # noqa: E402
from bdl_texts import ASSUMPTIONS_MARKDOWN  # noqa: E402


def testzahl() -> int:
    p = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "tests", "-p", "no:cacheprovider"], cwd=ROOT, capture_output=True, text=True, timeout=600)
    m = re.search(r"(\d+) tests? collected", p.stdout)
    if not m:
        raise SystemExit(p.stdout[-400:])
    return int(m.group(1))


def _ersetze(text: str, anfang: str, ende: str, inhalt: str) -> str:
    """Ersetzt alles zwischen der Marke `anfang` und der nächsten Marke `ende` (auch bei leerem Block) durch `inhalt`; fehlt eine Marke, bricht der Aufruf ab, ohne etwas zu ändern."""
    i = text.index(anfang)
    j = text.index(ende, i)
    return text[: i + len(anfang)] + "\n" + inhalt + "\n" + text[j:]


def fuelle(text: str, zahl_der_tests: int) -> str:
    for name, tabelle in readme_tabellen.alle().items():
        text = _ersetze(text, f"<!-- tabelle:{name} -->", "<!-- /tabelle -->", tabelle)
    text = _ersetze(text, "<!-- annahmen -->", "<!-- /annahmen -->", ASSUMPTIONS_MARKDOWN.strip())
    return _ersetze(text, "<!-- testzahl -->", "<!-- /testzahl -->", f"Die Suite hat {zahl_der_tests} Tests (`pytest --collect-only -q tests`).")


if __name__ == "__main__":
    pfad = ROOT / "README.md"
    pfad.write_text(fuelle(pfad.read_text(encoding="utf-8"), testzahl()), encoding="utf-8", newline="\n")
