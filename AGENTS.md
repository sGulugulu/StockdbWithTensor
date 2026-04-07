# Repository Guidelines

## Rules
- Make the smallest change that fixes the issue.
- Always show a plan before editing.
- Before finishing: run tests (or explain why you cannot).
- Never commit secrets (.env, keys) or credentials.
- 请在每次排障时，严格遵循 skills/bugfix.md 中定义的流程卡片。

## Project Structure & Module Organization
This repository currently stores thesis deliverables at the root, including proposal, literature review, translation, slides, and working notes such as `毕设.md`. Keep these source documents in place. Put all runnable code under `code/` so research files and implementation stay separate. If you add scripts, organize them by purpose, for example `code/data/`, `code/models/`, `code/notebooks/`, and `code/tests/`.

## Build, Test, and Development Commands
There is no committed build pipeline yet, so keep workflow simple and reproducible.

- `git status`: check pending changes before editing or submitting work.
- `Get-ChildItem code`: inspect the current implementation area.
- `rg --files`: list tracked source files quickly once code is added.
- `python3 -m venv .venv`: create the local virtual environment for WSL/Linux validation.
- `.venv/bin/python -m pip install -r requirements.txt`: install runtime and API dependencies.
- `.venv/bin/python code/main.py --config code/configs/sample_cn_smoke.yaml`: run the smoke-test tensor-factorization experiment pipeline.
- `.venv/bin/python -m unittest discover -s code/tests`: run the automated test suite.

If you introduce Python or another runtime, add a single documented entry point such as `python code/main.py` or `pytest code/tests`, then update this guide and the project README in the same change.

## Coding Style & Naming Conventions
Use 4 spaces for indentation in Python and keep line length reasonable, preferably under 100 characters. Name Python files and modules in `snake_case`, classes in `PascalCase`, and functions or variables in `snake_case`. Use descriptive names tied to the finance and tensor-factorization domain, such as `factor_tensor.py` or `train_cp_model.py`. Keep notebooks exploratory; move reusable logic into `.py` files.

## Testing Guidelines
No test framework is present yet. When adding code, also add automated tests under `code/tests/`. Name test files `test_<module>.py` and keep each test focused on one behavior, such as tensor construction, factor normalization, or metric calculation. Prefer deterministic fixtures over manual spreadsheet checks.

## Commit & Pull Request Guidelines
This repository has no commit history yet, so there is no established convention to inherit. Start with short, imperative commit messages such as `add tensor preprocessing script` or `document experiment inputs`. For pull requests, include a clear summary, affected paths, validation steps, and screenshots only when notebooks or figures change. Link the related thesis task or milestone when applicable.

## Document Handling
Do not rename or overwrite the original `.doc`, `.docx`, or `.pptx` files without a clear reason. Add generated datasets, charts, or exported results inside `code/outputs/` or another dedicated subdirectory instead of cluttering the repository root.

<!-- TRELLIS:START -->
# Trellis Instructions

These instructions are for AI assistants working in this project.

Use the `/trellis:start` command when starting a new session to:
- Initialize your developer identity
- Understand current project context
- Read relevant guidelines

Use `@/.trellis/` to learn:
- Development workflow (`workflow.md`)
- Project structure guidelines (`spec/`)
- Developer workspace (`workspace/`)

Keep this managed block so 'trellis update' can refresh the instructions.

<!-- TRELLIS:END -->
