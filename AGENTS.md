# Repository Guidelines

## Project Structure & Module Organization
- `app/` Blender integration utilities and entry points.
- `asset_manager/` asset registry, loaders, validation, and CLI helpers.
- `assets/` Blender `.blend` files and `asset_registry.json` (treat as large/binary).
- Domain modules: `building/`, `road/`, `renderer/`, `route/`, `routecam/`, `setup/`, `util/`.
- `gui/` UI panels, properties, and operators (see `gui/README.md`).
- `config/` runtime JSON (e.g., `config/render_config.json`).
- Add‑on package root at top‑level `__init__.py`.

## Build, Test, and Development Commands
- Format/lint (optional but recommended): `black .` and `ruff check .`
- Quick syntax check: `py -m compileall .` (Windows) or `python -m compileall .`
- Headless Blender smoke test: `blender --background --python assets/compositor_script.py`
- Enable for development: copy/symlink this folder into Blender’s add‑ons directory, then enable in Preferences.

## Coding Style & Naming Conventions
- Python (Blender 4.x compatible). Use 4‑space indentation.
- Names: snake_case for functions/vars, PascalCase for classes, UPPER_SNAKE_CASE for constants, packages/modules lower_snake_case.
- Keep modules focused; prefer small, composable helpers (e.g., `util/`, `asset_manager/`).

## Testing Guidelines
- If adding tests, place them under `tests/`, mirroring package paths; name files `test_*.py`.
- Use `pytest` for pure‑Python units (e.g., `util/`, `asset_manager/`).
- For Blender‑dependent paths, prefer headless runs: `blender --background -P tests/<script>.py`.
- Target coverage on non‑Blender logic; use smoke tests for Blender operators.

## Commit & Pull Request Guidelines
- Messages: imperative, scope‑prefixed (e.g., `route: fix preview bounds`, `gui: add extent panel`).
- PRs include: concise summary, before/after (screenshots for GUI), reproduction/verification steps, and linked issues.
- Avoid committing large binaries unless required; prefer Git LFS for `.blend`.

## Security & Configuration Tips
- Don’t commit secrets; sanitize JSON (e.g., `asset_registry.json`).
- Treat `assets/` as read‑only at runtime; validate external file paths.
- Exclude backups (`*.blend1`, `backup/`) unless specifically needed.
