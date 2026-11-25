"""Chargement d'un catalogue de projet : project.yml (build) + tests.yml (cas de test)."""

from pathlib import Path
from typing import Any

import yaml


class CatalogError(ValueError):
    pass


def _load_yaml(path: Path) -> Any:
    if not path.is_file():
        raise CatalogError(f"fichier manquant : {path}")
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise CatalogError(f"YAML invalide dans {path} : {exc}") from exc


def _validate_test(test: Any, index: int) -> dict:
    if not isinstance(test, dict):
        raise CatalogError(f"test #{index} : doit être un mapping")
    if not test.get("name"):
        raise CatalogError(f"test #{index} : champ `name` requis")
    cmd = test.get("cmd")
    if not isinstance(cmd, list) or not cmd or not all(isinstance(c, str) for c in cmd):
        raise CatalogError(f"test « {test['name']} » : `cmd` doit être une liste non vide de chaînes")
    if test.get("reference") is not None and not (
        isinstance(test["reference"], list) and all(isinstance(c, str) for c in test["reference"])
    ):
        raise CatalogError(f"test « {test['name']} » : `reference` doit être une liste de chaînes")
    return test


def load(catalog_dir: Path) -> tuple[dict, list[dict]]:
    """Renvoie (project, tests) pour le dossier de catalogue donné."""
    project = _load_yaml(catalog_dir / "project.yml")
    tests_doc = _load_yaml(catalog_dir / "tests.yml")
    raw_tests = tests_doc.get("tests") or []
    if not isinstance(raw_tests, list):
        raise CatalogError("tests.yml : `tests` doit être une liste")
    tests = [_validate_test(t, i) for i, t in enumerate(raw_tests, 1)]
    return project, tests


def build_spec(project: dict, tests: list[dict]) -> dict:
    """Spec JSON transmise au driver dans le conteneur."""
    build = None
    if project.get("binary"):
        build = {
            "binary": project["binary"],
            "allowed_functions": project.get("allowed_functions"),
            "timeout": project.get("build_timeout", 120),
        }
    return {"build": build, "tests": tests}
