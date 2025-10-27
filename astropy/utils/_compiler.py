"""Pure-Python fallback for astropy.utils._compiler extension.

This module provides a minimal definition to satisfy imports in
environments where building C extensions is not possible or desired
for testing purposes.
"""

# Provide a string similar to what the C extension would define.
compiler = "Python Fallback"

