"""Contrôles faits sur l'hôte, en lecture seule sur le repo original.

- fichiers interdits (*.o, vgcore.*, *~, #*#) ;
- coding style : parseur du format `fichier:ligne: GRAVITÉ:C-XX` du checker officiel,
  et une APPROXIMATION locale (le checker officiel n'est pas accessible, voir docs/RESEARCH.md).
"""

import re
from dataclasses import dataclass, asdict
from pathlib import Path

FORBIDDEN_PATTERNS = ("*.o", "vgcore.*", "*~", "#*#")
STYLE_RE = re.compile(
    r"^(?P<file>[^:\n]+):(?P<line>\d+): (?P<sev>MAJOR|MINOR|INFO):(?P<code>C-\d+)\b(?P<msg>.*)$"
)


@dataclass(frozen=True)
class Infraction:
    file: str
    line: int
    severity: str
    code: str
    message: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


def forbidden_files(repo: Path) -> list[str]:
    found = set()
    for pattern in FORBIDDEN_PATTERNS:
        for path in repo.rglob(pattern):
            if ".git" not in path.relative_to(repo).parts and path.is_file():
                found.add(str(path.relative_to(repo)))
    return sorted(found)


def parse_checker_report(text: str) -> list[Infraction]:
    """Parse une sortie `fichier:ligne: MAJOR|MINOR|INFO: C-XX message`."""
    infractions = []
    for raw in text.splitlines():
        m = STYLE_RE.match(raw.strip())
        if m:
            infractions.append(
                Infraction(m["file"], int(m["line"]), m["sev"], m["code"], m["msg"].strip(" -"))
            )
    return infractions


def local_style_check(repo: Path) -> list[Infraction]:
    """APPROXIMATION : quelques règles simples (80 colonnes, espaces en fin de ligne, tabulations).
    Ce ne sont PAS les règles officielles ; les codes sont préfixés LOCAL-."""
    infractions = []
    for path in sorted(repo.rglob("*")):
        if not path.is_file() or path.suffix not in {".c", ".h"} or ".git" in path.relative_to(repo).parts:
            continue
        rel = str(path.relative_to(repo))
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            if len(line) > 80:
                infractions.append(Infraction(rel, lineno, "MAJOR", "LOCAL-LINE80", "ligne de plus de 80 colonnes"))
            if line != line.rstrip():
                infractions.append(Infraction(rel, lineno, "MINOR", "LOCAL-TRAILING", "espaces en fin de ligne"))
            if "\t" in line:
                infractions.append(Infraction(rel, lineno, "MINOR", "LOCAL-TAB", "tabulation"))
    return infractions
