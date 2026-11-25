"""Logique de comparaison du driver, testée sur l'hôte avec des commandes shell réelles."""

import sys
from pathlib import Path

from vibe_mouli import driver


def test_expected_stdout_and_rc_pass(tmp_path):
    r = driver.run_test({"name": "ok", "cmd": ["echo", "hi"], "expect": {"stdout": "hi\n", "exit_code": 0}}, src=tmp_path)
    assert r["passed"], r["reason"]


def test_reference_is_used_as_oracle(tmp_path):
    r = driver.run_test({"name": "ref", "cmd": ["echo", "a"], "reference": ["echo", "a"]}, src=tmp_path)
    assert r["passed"], r["reason"]


def test_wrong_stdout_fails_with_diff(tmp_path):
    r = driver.run_test({"name": "bad", "cmd": ["echo", "a"], "expect": {"stdout": "b\n"}}, src=tmp_path)
    assert not r["passed"]
    assert "sortie standard différente" in r["reason"]
    assert "-b" in r["diff"] and "+a" in r["diff"]


def test_segfault_is_reported_as_crash(tmp_path):
    r = driver.run_test({"name": "seg", "cmd": ["sh", "-c", "kill -SEGV $$"]}, src=tmp_path)
    assert not r["passed"]
    assert "SIGSEGV" in r["reason"]


def test_timeout_is_reported(tmp_path):
    r = driver.run_test({"name": "loop", "cmd": ["sleep", "5"], "timeout": 0.3}, src=tmp_path)
    assert not r["passed"]
    assert "timeout" in r["reason"]


def test_missing_binary_is_reported(tmp_path):
    r = driver.run_test({"name": "absent", "cmd": ["./does-not-exist"]}, src=tmp_path)
    assert not r["passed"]
    assert "exécution impossible" in r["reason"]
