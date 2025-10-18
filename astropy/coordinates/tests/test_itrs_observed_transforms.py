# Licensed under a 3-clause BSD style license - see LICENSE.rst

import numpy as np

import pytest

from astropy import units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation, Angle, Longitude
from astropy.coordinates.representation import CartesianRepresentation
from astropy.coordinates.builtin_frames import ITRS, AltAz, HADec, CIRS


def _home():
    return EarthLocation(lon=-1 * u.deg, lat=52 * u.deg, height=0 * u.m)


def _time():
    return Time('J2010')


def test_itrs_to_altaz_overhead_parity():
    t = _time()
    home = _home()

    # Object at zenith for topocentric observer: construct via CIRS as in existing tests
    obj = EarthLocation(-1 * u.deg, 52 * u.deg, height=10.0 * u.km)
    cirs_geo = obj.get_itrs(t).transform_to(CIRS(obstime=t))
    obsrepr = home.get_itrs(t).transform_to(CIRS(obstime=t)).cartesian
    cirs_repr = cirs_geo.cartesian - obsrepr
    cirs_topo = CIRS(obstime=t, location=home).realize_frame(cirs_repr)

    # Transform to ITRS at same obstime then to AltAz via direct ITRS path
    itrs_topo = cirs_topo.transform_to(ITRS(obstime=t))
    aa = itrs_topo.transform_to(AltAz(obstime=t, location=home))
    assert aa.alt.to_value(u.deg) == pytest.approx(90.0, abs=1e-6)


def test_itrs_to_hadec_overhead_parity():
    t = _time()
    home = _home()

    obj = EarthLocation(-1 * u.deg, 52 * u.deg, height=10.0 * u.km)
    cirs_geo = obj.get_itrs(t).transform_to(CIRS(obstime=t))
    obsrepr = home.get_itrs(t).transform_to(CIRS(obstime=t)).cartesian
    cirs_repr = cirs_geo.cartesian - obsrepr
    cirs_topo = CIRS(obstime=t, location=home).realize_frame(cirs_repr)

    itrs_topo = cirs_topo.transform_to(ITRS(obstime=t))
    hd = itrs_topo.transform_to(HADec(obstime=t, location=home))
    assert hd.ha.to_value(u.hourangle) == pytest.approx(0.0, abs=1e-6)
    assert hd.dec.to_value(u.deg) == pytest.approx(52.0, abs=1e-6)


def test_round_trip_itrs_altaz_itrs():
    t = _time()
    home = _home()

    # A point offset from observer
    dvec = np.array([1000.0, 2000.0, 50.0]) * u.m
    lon, lat, _ = home.to_geodetic('WGS84')
    lam = lon.to_value(u.rad)
    phi = lat.to_value(u.rad)

    from astropy.coordinates.builtin_frames.itrs_observed_transforms import _r_ecef_to_enu
    obs_itrs = home.get_itrs(t).cartesian
    topo_ecef = _r_ecef_to_enu(phi, lam).T @ dvec.to_value(u.m)
    itrs_point_cart = CartesianRepresentation(*(topo_ecef * u.m)) + obs_itrs
    itrs_point = ITRS(obstime=t).realize_frame(itrs_point_cart)

    aa = itrs_point.transform_to(AltAz(obstime=t, location=home))
    aa = AltAz(az=aa.az, alt=aa.alt, distance=aa.distance, obstime=t, location=home)
    itrs_back = aa.transform_to(ITRS(obstime=t))
    sep = itrs_back.separation_3d(itrs_point)
    assert sep.to_value(u.mm) == pytest.approx(0.0, abs=1e-3)


def test_round_trip_itrs_hadec_itrs():
    t = _time()
    home = _home()

    dvec = np.array([500.0, -1500.0, 75.0]) * u.m
    lon, lat, _ = home.to_geodetic('WGS84')
    lam = lon.to_value(u.rad)
    phi = lat.to_value(u.rad)

    from astropy.coordinates.builtin_frames.itrs_observed_transforms import _r_ecef_to_enu
    obs_itrs = home.get_itrs(t).cartesian
    topo_ecef = _r_ecef_to_enu(phi, lam).T @ dvec.to_value(u.m)
    itrs_point_cart = CartesianRepresentation(*(topo_ecef * u.m)) + obs_itrs
    itrs_point = ITRS(obstime=t).realize_frame(itrs_point_cart)

    hd = itrs_point.transform_to(HADec(obstime=t, location=home))
    hd = HADec(ha=hd.ha, dec=hd.dec, distance=hd.distance, obstime=t, location=home)
    itrs_back = hd.transform_to(ITRS(obstime=t))
    sep = itrs_back.separation_3d(itrs_point)
    assert sep.to_value(u.mm) == pytest.approx(0.0, abs=1e-3)


def test_direct_vs_cirs_path_equivalence_altaz():
    t = _time()
    home = _home()
    # Some arbitrary ITRS point: location + offset
    obs = home.get_itrs(t)
    offset = np.array([10.0, -20.0, 5.0]) * u.m
    itrs_point = ITRS(obs.cartesian + offset, obstime=t)

    aa_direct = itrs_point.transform_to(AltAz(obstime=t, location=home))
    aa_via_cirs = itrs_point.transform_to(CIRS(obstime=t, location=home)).transform_to(
        AltAz(obstime=t, location=home)
    )

    assert aa_direct.separation(aa_via_cirs).to_value(u.arcsec) == pytest.approx(0.0, abs=1e-6)


