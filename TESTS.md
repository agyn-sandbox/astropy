
Astropy test guide

1) Overview
This guide explains how to run Astropy tests locally using pytest and via tox. It covers environment setup, extras, common pytest options, remote-data handling, coverage, running against installed astropy, image comparison tests, locale-related environments, a fork versioning note, and troubleshooting.

2) Prerequisites and environment setup
- Supported Python versions
  - CPython 3.11–3.14 per pyproject.toml (requires-python >= 3.11; classifiers include 3.11–3.14). Recommended: Python 3.12 or 3.13.
- Create and activate a virtual environment
  - Linux/macOS:
    - python3 -m venv .venv
    - source .venv/bin/activate
  - Windows (PowerShell):
    - py -3 -m venv .venv
    - .venv\Scripts\Activate.ps1
- Upgrade packaging tools
  - python -m pip install --upgrade pip setuptools wheel
- Install the package in editable mode with the desired extra (choose one in section 3). Do not run a plain `-e .` first to avoid double editable installs.

3) Installing test and development extras (pick one)
- Minimal for running tests:
  - python -m pip install -e ".[test]"
- For broader feature coverage:
  - python -m pip install -e ".[test_all]"
- Full developer environment:
  - python -m pip install -e ".[dev_all]"
- When to use which
  - [test]: fastest setup; for working on core or pure-Python changes.
  - [test_all]: for validating functionality requiring optional deps; recommended before submitting broader changes.
  - [dev_all]: for contributors who also build docs, run type checks, and use tox regularly.

4) Running tests directly with pytest
- Full suite (package + docs)
  - python -m pytest --pyargs astropy docs
- Package tests only
  - python -m pytest --pyargs astropy
- Docs tests only
  - python -m pytest docs
- Filter by subpackage (-P)
  - Requires the pytest-filter-subpackage plugin. It is commonly provided via pytest-astropy (installed by the [test] extras); if missing, install explicitly: `python -m pip install pytest-filter-subpackage`.
  - Examples:
    - python -m pytest --pyargs astropy -P wcs,utils
- Filter by keyword (-k)
  - python -m pytest --pyargs astropy -k "table and not io"
- Re-run last failures
  - python -m pytest --pyargs astropy --last-failed
- Single test file / function
  - python -m pytest astropy/table/tests/test_table.py::test_init_from_dict
- Parallelize (pytest-xdist)
  - python -m pytest --pyargs astropy -n auto
- Notes
  - Tests are discovered under `testpaths = ["astropy", "docs"]` and docs doctests are enabled by default via `--doctest-rst` in `pyproject.toml` under `[tool.pytest.ini_options]`.
  - `remote_data_strict = true` in `pyproject.toml` means doctest blocks requiring remote data are skipped unless `--remote-data` is provided.

5) Remote data tests
- Default: skipped by default
- Enable all remote data
  - python -m pytest --pyargs astropy --remote-data=any
- Enable only data.astropy.org sources
  - python -m pytest --pyargs astropy --remote-data=astropy
- Docs remote-data blocks may require --remote-data
- Caching: tests isolate caches per run using temporary directories.

6) Coverage
- XML-only (as in CI):
  - python -m pytest --pyargs astropy docs --cov astropy --cov-config=pyproject.toml --cov-report xml:coverage.xml
- HTML + XML:
  - python -m pytest --pyargs astropy docs --cov astropy --cov-config=pyproject.toml --cov-report html --cov-report xml:coverage.xml
- Notes
  - These invocations mirror CI. Coverage omit and exclude patterns are configured in `pyproject.toml` under `[tool.coverage.run]` and `[tool.coverage.report]`.

7) Running tests against an installed astropy (outside repo)
- Install:
  - python -m pip install "astropy[test]"
- Run:
  - python -m pytest --pyargs astropy

8) Running tests via tox
- List environments
  - tox -l -v
