# Compte-rendu de recherche (vérifié le 2026-11-25)

## 1. Image de la moulinette — `epitechcontent/epitest-docker`
- Repo : https://github.com/Epitech/epitest-docker (public). Build : `build.sh --tag <tag>` ; tags attendus : `latest`, `devel`, `coverage`.
- Image présente localement : `epitechcontent/epitest-docker:latest`, digest `sha256:20a7d00ea4c6…` (ID `118ee295d416`), 11.9 GB.
- Base : **Ubuntu 26.04.1 LTS**.
- Outils vérifiés dans le conteneur : gcc 15.2.0, clang 21.1.8, valgrind, gcovr, python3, tcsh, bash, sudo, ls, nm (binutils). Bibliothèques : CSFML, SDL2, ncurses (headers présents).
- **Criterion absent** (`/usr/include/criterion` introuvable) : les tests unitaires `criterion` ne sont pas exécutables tels quels — à traiter plus tard.
- Pin : la config doit fixer le digest `sha256:20a7d00e…` plutôt que `latest`. (Pas encore fait : `--image` par défaut = `latest`.)

## 2. Coding style checker — **non vérifié, accès impossible**
- `ghcr.io/epitech/coding-style-checker:latest` : **introuvable** (`docker pull` → « not found », tenté le 2026-11-25).
- `github.com/Epitech/coding-style-checker` : 404 via `gh api` (repo privé ou renommé).
- Indices publics : le checker s'appuie sur **Vera++** (banana-vera) ; un script tiers monte un dossier de rapports dans l'image — nom exact du log **non confirmé** (cf. https://gist.github.com/Sigmanificient/6ef147920ad057ef6bcd9b057f81d83d et https://awesome.ecosyste.ms/projects/github.com%2FEpitech%2Fcoding-style-checker).
- Conséquence : le **parseur** suit le format du PROMPT (`fichier:ligne: GRAVITÉ:C-XX`), mais la **liste des règles n'est pas établie**. Le coding style affiché est une **approximation locale** (80 colonnes, espaces fin de ligne, tabulations), étiquetée `LOCAL-*`.

## 3. my.epitech.eu / api.epitest.eu — **non recherché à ce stade**
- Pas d'accès authentifié dans cette session : endpoints (`/me/<année>`, `/me/details/<id>`), format de réponse, méthode d'auth (SSO Microsoft → bearer) **non confirmés**. À observer dans le navigateur de l'utilisateur (Claude in Chrome ou DevTools) avant d'implémenter `login`.

## 4. Repos GitHub des projets
- Non vérifié (nommage `B-PSU-…`, orgas `EpitechPromo*` / `Epitech<Année>`) : à confirmer avec un repo réel de l'utilisateur.

## 5. Règles d'une moulinette réelle
- Non validées contre une vraie moulinette. Le socle implémente : `make` réussit, binaire exécutable, pas de relink, `clean`/`fclean`/`re`, fichiers interdits, fonctions autorisées via `nm -u`. Les listes exactes et les flags interdits sont à compléter par projet dans `project.yml`.

## 6. Claude CLI (`claude 2.1.332`) — flags vérifiés via `claude --help`
- Headless : `-p/--print`, `--output-format json`, `--json-schema <schema>`, `--model`.
- Restriction d'outils : `--allowedTools`, `--disallowedTools`, `--tools` (lecture seule à utiliser pour les sous-appels).
- Contexte : `--append-system-prompt`, `--add-dir`, `--bare` (sans hooks), `--max-budget-usd`, `--no-session-persistence`.
- Pas encore utilisé par le socle (étape 6 du plan).

## 7. Outillage Python
- `pipx` absent ; `uv 0.13.9` présent. Environnement : `.venv` créé avec `uv venv -p 3.14`, dépendances : pyyaml, rich, typer, pytest.

## Sources
- https://github.com/Epitech/epitest-docker (README via `gh api`)
- https://gist.github.com/Sigmanificient/6ef147920ad057ef6bcd9b057f81d83d
- https://awesome.ecosyste.ms/projects/github.com%2FEpitech%2Fcoding-style-checker
- https://github.com/Epitech/coding-style-checker → 404 (vérifié)