def test_direct_vs_cirs_path_equivalence_hadec():
    t = _time()
    home = _home()
    obs = home.get_itrs(t)
    offset = np.array([10.0, -20.0, 5.0]) * u.m
    itrs_point = ITRS(obs.cartesian + offset, obstime=t)

    hd_direct = itrs_point.transform_to(HADec(obstime=t, location=home))
    hd_via_cirs = itrs_point.transform_to(CIRS(obstime=t, location=home)).transform_to(
        HADec(obstime=t, location=home)
    )

    assert hd_direct.separation(hd_via_cirs).to_value(u.arcsec) == pytest.approx(0.0, abs=1e-6)


def test_obstime_alignment_no_dependency_on_input_itrs_obstime():
    t = _time()
    home = _home()

    # Two ITRS inputs with different obstime, representing same spatial position
    obs = home.get_itrs(t)
    offset = np.array([123.0, 456.0, 789.0]) * u.m
    itrs_t1 = ITRS(obs.cartesian + offset, obstime=t)
    itrs_t2 = ITRS(obs.cartesian + offset, obstime=t + 1 * u.day)

    aa1 = itrs_t1.transform_to(AltAz(obstime=t, location=home))
    aa2 = itrs_t2.transform_to(AltAz(obstime=t, location=home))
    assert aa1.separation(aa2).to_value(u.arcsec) == pytest.approx(0.0, abs=1e-9)


def test_altaz_to_itrs_requires_distance():
    t = _time()
    home = _home()
    aa = AltAz(az=10 * u.deg, alt=20 * u.deg, obstime=t, location=home)
    with pytest.raises(ValueError):
        aa.transform_to(ITRS(obstime=t))


def test_hadec_to_itrs_requires_distance():
    t = _time()
    home = _home()
    hd = HADec(ha=1 * u.hourangle, dec=10 * u.deg, obstime=t, location=home)
    with pytest.raises(ValueError):
        hd.transform_to(ITRS(obstime=t))


def test_pressure_not_implemented():
    t = _time()
    home = _home()
    obs = home.get_itrs(t)
    itrs_point = ITRS(obs.cartesian + np.array([10.0, 0.0, 0.0]) * u.m, obstime=t)

    with pytest.raises(NotImplementedError):
        itrs_point.transform_to(AltAz(obstime=t, location=home, pressure=1010 * u.hPa))
    with pytest.raises(NotImplementedError):
        itrs_point.transform_to(HADec(obstime=t, location=home, pressure=1010 * u.hPa))

    aa = AltAz(az=10 * u.deg, alt=20 * u.deg, distance=100 * u.m, obstime=t, location=home, pressure=1010 * u.hPa)
    with pytest.raises(NotImplementedError):
        aa.transform_to(ITRS(obstime=t))

    hd = HADec(ha=1 * u.hourangle, dec=10 * u.deg, distance=100 * u.m, obstime=t, location=home, pressure=1010 * u.hPa)
    with pytest.raises(NotImplementedError):
        hd.transform_to(ITRS(obstime=t))


def test_wrapping_azimuth_boundaries():
    t = _time()
    home = _home()
    # Build two AltAz positions near wrap boundaries and ensure wrapping is correct
    d = 1000 * u.m
    # Use az just below 0 and just above 360 by constructing AltAz and round-tripping
    for az_deg in (-0.0001, 359.9999):
        aa = AltAz(az=az_deg * u.deg, alt=45 * u.deg, distance=d, obstime=t, location=home)
        it = aa.transform_to(ITRS(obstime=t))
        aa2 = it.transform_to(AltAz(obstime=t, location=home))
        # Wrapped to [0, 360)
        az_wrapped = Longitude(az_deg * u.deg, wrap_angle=360 * u.deg)
        assert (aa2.az - az_wrapped).to_value(u.arcsec) == pytest.approx(0.0, abs=1e-4)


def test_wrapping_hourangle_boundaries():
    t = _time()
    home = _home()
    d = 1000 * u.m
    for ha_h in (-12.000001, 12.000001):
        hd = HADec(ha=ha_h * u.hourangle, dec=10 * u.deg, distance=d, obstime=t, location=home)
        it = hd.transform_to(ITRS(obstime=t))
        hd2 = it.transform_to(HADec(obstime=t, location=home))
        ha_wrapped = Angle(ha_h * u.hourangle).wrap_at(12 * u.hourangle)
        # Compare in hourangle
        assert (hd2.ha - ha_wrapped).to_value(u.second) == pytest.approx(0.0, abs=1e-6)


def test_observed_to_itrs_obstime_labeling():
    t = _time()
    home = _home()
    d = 1234 * u.m

    # Build AltAz with distance and convert to ITRS while requesting different obstime label
    aa = AltAz(az=10 * u.deg, alt=20 * u.deg, distance=d, obstime=t, location=home)
    it_target = ITRS(obstime=t + 1 * u.day)
    it = aa.transform_to(it_target)
    # Check label matches target
    assert it.obstime == it_target.obstime

    # Ensure numerically the same as ITRS realized at observed time transformed to target obstime
    it_obs = aa.transform_to(ITRS(obstime=t))
    it_obs_to_target = it_obs.transform_to(it_target)
    sep = it.separation_3d(it_obs_to_target)
    assert sep.to_value(u.mm) == pytest.approx(0.0, abs=1e-3)
