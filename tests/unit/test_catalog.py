import pytest

from vibe_mouli import catalog


def _write(d, name, text):
    (d / name).write_text(text, encoding="utf-8")


def test_load_and_build_spec(tmp_path):
    _write(tmp_path, "project.yml", "name: p\nbinary: p\nallowed_functions: [printf]\n")
    _write(tmp_path, "tests.yml", "tests:\n  - name: t\n    cmd: [./p]\n")
    project, tests = catalog.load(tmp_path)
    spec = catalog.build_spec(project, tests)
    assert spec["build"]["binary"] == "p"
    assert spec["build"]["allowed_functions"] == ["printf"]
    assert spec["tests"][0]["name"] == "t"


def test_missing_cmd_is_rejected(tmp_path):
    _write(tmp_path, "project.yml", "name: p\n")
    _write(tmp_path, "tests.yml", "tests:\n  - name: t\n")
    with pytest.raises(catalog.CatalogError, match="cmd"):
        catalog.load(tmp_path)


def test_invalid_yaml_is_reported(tmp_path):
    _write(tmp_path, "project.yml", "name: [\n")
    _write(tmp_path, "tests.yml", "tests: []\n")
    with pytest.raises(catalog.CatalogError, match="YAML invalide"):
        catalog.load(tmp_path)


def test_no_binary_means_no_build_checks():
    assert catalog.build_spec({"name": "x"}, [])["build"] is None
