"""Exécuté DANS le conteneur epitest (python3 -I, stdlib uniquement).

Lit la spec (/opt/vm/spec.json, montage en lecture seule), lance les contrôles
de build puis les tests sur /job/src (copie du repo de l'étudiant), et écrit
/out/results.json. Ce fichier n'est pas exécuté sur l'hôte.
"""

import difflib
import json
import os
import signal
import subprocess
import time

SRC = os.environ.get("VM_SRC", "/job/src")
SPEC = os.environ.get("VM_SPEC", "/opt/vm/spec.json")
OUT = os.environ.get("VM_OUT", "/out/results.json")
MAX_OUT = 64 * 1024
# Symboles injectés par la libc / le linker, jamais comptés comme « fonctions utilisées ».
IGNORED_SYMBOL_PREFIXES = ("__", "_ITM_", "_Jv_")


def _clip(text):
    if len(text) > MAX_OUT:
        return text[:MAX_OUT] + "\n[...tronqué]"
    return text


def describe_rc(rc):
    if rc is None:
        return "aucun code de retour"
    if rc < 0:
        try:
            return f"signal {signal.Signals(-rc).name}"
        except ValueError:
            return f"signal {-rc}"
    return f"code {rc}"


def sh(cmd, timeout, stdin=b"", env=None, cwd=SRC):
    """Lance une commande ; ne lève jamais, renvoie un dict décrivant le résultat."""
    try:
        p = subprocess.run(
            cmd, cwd=cwd, input=stdin, capture_output=True, timeout=timeout, env=env
        )
        return {
            "rc": p.returncode,
            "stdout": _clip(p.stdout.decode("utf-8", "replace")),
            "stderr": _clip(p.stderr.decode("utf-8", "replace")),
            "timeout": False,
            "error": None,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "rc": None,
            "stdout": _clip((exc.stdout or b"").decode("utf-8", "replace")),
            "stderr": _clip((exc.stderr or b"").decode("utf-8", "replace")),
            "timeout": True,
            "error": None,
        }
    except OSError as exc:
        return {"rc": None, "stdout": "", "stderr": "", "timeout": False, "error": str(exc)}


def run_test(t, src=SRC):
    """Exécute un cas de test et compare à `expect` ou à `reference`."""
    name = t.get("name", "sans nom")
    timeout = float(t.get("timeout", 5))
    stdin = str(t.get("stdin", "")).encode()
    env = dict(os.environ, LC_ALL="C")
    env.update({k: str(v) for k, v in (t.get("env") or {}).items()})

    res = sh(list(t["cmd"]), timeout, stdin, env, cwd=src)
    ref = sh(list(t["reference"]), timeout, stdin, env, cwd=src) if t.get("reference") else None
    expect = t.get("expect") or {}

    exp_out = expect["stdout"] if "stdout" in expect else (ref["stdout"] if ref else None)
    exp_rc = expect["exit_code"] if "exit_code" in expect else (ref["rc"] if ref else 0)

    reasons = []
    if res["error"]:
        reasons.append(f"exécution impossible : {res['error']}")
    elif res["timeout"]:
        reasons.append(f"timeout après {timeout:g}s")
    elif res["rc"] is not None and res["rc"] < 0:
        reasons.append(f"crash ({describe_rc(res['rc'])})")
    else:
        if exp_rc is not None and res["rc"] != exp_rc:
            reasons.append(f"code de retour attendu {exp_rc}, obtenu {res['rc']}")
        if exp_out is not None and res["stdout"] != exp_out:
            reasons.append("sortie standard différente")

    diff = ""
    if exp_out is not None and res["stdout"] != exp_out:
        diff = "\n".join(
            difflib.unified_diff(
                exp_out.splitlines(),
                res["stdout"].splitlines(),
                "attendu",
                "obtenu",
                lineterm="",
                n=2,
            )
        )[:4000]

    return {
        "category": t.get("category", "Tests"),
        "name": name,
        "passed": not reasons,
        "reason": "; ".join(reasons),
        "rc": res["rc"],
        "expected_rc": exp_rc,
        "stdout": res["stdout"],
        "expected_stdout": exp_out,
        "stderr": res["stderr"][-2000:],
        "diff": diff,
    }


