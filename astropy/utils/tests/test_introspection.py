# Licensed under a 3-clause BSD style license - see LICENSE.rst

# namedtuple is needed for find_mod_objs so it can have a non-local module
from collections import namedtuple

import pytest

from .. import introspection
from ..introspection import (find_current_module, find_mod_objs,
                             isinstancemethod, minversion)


def test_pkg_finder():
    """
    Tests that the `find_current_module` function works. Note that
    this also implicitly tests compat.misc._patched_getmodule
    """
    mod1 = 'astropy.utils.introspection'
    mod2 = 'astropy.utils.tests.test_introspection'
    mod3 = 'astropy.utils.tests.test_introspection'
    assert find_current_module(0).__name__ == mod1
    assert find_current_module(1).__name__ == mod2
    assert find_current_module(0, True).__name__ == mod3


def test_find_current_mod():
    from sys import getrecursionlimit

    thismodnm = __name__

    assert find_current_module(0) is introspection
    assert find_current_module(1).__name__ == thismodnm
    assert find_current_module(getrecursionlimit() + 1) is None

    assert find_current_module(0, True).__name__ == thismodnm
    assert find_current_module(0, [introspection]).__name__ == thismodnm
    assert find_current_module(0, ['astropy.utils.introspection']).__name__ == thismodnm

    with pytest.raises(ImportError):
        find_current_module(0, ['faddfdsasewrweriopunjlfiurrhujnkflgwhu'])


def test_find_mod_objs():
    lnms, fqns, objs = find_mod_objs('astropy')

    # this import  is after the above call intentionally to make sure
    # find_mod_objs properly imports astropy on its own
    import astropy

    # just check for astropy.test ... other things might be added, so we
    # shouldn't check that it's the only thing
    assert 'test' in lnms
    assert astropy.test in objs

    lnms, fqns, objs = find_mod_objs(__name__, onlylocals=False)
    assert 'namedtuple' in lnms
    assert 'collections.namedtuple' in fqns
    assert namedtuple in objs

    lnms, fqns, objs = find_mod_objs(__name__, onlylocals=True)
    assert 'namedtuple' not in lnms
    assert 'collections.namedtuple' not in fqns
    assert namedtuple not in objs


def test_minversion():
    from types import ModuleType
    test_module = ModuleType(str("test_module"))
    test_module.__version__ = '0.12.2'
    good_versions = ['0.12', '0.12.1', '0.12.0.dev']
    bad_versions = ['1', '1.2rc1']
    for version in good_versions:
        assert minversion(test_module, version)
    for version in bad_versions:
        assert not minversion(test_module, version)


def test_minversion_various_comparisons():
    # Cover comparisons that previously raised TypeError or behaved incorrectly
    from types import ModuleType

    def mk(ver):
        m = ModuleType(str('m'))
        m.__version__ = ver
        return m

    # '1.14.3' >= '1.14dev' -> True (inclusive default)
    assert minversion(mk('1.14.3'), '1.14dev') is True

    # '1.14dev' >= '1.14.3' -> False
    assert minversion(mk('1.14dev'), '1.14.3') is False

    # Inclusive flag behavior on equal versions
    assert minversion(mk('1.0'), '1.0', inclusive=True) is True
    assert minversion(mk('1.0'), '1.0', inclusive=False) is False

    # Pre-release behavior
    assert minversion(mk('1.14rc1'), '1.14') is False
    assert minversion(mk('1.14rc1'), '1.14rc1', inclusive=True) is True
    assert minversion(mk('1.14rc1'), '1.14rc1', inclusive=False) is False

    # Post-release
    assert minversion(mk('1.0.post1'), '1.0') is True
    assert minversion(mk('1.0'), '1.0.post1') is False

    # Local version
    assert minversion(mk('1.0+local.1'), '1.0') is True
    assert minversion(mk('1.0'), '1.0+local.1') is False

    # Legacy normalization (LooseVersion fallback normalization equivalence)
    assert minversion(mk('1.14dev'), '1.14.dev0', inclusive=True) is True


def test_minversion_fallback_pkg_resources(monkeypatch):
    # Force packaging missing to use pkg_resources.parse_version
    import sys
    # Temporarily remove packaging
    saved_packaging = sys.modules.pop('packaging', None)
    try:
        from types import ModuleType

        def mk(ver):
            m = ModuleType(str('m'))
            m.__version__ = ver
            return m

        # Behavior under pkg_resources path
        assert minversion(mk('1.14.3'), '1.14dev') is True
        assert minversion(mk('1.14dev'), '1.14.3') is False
        assert minversion(mk('1.0+local.1'), '1.0') is True
        # Invalid version inputs should not raise and return False
        assert minversion(mk('invalid'), '1.0') is False
        assert minversion(mk('1.0'), 'invalid') is False
    finally:
        if saved_packaging is not None:
            sys.modules['packaging'] = saved_packaging


def test_minversion_fallback_legacy(monkeypatch):
    # Force both packaging and pkg_resources missing to use legacy comparator
    import sys
    saved_packaging = sys.modules.pop('packaging', None)
    saved_pkg_resources = sys.modules.pop('pkg_resources', None)
    try:
        from types import ModuleType

        def mk(ver):
            m = ModuleType(str('m'))
            m.__version__ = ver
            return m

        assert minversion(mk('1.14.3'), '1.14dev') is True
        assert minversion(mk('1.14dev'), '1.14.3') is False
        # Pre-release and post/local behavior
        assert minversion(mk('1.14rc1'), '1.14') is False
        assert minversion(mk('1.0.post1'), '1.0') is True
        assert minversion(mk('1.0+local.1'), '1.0') is True
        # Invalid version inputs should not raise and return False
        assert minversion(mk('invalid'), '1.0') is False
        assert minversion(mk('1.0'), 'invalid') is False
    finally:
        if saved_packaging is not None:
            sys.modules['packaging'] = saved_packaging
        if saved_pkg_resources is not None:
            sys.modules['pkg_resources'] = saved_pkg_resources
