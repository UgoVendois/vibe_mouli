"""Parseurs des sorties du coding style officiel, exécutées dans l'image epitest.

- `epiclang` (plugin banana, règles C-*) : `fichier:ligne:col: warning: [Banana] [Major] msg (C-F3)`
- `banana-check-repo` (règles C-O*) : `chemin: [Banana] [Major] msg (C-O1)`

Les commandes sont lancées par le driver dans le conteneur ; ce module ne fait que parser.
"""

import re
from dataclasses import asdict, dataclass

EPICLANG_RE = re.compile(
    r"^(?P<file>[^:\n]+):(?P<line>\d+):(?P<col>\d+): (?:warning|error): "
    r"\[Banana\] \[(?P<sev>\w+)\] (?P<msg>.*?) \((?P<code>C-[A-Z]\d+)\)\s*$"
)
REPO_RE = re.compile(
    r"^(?P<file>[^:\n]+): \[Banana\] \[(?P<sev>\w+)\] (?P<msg>.*?) \((?P<code>C-[A-Z]\d+)\)\s*$"
)
REPO_PREFIXES = ("/job/src/", "./")


@dataclass(frozen=True)
class Infraction:
    file: str
    line: int
    col: int
    severity: str
    code: str
    message: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


def _clean_path(path: str) -> str:
    for prefix in REPO_PREFIXES:
        if path.startswith(prefix):
            path = path[len(prefix):]
    return path


def parse_epiclang(text: str) -> list[Infraction]:
    """Infractions C-* ; dédupliquées car un header est réémis à chaque unité de compilation."""
    found = {}
    for raw in text.splitlines():
        m = EPICLANG_RE.match(raw)
        if m:
            key = (m["file"], int(m["line"]), int(m["col"]), m["code"], m["msg"])
            found.setdefault(key, Infraction(m["file"], int(m["line"]), int(m["col"]),
                                             m["sev"].upper(), m["code"], m["msg"]))
    return list(found.values())


def epiclang_errors(text: str) -> list[str]:
    """Erreurs de compilation (syntaxe, include manquant...) : elles faussent le contrôle."""
    return sorted({raw.strip() for raw in text.splitlines()
                   if ": error:" in raw and "[Banana]" not in raw})


def parse_banana_repo(text: str) -> list[Infraction]:
    """Infractions C-O* de banana-check-repo (fichiers indésirables, etc.)."""
    found = {}
    for raw in text.splitlines():
        m = REPO_RE.match(raw.strip())
        if m:
            path = _clean_path(m["file"])
            found.setdefault((path, m["code"], m["msg"]),
                             Infraction(path, 0, 0, m["sev"].upper(), m["code"], m["msg"]))
    return list(found.values())
