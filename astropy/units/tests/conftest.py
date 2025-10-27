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
# scoped to astropy.table and units tests where legacy patterns are present.
warnings.filterwarnings(
    'ignore',
    message=r"`np\.int` is a deprecated alias for the builtin `int`\.",
    category=DeprecationWarning,
    module=r"astropy\.table\..*",
)
warnings.filterwarnings(
    'ignore',
    message=r"`np\.float` is a deprecated alias for the builtin `float`\.",
    category=DeprecationWarning,
    module=r"astropy\.table\..*",
)
warnings.filterwarnings(
    'ignore',
    message=r"`np\.str` is a deprecated alias for the builtin `str`\.",
    category=DeprecationWarning,
    module=r"astropy\.table\..*",
)
warnings.filterwarnings(
    'ignore',
    message=r"`np\.unicode` is a deprecated alias for `np\.compat\.unicode`\.",
    category=DeprecationWarning,
    module=r"astropy\.table\..*",
)
warnings.filterwarnings(
    'ignore',
    message=r"distutils Version classes are deprecated\.",
    category=DeprecationWarning,
    module=r"astropy\.(units|table)\..*",
)

# Older astropy test helpers can turn deprecations into errors; ensure that
# numpy deprecation warnings during import do not fail tests by default.
try:
    import numpy as _np  # noqa: F401
except Exception:
    pass

# Ensure deprecations-as-exceptions ignores our targeted patterns as well.
try:
    from astropy.tests import helper as _ah
    _ah._warnings_to_ignore_by_pyver.setdefault(None, set()).update({
        r"`np\.int` is a deprecated alias for the builtin `int`\.",
        r"`np\.float` is a deprecated alias for the builtin `float`\.",
        r"`np\.str` is a deprecated alias for the builtin `str`\.",
        r"`np\.unicode` is a deprecated alias for `np\.compat\.unicode`\.",
        r"distutils Version classes are deprecated\."
    })
except Exception:
    pass
