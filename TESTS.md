
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
- Editable install of the source tree
  - python -m pip install -e .

3) Installing test and development extras
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
- Filter by subpackage (-P; pytest-filter-subpackage)
  - python -m pytest -P wcs,utils
- Filter by keyword (-k)
  - python -m pytest --pyargs astropy -k "table and not io"
- Re-run last failures
  - python -m pytest --pyargs astropy --last-failed
- Single test file / function
  - python -m pytest astropy/table/tests/test_table.py::test_init_from_dict
- Parallelize (pytest-xdist)
  - python -m pytest --pyargs astropy -n auto
- Notes
  - Test and warning filters are configured in pyproject.toml under [tool.pytest.ini_options].

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

7) Running tests against an installed astropy (outside repo)
- Install:
  - python -m pip install "astropy[test]"
- Run:
  - python -m pytest --pyargs astropy

8) Running tests via tox
- List environments
  - tox -l -v
- Common py312 environments
  - tox -e py312-test
  - tox -e py312-test-alldeps
  - tox -e py312-test-cov
  - tox -e py311-test-image-mpl380-cov (image tests; see image section)
- Pass pytest args through tox
  - tox -e py312-test -- -k "wcs and not io" -n auto
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
- Remote-data requirement
  - Image envs include --remote-data
- Run only image tests
  - python -m pytest --pyargs astropy -m mpl_image_compare --mpl --mpl-generate-summary=html

10) Locale (clocale) environments
- When to use
  - Locale-sensitive behavior or CI reproduction
- Run
  - tox -e py312-test-clocale
- Caveats
  - LC_ALL/LC_CTYPE are set to C/C.ascii and may change formatting behavior.

11) Fork versioning note (setuptools_scm)
- In forks without upstream tags, setuptools_scm may yield 0.1.dev* which can cause doctest minversion failures.
- Workarounds
  1) Pretend version (Linux/macOS):
     - export SETUPTOOLS_SCM_PRETEND_VERSION=7.1.1
     - python -m pip install -e .
     - python -m pytest --pyargs astropy
  2) Add a v7.x tag in your fork:
     - git tag -a v7.1.1 -m "Align version with upstream"
     - git push origin v7.1.1

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