- Common py312 environments (py311/py313 variants are also available)
  - tox -e py312-test
  - tox -e py312-test-alldeps
  - tox -e py312-test-cov
  - tox -e py312-test-clocale
  - tox -e py312-test-fitsio
  - tox -e py312-test-noscipy
  - tox -e py312-test-numpy124
  - tox -e py312-test-numpy125
  - tox -e py311-test-image-mpl380-cov (image tests; see image section)
- Pass pytest args through tox
  - tox -e py312-test -- -k "wcs and not io" -n auto
  - tox -e py312-test -- -P wcs,utils
  - tox -e py312-test -- --remote-data=any
- Recreate env
  - tox -r -e py312-test
- Note: tox runs in .tmp/{envname} to avoid importing from the source tree.

9) Image comparison tests
- Prerequisites
  - python -m pip install -e ".[test]" matplotlib pytest-mpl
  - Some image tests also require scipy
- Baselines and hashes
  - Hash library: astropy/tests/figures/{envname}.json
  - Baseline path: https://raw.githubusercontent.com/astropy/astropy-figure-tests/astropy-main/figures/{envname}/
  - Exact figure hash files exist for:
    - py311-test-image-mpl380-cov
    - py311-test-image-mpldev-cov
  - Note: Only the py311 image environments have published hash files at this time; do not assume py312/py313 image hash support.
- Remote-data requirement
  - Image envs include --remote-data
- Run only image tests
  - python -m pytest --pyargs astropy -m mpl_image_compare --mpl --mpl-generate-summary=html
- Reproducible local run mirroring tox MPLFLAGS
  - Example (Linux/macOS) matching `py311-test-image-mpl380-cov` tox settings:
    - python -m pytest --pyargs astropy -m mpl_image_compare \
        --mpl \
        --mpl-generate-summary=html \
        --mpl-results-path=./results \
        --mpl-hash-library=astropy/tests/figures/py311-test-image-mpl380-cov.json \
        --mpl-baseline-path=https://raw.githubusercontent.com/astropy/astropy-figure-tests/astropy-main/figures/py311-test-image-mpl380-cov/ \
        --remote-data

10) Locale (clocale) environments
- When to use
  - Locale-sensitive behavior or CI reproduction
- Run
  - tox -e py312-test-clocale
- Caveats
  - LC_ALL/LC_CTYPE are set to C/C.ascii and may change formatting behavior.

11) Fork versioning note (setuptools_scm)
- Scope: local testing only. In forks without upstream tags, setuptools_scm may yield 0.1.dev* which can cause doctest minversion failures.
- Workarounds
  1) Pretend version (Linux/macOS) — local only:
     - export SETUPTOOLS_SCM_PRETEND_VERSION=7.1.1
     - python -m pip install -e .
     - python -m pytest --pyargs astropy
  2) Add an annotated tag in your fork (align with upstream):
     - git tag -a v7.1.1 -m "Align version with upstream"
     - git push origin v7.1.1
     - Caution: ensure tags you add match upstream's versioning scheme and are annotated; avoid creating conflicting tags in public forks.

12) Troubleshooting
- Warnings treated as errors: pinpoint with -k or -x; do not relax filters globally.
- Missing optional deps: use -e ".[test_all]" or install the specific package.
- Remote-data disabled: add --remote-data=any.
- Locale issues: try tox -e py312-test-clocale.
- Re-run failing tests quickly: --last-failed, -x, -vv.
- Reporting issues: include OS, Python, install commands, pytest command/output, and whether remote-data was enabled.

Appendix: quick start
- Setup
  - python -m pip install --upgrade pip
  - python -m pip install -e ".[test]"
- Full suite
  - python -m pytest --pyargs astropy docs -n auto
- With remote data
  - python -m pytest --pyargs astropy --remote-data=any
- Coverage (XML)
  - python -m pytest --pyargs astropy docs --cov astropy --cov-config=pyproject.toml --cov-report xml:coverage.xml
- Tox (core)
  - tox -e py312-test -- --maxfail=1 -q
