# Licensed under a 3-clause BSD style license - see LICENSE.rst

import numpy as np
import pytest

from astropy import units as u
from astropy.time import Time
from astropy.utils.exceptions import AstropyWarning
from astropy.coordinates import (
    AltAz,
    HADec,
    ICRS,
    ITRS,
    EarthLocation,
)
from astropy.coordinates.representation import UnitSphericalRepresentation


@pytest.fixture
def location():
    return EarthLocation(lat=35.0 * u.deg, lon=-111.0 * u.deg, height=2150 * u.m)


@pytest.fixture
def obstime():
    return Time("2024-01-01T00:00:00", scale="utc")


def _zenith_target(location, obstime, height_offset):
    return EarthLocation(
        lat=location.lat,
        lon=location.lon,
        height=location.height + height_offset,
    ).get_itrs(obstime=obstime)


def test_round_trip_itrs_altaz_hadec(location, obstime):
    target = _zenith_target(location, obstime, 1500 * u.m)
    altaz_frame = AltAz(obstime=obstime, location=location, pressure=0 * u.hPa)
    hadec_frame = HADec(obstime=obstime, location=location, pressure=0 * u.hPa)
    itrs_frame = ITRS(obstime=obstime)

    altaz = target.transform_to(altaz_frame)
    recovered = altaz.transform_to(itrs_frame)
    separation = (recovered.cartesian - target.cartesian).norm()
    assert separation.to_value(u.m) < 1e-3

    hadec = target.transform_to(hadec_frame)
    recovered_hadec = hadec.transform_to(itrs_frame)
    separation_hadec = (recovered_hadec.cartesian - target.cartesian).norm()
    assert separation_hadec.to_value(u.m) < 1e-3


def test_obstime_mismatch_raises(location, obstime):
    delta_time = Time("2024-01-02T00:00:00", scale="utc")
    itrs_coo = _zenith_target(location, obstime, 1000 * u.m)
    altaz_frame = AltAz(obstime=delta_time, location=location, pressure=0 * u.hPa)

    with pytest.raises(ValueError, match="Obstime mismatch"):
        itrs_coo.transform_to(altaz_frame)

    altaz_coord = AltAz(
        az=180 * u.deg,
        alt=45 * u.deg,
        distance=30 * u.km,
        obstime=obstime,
        location=location,
        pressure=0 * u.hPa,
    )
    with pytest.raises(ValueError, match="Obstime mismatch"):
        altaz_coord.transform_to(ITRS(obstime=delta_time))


def test_unit_spherical_itrs_warns(location, obstime):
    direction = UnitSphericalRepresentation(lon=25 * u.deg, lat=60 * u.deg)
    itrs_dir = ITRS(direction, obstime=obstime)
    altaz_frame = AltAz(obstime=obstime, location=location, pressure=0 * u.hPa)

    with pytest.warns(AstropyWarning, match="Unit-spherical ITRS inputs"):
        altaz = itrs_dir.transform_to(altaz_frame)

    assert isinstance(altaz.data, UnitSphericalRepresentation)


@pytest.mark.parametrize("observed_cls, kwargs", [
    (AltAz, {"az": 45 * u.deg, "alt": 30 * u.deg}),
    (HADec, {"ha": 1 * u.hourangle, "dec": 20 * u.deg}),
])
def test_unit_spherical_observed_to_itrs_warns(location, obstime, observed_cls, kwargs):
    frame_kwargs = {"obstime": obstime, "location": location, "pressure": 0 * u.hPa}
    frame_kwargs.update(kwargs)
    observed = observed_cls(**frame_kwargs)

    with pytest.warns(AstropyWarning, match="Unit-spherical observed inputs"):
        result = observed.transform_to(ITRS(obstime=obstime))

    assert isinstance(result.data, UnitSphericalRepresentation)


def test_zenith_alignment(location, obstime):
    target = _zenith_target(location, obstime, 500 * u.m)
    altaz_frame = AltAz(obstime=obstime, location=location, pressure=0 * u.hPa)
    hadec_frame = HADec(obstime=obstime, location=location, pressure=0 * u.hPa)

    altaz = target.transform_to(altaz_frame)
    assert np.isclose((altaz.alt - 90 * u.deg).to_value(u.arcsec), 0.0, atol=1e-6)
    hadec = target.transform_to(hadec_frame)
    ha_wrapped = hadec.ha.wrap_at(180 * u.deg)
    assert np.isclose(ha_wrapped.to_value(u.arcsec), 0.0, atol=1e-6)


def test_deep_space_matches_icrs_route(location, obstime):
    altaz_frame = AltAz(obstime=obstime, location=location, pressure=0 * u.hPa)
    distant = AltAz(
        az=130 * u.deg,
        alt=40 * u.deg,
        distance=1e9 * u.m,
        obstime=obstime,
        location=location,
        pressure=0 * u.hPa,
    )

    itrs_target = distant.transform_to(ITRS(obstime=obstime))
    direct = itrs_target.transform_to(altaz_frame)
    with pytest.warns(AstropyWarning):
        via_icrs = itrs_target.transform_to(ICRS()).transform_to(altaz_frame)

    assert u.allclose(direct.distance, distant.distance)
    assert np.isclose((direct.alt - distant.alt).to_value(u.arcsec), 0.0, atol=1e-6)
    az_diff = (direct.az - distant.az).wrap_at(180 * u.deg).to(u.arcsec)
    assert np.isclose(az_diff.value, 0.0, atol=1e-6)

    alt_delta = (direct.alt - via_icrs.alt).to(u.arcsec)
    az_delta = (direct.az - via_icrs.az).wrap_at(180 * u.deg).to(u.arcsec)
    assert alt_delta.value < 0.5
    assert az_delta.value < 0.5
