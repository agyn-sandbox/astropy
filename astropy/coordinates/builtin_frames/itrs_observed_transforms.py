# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Direct transforms between ITRS and observed frames (AltAz, HADec) operating
purely in ITRS via topocentric subtraction and ENU rotations.
"""

import numpy as np

from astropy import units as u
from astropy.coordinates import Angle, Longitude
from astropy.coordinates.baseframe import frame_transform_graph
from astropy.coordinates.transformations import FunctionTransformWithFiniteDifference
from astropy.coordinates.representation import (
    CartesianRepresentation,
    SphericalRepresentation,
    UnitSphericalRepresentation,
)

from .itrs import ITRS
from .altaz import AltAz
from .hadec import HADec


def _r_ecef_to_enu(phi, lam):
    """Rotation matrix from ECEF (ITRS) to ENU.

    Parameters
    ----------
    phi : float
        Geodetic latitude in radians.
    lam : float
        Geodetic longitude in radians.

    Returns
    -------
    ndarray
        3x3 rotation matrix mapping ECEF xyz to ENU (east, north, up).
    """
    sphi, cphi = np.sin(phi), np.cos(phi)
    slam, clam = np.sin(lam), np.cos(lam)
    return np.array([
        [-slam, clam, 0.0],
        [-sphi * clam, -sphi * slam, cphi],
        [cphi * clam, cphi * slam, sphi],
    ])


def _pressure_nonzero(frame):
    """Return True if frame has a non-zero pressure attribute."""
    p = getattr(frame, "pressure", 0 * u.hPa)
    try:
        return np.any(u.Quantity(p, u.hPa).value != 0.0)
    except Exception:
        return False


def _wrap_az_positive(az_rad):
    """Wrap azimuth in radians to [0, 2*pi)."""
    # Use Longitude with wrap_angle=360 deg for [0,360) behaviour
    return Longitude(az_rad * u.radian, wrap_angle=360 * u.deg).to_value(u.radian)


def _wrap_ha_pm_pi(ha_rad):
    """Wrap hour angle in radians to (-pi, pi]."""
    return Angle(ha_rad * u.radian).wrap_at(180 * u.deg).to_value(u.radian)


@frame_transform_graph.transform(FunctionTransformWithFiniteDifference, ITRS, AltAz)
def itrs_to_altaz(itrs_coo, altaz_frame):
    # Validate required attributes
    if altaz_frame.location is None:
        raise ValueError("AltAz frame requires a location for ITRS<->AltAz direct transform")
    if altaz_frame.obstime is None:
        raise ValueError("AltAz frame requires an obstime for ITRS<->AltAz direct transform")

    # Refraction not supported in direct transform
    if _pressure_nonzero(altaz_frame):
        raise NotImplementedError(
            "Direct ITRS<->Observed does not implement refraction; "
            "use CIRS/ICRS path or set pressure=0"
        )

    # Ensure ITRS obstime matches target AltAz obstime, handling None robustly
    target_obstime = altaz_frame.obstime
    if target_obstime is None:
        if getattr(itrs_coo, "obstime", None) is not None:
            itrs_coo = itrs_coo.transform_to(ITRS(obstime=None))
    else:
        if np.any(getattr(itrs_coo, "obstime", None) != target_obstime):
            itrs_coo = itrs_coo.transform_to(ITRS(obstime=target_obstime))

    # Observer position in ITRS
    obs_itrs = altaz_frame.location.get_itrs(altaz_frame.obstime).cartesian

    # Topocentric vector in ITRS
    topo = itrs_coo.cartesian - obs_itrs

    # ECEF -> ENU rotation at site
    lon, lat, _ = altaz_frame.location.to_geodetic()
    lam = lon.to_value(u.radian)
    phi = lat.to_value(u.radian)
    R = _r_ecef_to_enu(phi, lam)

    topo_xyz_m = topo.xyz.to_value(u.m)
    enu = R @ topo_xyz_m
    e, n, uup = enu

    distance = np.sqrt(e * e + n * n + uup * uup) * u.m
    alt = np.arctan2(uup, np.hypot(e, n)) * u.radian
    az = Longitude(np.arctan2(e, n) * u.radian, wrap_angle=360 * u.deg)

    rep = SphericalRepresentation(lon=az.to(u.radian), lat=alt, distance=distance)
    return altaz_frame.realize_frame(rep)


@frame_transform_graph.transform(FunctionTransformWithFiniteDifference, AltAz, ITRS)
def altaz_to_itrs(altaz_coo, itrs_frame):
    # Validate required attributes
    if altaz_coo.location is None:
        raise ValueError("AltAz coordinate requires a location for AltAz->ITRS direct transform")
    if altaz_coo.obstime is None:
        raise ValueError("AltAz coordinate requires an obstime for AltAz->ITRS direct transform")

    # Refraction not supported in direct transform
    if _pressure_nonzero(altaz_coo):
        raise NotImplementedError(
            "Direct ITRS<->Observed does not implement refraction; "
            "use CIRS/ICRS path or set pressure=0"
        )

    # Distance required
    if isinstance(altaz_coo.data, UnitSphericalRepresentation) or getattr(altaz_coo, "distance", None) is None:
        raise ValueError("Distance required for AltAz->ITRS direct transform")

    # Site parameters and spherical to ENU
    lon, lat, _ = altaz_coo.location.to_geodetic()
    lam = lon.to_value(u.radian)
    phi = lat.to_value(u.radian)
    alt = altaz_coo.alt.to_value(u.radian)
    # Wrap azimuth into [0, 2pi) for consistency
    az = Longitude(altaz_coo.az, wrap_angle=360 * u.deg).to_value(u.radian)
    d = altaz_coo.distance.to_value(u.m)

    e = d * np.cos(alt) * np.sin(az)
    n = d * np.cos(alt) * np.cos(az)
    uup = d * np.sin(alt)

    R = _r_ecef_to_enu(phi, lam)
    topo_ecef = R.T @ np.array([e, n, uup])

    # Realize at observed obstime first
    obs_time = altaz_coo.obstime
    obs_itrs = altaz_coo.location.get_itrs(obs_time).cartesian
    cart = CartesianRepresentation(*(topo_ecef * u.m)) + obs_itrs
    itrs_at_obs = ITRS(obstime=obs_time).realize_frame(cart)

    # If requested target ITRS frame has different obstime (incl. None), transform
    target_obstime = itrs_frame.obstime
    if np.any(getattr(itrs_at_obs, "obstime", None) != target_obstime):
        return itrs_at_obs.transform_to(ITRS(obstime=target_obstime))
    else:
        return itrs_frame.realize_frame(itrs_at_obs.data)


@frame_transform_graph.transform(FunctionTransformWithFiniteDifference, ITRS, HADec)
def itrs_to_hadec(itrs_coo, hadec_frame):
    # Validate required attributes
    if hadec_frame.location is None:
        raise ValueError("HADec frame requires a location for ITRS<->HADec direct transform")
    if hadec_frame.obstime is None:
        raise ValueError("HADec frame requires an obstime for ITRS<->HADec direct transform")

    # Refraction not supported
    if _pressure_nonzero(hadec_frame):
        raise NotImplementedError(
            "Direct ITRS<->Observed does not implement refraction; "
            "use CIRS/ICRS path or set pressure=0"
        )

    # Ensure ITRS obstime matches target obstime, handling None robustly
    target_obstime = hadec_frame.obstime
    if target_obstime is None:
        if getattr(itrs_coo, "obstime", None) is not None:
            itrs_coo = itrs_coo.transform_to(ITRS(obstime=None))
    else:
        if np.any(getattr(itrs_coo, "obstime", None) != target_obstime):
            itrs_coo = itrs_coo.transform_to(ITRS(obstime=target_obstime))

    # Observer and topocentric vector
    obs_itrs = hadec_frame.location.get_itrs(hadec_frame.obstime).cartesian
    topo = itrs_coo.cartesian - obs_itrs

    lon, lat, _ = hadec_frame.location.to_geodetic()
    lam = lon.to_value(u.radian)
    phi = lat.to_value(u.radian)
    R = _r_ecef_to_enu(phi, lam)

    topo_xyz_m = topo.xyz.to_value(u.m)
    enu = R @ topo_xyz_m
    e, n, uup = enu

    # Convert ENU to HA/Dec using site latitude phi
    distance = np.sqrt(e * e + n * n + uup * uup) * u.m
    alt = np.arctan2(uup, np.hypot(e, n))
    az = _wrap_az_positive(np.arctan2(e, n))

    sin_alt = np.sin(alt)
    cos_alt = np.cos(alt)
    sin_phi = np.sin(phi)
    cos_phi = np.cos(phi)

    arg_dec = sin_alt * sin_phi + cos_alt * cos_phi * np.cos(az)
    dec = np.arcsin(np.clip(arg_dec, -1.0, 1.0))

    # Guard against cos(dec)=0
    cos_dec = np.cos(dec)
    # Avoid division by zero using where; values at poles won't affect HA meaningfully
    sinH = -np.sin(az) * cos_alt / np.where(cos_dec == 0, np.inf, cos_dec)
    cosH = (sin_alt - sin_phi * np.sin(dec)) / np.where(cos_phi * cos_dec == 0, np.inf, cos_phi * cos_dec)
    ha = _wrap_ha_pm_pi(np.arctan2(sinH, cosH))

    # Ensure HA is in hourangle units for HADec
    ha_angle = Angle(ha * u.radian).wrap_at(180 * u.deg).to(u.hourangle)
    rep = SphericalRepresentation(lon=ha_angle, lat=dec * u.radian, distance=distance)
    return hadec_frame.realize_frame(rep)


@frame_transform_graph.transform(FunctionTransformWithFiniteDifference, HADec, ITRS)
def hadec_to_itrs(hadec_coo, itrs_frame):
    # Validate required attributes
    if hadec_coo.location is None:
        raise ValueError("HADec coordinate requires a location for HADec->ITRS direct transform")
    if hadec_coo.obstime is None:
        raise ValueError("HADec coordinate requires an obstime for HADec->ITRS direct transform")

    # Refraction not supported
    if _pressure_nonzero(hadec_coo):
        raise NotImplementedError(
            "Direct ITRS<->Observed does not implement refraction; "
            "use CIRS/ICRS path or set pressure=0"
        )

    # Distance required
    if isinstance(hadec_coo.data, UnitSphericalRepresentation) or getattr(hadec_coo, "distance", None) is None:
        raise ValueError("Distance required for HADec->ITRS direct transform")

    # Site latitude and convert HADec to AltAz
    lon, lat, _ = hadec_coo.location.to_geodetic()
    phi = lat.to_value(u.radian)
    # Wrap HA to (-pi, pi]
    H = Angle(hadec_coo.ha).wrap_at(180 * u.deg).to_value(u.radian)
    dec = hadec_coo.dec.to_value(u.radian)
    d = hadec_coo.distance.to_value(u.m)

    sin_phi = np.sin(phi)
    cos_phi = np.cos(phi)
    sin_dec = np.sin(dec)
    cos_dec = np.cos(dec)
    cosH = np.cos(H)
    sinH = np.sin(H)

    sin_alt = sin_dec * sin_phi + cos_dec * cos_phi * cosH
    # Numerical guard: ensure within [-1,1]
    sin_alt = np.clip(sin_alt, -1.0, 1.0)
    alt = np.arcsin(sin_alt)

    cos_alt = np.cos(alt)
    # Avoid division by zero in az at zenith/nadir
    denom = np.where(cos_alt == 0, np.inf, cos_alt)
    sin_az = -sinH * cos_dec / denom
    cos_az = (sin_dec - sin_phi * sin_alt) / np.where(cos_phi * denom == 0, np.inf, cos_phi * denom)
    az = _wrap_az_positive(np.arctan2(sin_az, cos_az))

    # AltAz spherical to ENU
    e = d * np.cos(alt) * np.sin(az)
    n = d * np.cos(alt) * np.cos(az)
    uup = d * np.sin(alt)

    lam = lon.to_value(u.radian)
    R = _r_ecef_to_enu(phi, lam)
    topo_ecef = R.T @ np.array([e, n, uup])

    # Realize at observed obstime first
    obs_time = hadec_coo.obstime
    obs_itrs = hadec_coo.location.get_itrs(obs_time).cartesian
    cart = CartesianRepresentation(*(topo_ecef * u.m)) + obs_itrs
    itrs_at_obs = ITRS(obstime=obs_time).realize_frame(cart)

    target_obstime = itrs_frame.obstime
    if np.any(getattr(itrs_at_obs, "obstime", None) != target_obstime):
        return itrs_at_obs.transform_to(ITRS(obstime=target_obstime))
    else:
        return itrs_frame.realize_frame(itrs_at_obs.data)
