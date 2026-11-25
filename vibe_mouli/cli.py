"""Point d'entrée `vibe_mouli`."""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from vibe_mouli import __version__, catalog, docker_runner, report, static_checks

app = typer.Typer(help="Simulateur de moulinette + défense Epitech.", no_args_is_help=True,
                  add_completion=False)
console = Console()
CATALOG_ROOT = Path(__file__).resolve().parent.parent / "tests" / "catalog"


@app.command()
def version() -> None:
    """Affiche la version."""
    console.print(__version__)


@app.command()
def run(
    project: Path = typer.Argument(..., exists=True, file_okay=False, help="Repo local du projet."),
    catalog_dir: Optional[Path] = typer.Option(None, "--catalog", help="Dossier avec project.yml et tests.yml (défaut : tests/catalog/<nom du dossier>)."),
    image: str = typer.Option(docker_runner.DEFAULT_IMAGE, "--image", help="Image epitest."),
    memory: str = typer.Option("512m", "--memory", help="Limite RAM du conteneur."),
    json_out: Optional[Path] = typer.Option(None, "--json", help="Écrit le résultat en JSON."),
) -> None:
    """Compile et teste un projet dans l'image epitest, puis affiche le rapport."""
    project = project.resolve()
    cdir = (catalog_dir or CATALOG_ROOT / project.name).resolve()
    try:
        project_cfg, tests = catalog.load(cdir)
        spec = catalog.build_spec(project_cfg, tests)
        docker_runner.check_docker()
        console.print(f"[dim]Image : {image} · mémoire {memory} · réseau désactivé[/dim]")
        result = docker_runner.run_job(project, spec, image=image, memory=memory)
    except (catalog.CatalogError, docker_runner.DockerError) as exc:
        console.print(f"[red]Erreur :[/red] {exc}")
        raise typer.Exit(code=2)

    style_raw = result.pop("style_raw", "")
    style_items = static_checks.parse_epiclang(style_raw)
    repo_items = static_checks.parse_banana_repo(result.pop("repo_raw", ""))
    result["build"].append({
        "category": "Build", "name": "banana-check-repo : aucune infraction (C-O)",
        "passed": not repo_items,
        "reason": "" if not repo_items else ", ".join(f"{i.file} ({i.code})" for i in repo_items),
        "diff": "", "stdout": "", "stderr": "", "rc": None, "expected_rc": None, "expected_stdout": None,
    })
    result["style"] = [i.as_dict() for i in style_items]
    result["style_errors"] = static_checks.epiclang_errors(style_raw)
    result["project"] = project_cfg.get("name", project.name)

    report.render(result, console)
    if json_out:
        json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        console.print(f"[dim]JSON écrit dans {json_out}[/dim]")


if __name__ == "__main__":
    app()
