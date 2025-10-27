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


def test_minversion_pep440_semantics():
    """PEP 440 comparison semantics and inclusive/exclusive behavior."""
    from types import ModuleType

    # 1) dev vs release: have '1.14.3' >= '1.14dev'
    mod_dev = ModuleType(str("mod_dev"))
    mod_dev.__version__ = '1.14.3'
    assert minversion(mod_dev, '1.14dev')
    assert minversion(mod_dev, '1.14dev', inclusive=False)

    # 2) pre-release lower than final: '1.14.dev0' < '1.14'
    mod_prerelease = ModuleType(str("mod_prerelease"))
    mod_prerelease.__version__ = '1.14.dev0'
    assert not minversion(mod_prerelease, '1.14')

    # 3) equality boundary
    mod_equal = ModuleType(str("mod_equal"))
    mod_equal.__version__ = '1.14.0'
    assert minversion(mod_equal, '1.14.0')
    assert not minversion(mod_equal, '1.14.0', inclusive=False)

    # 4) rc vs final
    mod_rc = ModuleType(str("mod_rc"))
    mod_rc.__version__ = '1.2rc1'
    assert not minversion(mod_rc, '1.2')
    mod_final = ModuleType(str("mod_final"))
    mod_final.__version__ = '1.2'
    assert minversion(mod_final, '1.2rc1')

    # 5) post-release higher than base
    mod_post = ModuleType(str("mod_post"))
    mod_post.__version__ = '1.2.post1'
    assert minversion(mod_post, '1.2')

    # 6) local version considered >= base
    mod_local = ModuleType(str("mod_local"))
    mod_local.__version__ = '1.2+local'
    assert minversion(mod_local, '1.2')


def test_minversion_version_path_and_missing_attr():
    """Dotted version_path resolves; missing __version__ raises AttributeError."""
    from types import ModuleType
    import sys

    # Dotted version_path resolution: module.pkginfo.version
    parent = ModuleType(str("parent_mod"))
    pkginfo = ModuleType(str("pkginfo"))
    pkginfo.version = '1.0'
    # Attach nested module as attribute
    setattr(parent, 'pkginfo', pkginfo)
    # Make parent importable via resolve_name
    sys.modules[parent.__name__] = parent
    assert minversion(parent, '0.9', version_path='pkginfo.version')

    # Missing __version__ attribute: should raise AttributeError (non-dotted)
    nover = ModuleType(str("nover_mod"))
    with pytest.raises(AttributeError):
        minversion(nover, '0.1')
