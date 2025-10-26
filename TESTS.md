Astropy test guide

Prerequisites
- Python 3.11–3.13 (prefer 3.12 or 3.13)
- pip; optional tox
- Dependencies: install test extras (pytest, pytest-xdist, pytest-astropy*, pytest-doctestplus, pytest-mpl; matplotlib, fitsio optional)

Setup
- pip install -e .[test]

Run tests
- Core tests: python -m pytest --pyargs astropy docs -n auto
- Coverage: python -m pytest --pyargs astropy docs --cov astropy --cov-report xml
- Image tests (optional; require internet/baselines): python -m pytest --pyargs astropy docs --mpl --remote-data

Tox environments (optional)
- List envs: tox -l -v
- Examples:
  - tox -e py312-test - core tests
  - tox -e py312-test-cov - with coverage
  - tox -e py311-test-image-mpl380-cov - image tests with pinned Matplotlib and coverage

Troubleshooting
- Image comparison tests are sensitive and may need baseline images; run without image tests if environment differs.
- Locale/hypothesis tests can be slow/fragile; run serially to debug.
