"""Rendu terminal du résultat, façon my.epitech.eu : catégories, [OK]/[KO], pourcentages."""

from collections import Counter

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel


def group_by_category(result: dict) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for item in result.get("build", []):
        groups.setdefault("Build", []).append(item)
    for item in result.get("tests", []):
        groups.setdefault(item.get("category", "Tests"), []).append(item)
    return groups


def score(result: dict) -> tuple[int, int]:
    items = result.get("build", []) + result.get("tests", [])
    return sum(1 for i in items if i["passed"]), len(items)


def render(result: dict, console: Console) -> None:
    console.rule(f"[bold]vibe_mouli — {escape(result.get('project', '?'))}")
    for category, items in group_by_category(result).items():
        passed = sum(1 for i in items if i["passed"])
        pct = 100 * passed / len(items) if items else 0
        console.print(f"\n[bold]{escape(category)}[/bold] — {passed}/{len(items)} ({pct:.0f}%)")
        first_fail = None
        for item in items:
            if item["passed"]:
                console.print(f"  [green][OK][/green] {escape(item['name'])}")
            else:
                console.print(f"  [red][KO][/red] {escape(item['name'])} — {escape(item.get('reason', ''))}")
                first_fail = first_fail or item
        if first_fail and first_fail.get("diff"):
            console.print(Panel(escape(first_fail["diff"][:1500]), title=f"Premier échec : {escape(first_fail['name'])}", border_style="red"))

    style = result.get("style", [])
    counts = Counter(i["severity"] for i in style)
    console.print(
        f"\n[bold]Coding style[/bold] (approximation locale) — "
        f"MAJOR {counts['MAJOR']} · MINOR {counts['MINOR']} · INFO {counts['INFO']}"
    )
    for i in style[:15]:
        console.print(f"  {escape(i['file'])}:{i['line']}: {i['severity']}:{i['code']} {escape(i['message'])}")
    if len(style) > 15:
        console.print(f"  … {len(style) - 15} autre(s)")

    passed, total = score(result)
    pct = 100 * passed / total if total else 0
    console.rule(f"Score : {passed}/{total} ({pct:.0f}%)")
