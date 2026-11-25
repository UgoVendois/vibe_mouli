"""Exécution du driver et des tests dans l'image epitest, sans réseau, avec limites."""

import json
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

DEFAULT_IMAGE = "epitechcontent/epitest-docker:latest"
DRIVER = Path(__file__).with_name("driver.py")


class DockerError(RuntimeError):
    pass


def check_docker() -> str:
    try:
        r = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DockerError(f"Docker indisponible : {exc}") from exc
    if r.returncode != 0:
        raise DockerError("Docker indisponible : " + r.stderr.strip()[:300])
    return r.stdout.strip()


def run_job(repo: Path, spec: dict, *, image: str = DEFAULT_IMAGE, memory: str = "512m",
            cpus: str = "1", pids: int = 256, timeout: int = 900) -> dict:
    """Copie le repo (le repo original n'est jamais monté en écriture), lance le driver
    dans le conteneur et renvoie les résultats JSON."""
    with tempfile.TemporaryDirectory(prefix="vibe_mouli_") as tmp:
        base = Path(tmp)
        src, vm, out = base / "src", base / "vm", base / "out"
        shutil.copytree(repo, src, ignore=shutil.ignore_patterns(".git"), symlinks=True)
        vm.mkdir()
        out.mkdir()
        (vm / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
        shutil.copy(DRIVER, vm / "driver.py")

        name = f"vibe-mouli-{uuid.uuid4().hex[:12]}"
        cmd = [
            "docker", "run", "--rm", "--name", name,
            "--network", "none",
            "--memory", memory, "--memory-swap", memory,
            "--cpus", cpus,
            "--pids-limit", str(pids),
            "--security-opt", "no-new-privileges",
            "-v", f"{src}:/job/src",
            "-v", f"{vm}:/opt/vm:ro",
            "-v", f"{out}:/out",
            "-w", "/job/src",
            image, "python3", "-I", "/opt/vm/driver.py",
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            subprocess.run(["docker", "kill", name], capture_output=True)
            raise DockerError(f"délai global dépassé ({timeout}s)") from exc

        result_file = out / "results.json"
        if not result_file.is_file():
            tail = (proc.stderr or proc.stdout)[-800:]
            raise DockerError(f"le driver n'a pas produit de résultats (rc={proc.returncode}) : {tail}")
        return json.loads(result_file.read_text(encoding="utf-8"))