def build_checks(b, src=SRC):
    """Contrôles de build : make, binaire, pas de relink, clean/fclean/re, nm -u."""
    out = []
    timeout = float(b.get("timeout", 120))
    binary = b["binary"]
    path = os.path.join(src, binary)

    def add(name, ok, detail=""):
        out.append(
            {"category": "Build", "name": name, "passed": bool(ok), "reason": "" if ok else detail,
             "diff": "", "stdout": "", "stderr": "", "rc": None, "expected_rc": None,
             "expected_stdout": None}
        )

    r = sh(["make"], timeout, cwd=src)
    tail = (r["stderr"] or r["stdout"]).strip().splitlines()[-1:] or [""]
    add("make réussit", r["rc"] == 0, f"make : {describe_rc(r['rc'])} {tail[0]}")

    built = os.path.isfile(path) and os.access(path, os.X_OK)
    add(f"binaire {binary} présent et exécutable", built, f"{binary} absent après make")

    if built:
        m1 = os.stat(path).st_mtime_ns
        time.sleep(1.1)  # résolution mtime FAT/ext : garantit un écart mesurable
        r2 = sh(["make"], timeout, cwd=src)
        m2 = os.stat(path).st_mtime_ns
        add("second make ne relinke pas", r2["rc"] == 0 and m1 == m2,
            "le binaire est reconstruit alors que rien n'a changé")

        if b.get("allowed_functions") is not None:
            nm = sh(["nm", "-u", binary], 30, cwd=src)
            imported = set()
            for line in nm["stdout"].splitlines():
                parts = line.split()
                if len(parts) == 2 and parts[0] == "U":
                    sym = parts[1].split("@")[0]
                    if not sym.startswith(IGNORED_SYMBOL_PREFIXES):
                        imported.add(sym)
            bad = sorted(imported - set(b["allowed_functions"]))
            add("fonctions autorisées uniquement", not bad,
                "fonctions non autorisées : " + ", ".join(bad))

    sh(["make", "clean"], timeout, cwd=src)
    objs = sorted(f for f in os.listdir(src) if f.endswith(".o"))
    add("make clean supprime les .o", not objs, f"restent : {', '.join(objs)}")
    add("make clean garde le binaire", os.path.isfile(path), "binaire supprimé par make clean")

    sh(["make", "fclean"], timeout, cwd=src)
    add("make fclean supprime le binaire", not os.path.exists(path), "binaire restant après fclean")

    sh(["make", "re"], timeout, cwd=src)
    add("make re reconstruit le binaire", os.path.isfile(path), "make re n'a pas reconstruit le binaire")
    return out


def style_checks(src=SRC):
    """Coding style : epiclang sur chaque .c/.h (syntaxe seule, sans link) + banana-check-repo.
    Lancé AVANT make, pour ne pas voir les .o produits par le build."""
    c_files, include_dirs = [], set()
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in files:
            if name.endswith((".c", ".h")):
                rel = os.path.relpath(os.path.join(root, name), src)
                c_files.append(rel)
                if name.endswith(".h"):
                    include_dirs.add(os.path.relpath(root, src))
    includes = []
    for d in sorted(include_dirs):
        includes += ["-I", d]

    epi_stderr = []
    for rel in sorted(c_files):
        r = sh(["epiclang", "-fsyntax-only", *includes, rel], 60, cwd=src)
        epi_stderr.append(r["stderr"] if r["rc"] is not None else f"{rel}: error: {r['error'] or 'timeout'}")
    repo = sh(["banana-check-repo"], 60, cwd=src)
    return {
        "style_raw": "\n".join(epi_stderr),
        "repo_raw": repo["stdout"] + repo["stderr"],
        "c_files": len(c_files),
    }


def main():
    with open(SPEC, encoding="utf-8") as f:
        spec = json.load(f)
    results = {"build": [], "tests": []}
    results.update(style_checks())
    if spec.get("build"):
        results["build"] = build_checks(spec["build"])
    results["tests"] = [run_test(t) for t in spec.get("tests", [])]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
