# vibe_mouli

Simulateur de moulinette Epitech : compile et teste un projet dans l'image Docker officielle `epitechcontent/epitest-docker`, avec un rapport au format proche de my.epitech.eu.

> **État : première itération.** Fonctionnel et testé : `run` (build, tests catalogués, fichiers interdits, rapport terminal/JSON). Pas encore implémenté : `login`/`projects`/`fetch` (my.epitech.eu), génération de tests par Claude, simulation de défense, `diff`, rapport HTML. Voir « Limites ».

## Prérequis
- Python 3.11+ et Docker (testé avec Docker 29, image `epitechcontent/epitest-docker:latest`).
- Optionnel, pour plus tard : `gh` et `claude` (CLI authentifiée).

## Installation (développement)
```bash
uv venv -p 3.14 .venv && uv pip install -p .venv/bin/python -e ".[dev]"
.venv/bin/vibe_mouli --help
```
Installation utilisateur : `pipx install .` (une fois `pipx` installé).

## Utilisation
```bash
# Teste un repo local avec le catalogue tests/catalog/<nom du dossier>
vibe_mouli run ./examples/my_ls_partial

# Catalogue explicite, export JSON, image figée
vibe_mouli run ~/projets/my_ls --catalog tests/catalog/my_ls --json resultat.json --image epitechcontent/epitest-docker@sha256:20a7d00ea4c6ac6b8cbc4663de385ba0bd10c83a4fe4384c55785a4c30841700
```

Chaque exécution : copie du repo (le repo original n'est jamais modifié), conteneur **sans réseau**, 1 CPU, `--memory` (512 Mo par défaut), 256 PIDs max, `no-new-privileges`, timeout par test.

## Ajouter un projet au catalogue
Créer `tests/catalog/<nom>/` avec :

`project.yml`
```yaml
name: my_ls
binary: my_ls
allowed_functions: [opendir, readdir, printf, puts, malloc, free]   # optionnel ; sinon pas de contrôle
build_timeout: 120
```

`tests.yml`
```yaml
tests:
  - name: listing simple
    category: Listing           # une catégorie = une section du rapport
    cmd: ["./my_ls", "fixtures"]
    reference: ["ls", "fixtures"]   # oracle : stdout et code de retour du programme de référence
  - name: dossier inexistant
    category: Erreurs
    cmd: ["./my_ls", "nope"]
    expect: {exit_code: 84, stdout: ""}   # ou attendu explicite
    timeout: 5                  # secondes (défaut 5)
```
Les variables `LC_ALL=C` sont imposées pour rendre `ls` déterministe. `stdin` et `env` sont aussi supportés.

## Exemples
`examples/` contient des projets jouets qui prouvent le comportement de l'outil :
- `my_ls_partial` : listing OK, `-a`/`-r` KO (attendu) ;
- `crash` : segfault détecté (`SIGSEGV`) ;
- `loop` : boucle infinie détectée (timeout) ;
- `relink` : `make` relinke sans changement → KO ;
- `style_faults` : lignes trop longues, espaces, tabulations (approximation de style).

## Tests de l'outil
```bash
.venv/bin/python -m pytest -q
```

## Limites connues
- **Coding style** : le checker officiel (`ghcr.io/epitech/coding-style-checker`) n'est pas accessible publiquement ; seules 3 règles locales approximatives sont appliquées (voir `docs/RESEARCH.md`). Le parseur du format officiel est prêt mais non validé contre un vrai log.
- **Criterion** absent de l'image : pas de tests unitaires criterion.
- **my.epitech.eu** : non implémenté ; endpoints non confirmés.
- Catalogue : seuls les 5 projets jouets existent ; `my_sudo`, `organized`, `minishell1`, `my_ls` complet ne sont pas encore écrits.
- Valgrind (`--valgrind`) et couverture gcovr : non implémentés.
