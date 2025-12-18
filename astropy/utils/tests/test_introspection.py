# Licensed under a 3-clause BSD style license - see LICENSE.rst

# namedtuple is needed for find_mod_objs so it can have a non-local module
from collections import namedtuple
from types import ModuleType

import pytest

from .. import introspection
from ..introspection import (find_current_module, find_mod_objs,
                             minversion)


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
    assert find_current_module(
        0, ['astropy.utils.introspection']).__name__ == thismodnm

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


def _module_with_version(version):
    module = ModuleType(str("test_module"))
    module.__version__ = version
    return module


def test_minversion():
    test_module = _module_with_version('0.12.2')
    good_versions = ['0.12', '0.12.1', '0.12.0.dev']
    bad_versions = ['1', '1.2rc1']
    for version in good_versions:
        assert minversion(test_module, version)
    for version in bad_versions:
        assert not minversion(test_module, version)


def test_minversion_dev_comparisons():
    assert minversion(_module_with_version('1.14.3'), '1.14dev')
    assert not minversion(_module_with_version('1.14'), '1.14dev')


def test_minversion_multi_component_dev_ordering():
    lower = _module_with_version('1.2.3.4.dev1')
    higher_version = '1.2.3.5.dev1'
    assert not minversion(lower, higher_version)
    assert minversion(_module_with_version(higher_version), '1.2.3.4.dev1')


@pytest.mark.parametrize(
    'lower,higher',
    [
        ('1.14a1', '1.14b1'),
        ('1.14b1', '1.14rc1'),
        ('1.14rc1', '1.14'),
    ]
)
def test_minversion_prerelease_order(lower, higher):
    assert not minversion(_module_with_version(lower), higher)
    assert minversion(_module_with_version(higher), lower)


def test_minversion_post_release_order():
    assert not minversion(_module_with_version('1.14'), '1.14.post1')
    assert minversion(_module_with_version('1.14.1'), '1.14.post1')


def test_minversion_ignores_epoch_and_local():
    assert minversion(_module_with_version('2!1.14.0+g123'), '1.14')
    assert minversion(_module_with_version('1.14'), '2!1.14.0+local')
