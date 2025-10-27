# Local pytest configuration for astropy.units tests only.
# Ignore pytest deprecation about nose-style setup to allow legacy tests
# that define `def setup(self)` to run on pytest>=7, where the warning exists.
import warnings

try:
    import pytest
    PytestRemovedIn8Warning = getattr(pytest, 'PytestRemovedIn8Warning', None)
    if PytestRemovedIn8Warning is not None:
        warnings.filterwarnings('ignore', category=PytestRemovedIn8Warning)
except Exception:
    # If pytest is not importable here or no such warning exists, do nothing.
    pass

# Ignore numpy deprecation warnings that older parts of the code may trigger
# during imports (e.g., use of np.int) and distutils version class warnings,
# which otherwise get treated as errors by Astropy's test configuration.
warnings.filterwarnings(
    'ignore',
    message=r"`np\.int` is a deprecated alias for the builtin `int`\.",
    category=DeprecationWarning,
)
warnings.filterwarnings(
    'ignore',
    message=r"distutils Version classes are deprecated\.",
    category=DeprecationWarning,
)

# Older astropy test helpers can turn deprecations into errors; ensure that
# numpy deprecation warnings during import do not fail tests by default.
try:
    import numpy as _np  # noqa: F401
except Exception:
    pass
