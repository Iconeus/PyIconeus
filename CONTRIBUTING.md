# Contributing to PyIconeus

## Development Workflow

Use the `dev` branch as the base for branch creation. The `dev` branch is reserved for internal devs. The `master` branch is reserved for stable and release-ready changes.

Create a virtual environment and install the project with its development
dependencies:

```console
python -m pip install -e ".[test,dev]"
```

Hatch can also manage the test environment:

```console
hatch test
```

## Local Checks

Run the same checks used by continuous integration before opening a pull
request:

```console
hatch test -c
ruff check .
ruff format --check .
mypy --install-types --non-interactive src/pyiconeus tests
```

The test suite must maintain at least 90% total coverage. Test data is expected
to be available under `tests/data/`. It is hosted on Zenodo and can be fetched
with `python download_script.py`.

[![Test data DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21807850.svg)](https://doi.org/10.5281/zenodo.21807850)

## Pull Requests

- Keep each pull request focused on one change.
- Add or update tests for behavioral changes.
- Describe compatibility or data-format implications in the pull request.
- Confirm that tests, coverage, linting, formatting, and type checking pass.
- Iconeus's devs will merge PRs on `dev` after review.

## Commits

Use Conventional Commit subjects

```text
build, chore, ci, docs, feat, fix, perf, refactor, revert, style, test
```

Examples:

```text
fix: handle truncated scan timing data
refactor: split HDF5 scan loading
docs: update contribution guidance
```

Keep commits small enough to review independently and avoid combining unrelated
refactors with functional changes.

## Releases

Changes are developed and reviewed on `dev`. Release-ready changes can then be
merged into `master` after the full CI suite passes. Update the package version in
`src/pyiconeus/__about__.py` as part of release preparation.
