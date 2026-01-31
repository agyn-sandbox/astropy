# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Direct transformations between ITRS and observed frames."""

from __future__ import annotations

import warnings

import numpy as np
import erfa

from astropy import units as u
from astropy.utils.exceptions import AstropyWarning
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

__all__ = ["itrs_to_observed_mat"]


_OBSTIME_MISMATCH = (
    "Obstime mismatch between ITRS and {frame} frames. "
    "For time-dependent or aberration-aware cases use the ITRS→ICRS→Observed path."
)


def _require_observed_obstime(observed_frame) -> None:
    if getattr(observed_frame, "obstime", None) is None:
        raise ValueError(
            "Direct ITRS↔Observed transforms require obstime on the observed frame."
        )


def _require_location(frame) -> None:
    if getattr(frame, "location", None) is None:
        raise ValueError(
            "Direct ITRS↔Observed transforms require an EarthLocation on the observed frame."
        )


def _check_obstime_match(source_time, target_time, frame_label: str) -> None:
    if source_time is None or target_time is None:
        return
    if np.any(source_time != target_time):
        raise ValueError(_OBSTIME_MISMATCH.format(frame=frame_label))


def _warn_no_refraction(observed) -> None:
    pressure = getattr(observed, "pressure", None)
    if pressure is None:
        return
    pressure = u.Quantity(pressure, copy=False)
    if np.any(pressure.to_value(u.hPa) > 0):
        warnings.warn(
            "Direct ITRS↔Observed transforms do not apply atmospheric refraction. "
            "Set pressure=0 or transform via ITRS→ICRS→Observed to include refraction.",
            AstropyWarning,
            stacklevel=3,
        )


def itrs_to_observed_mat(observed_frame) -> np.ndarray:
    """Return the rotation matrix that maps ECEF vectors to local ENU coordinates."""

    _require_location(observed_frame)
    lon, lat, _ = observed_frame.location.geodetic
    lon_rad = lon.to_value(u.rad)
    lat_rad = lat.to_value(u.rad)

    sin_lon = np.sin(lon_rad)
    cos_lon = np.cos(lon_rad)
    sin_lat = np.sin(lat_rad)
    cos_lat = np.cos(lat_rad)

    return np.array([
        [-sin_lon, cos_lon, 0.0],
        [-sin_lat * cos_lon, -sin_lat * sin_lon, cos_lat],
        [cos_lat * cos_lon, cos_lat * sin_lon, sin_lat],
    ])


def _compute_altaz_from_itrs(diff_cart: CartesianRepresentation, rotation: np.ndarray):
    unit = diff_cart.x.unit
    diff_values = np.stack(
        [
            diff_cart.x.to_value(unit),
            diff_cart.y.to_value(unit),
            diff_cart.z.to_value(unit),
        ],
        axis=0,
    )

    enu = np.tensordot(rotation, diff_values, axes=([1], [0]))
    east = enu[0]
    north = enu[1]
    up = enu[2]

    horizontal = np.hypot(east, north)
    alt = np.arctan2(up, horizontal)
    az = np.mod(np.arctan2(east, north), 2.0 * np.pi)

    return az, alt


@frame_transform_graph.transform(FunctionTransformWithFiniteDifference, ITRS, AltAz)
@frame_transform_graph.transform(FunctionTransformWithFiniteDifference, ITRS, HADec)
def itrs_to_observed(itrs_coo, observed_frame):
    _require_location(observed_frame)
    _require_observed_obstime(observed_frame)
    _check_obstime_match(
        itrs_coo.obstime,
        observed_frame.obstime,
        observed_frame.__class__.__name__,
    )
    _warn_no_refraction(observed_frame)

    rotation = itrs_to_observed_mat(observed_frame)
    location_cart = observed_frame.location.get_itrs(obstime=observed_frame.obstime).cartesian
    cart = itrs_coo.cartesian

    is_unitspherical = (
        isinstance(itrs_coo.data, UnitSphericalRepresentation)
        or cart.x.unit == u.one
    )

    if is_unitspherical:
        warnings.warn(
            "Unit-spherical ITRS inputs are treated as infinite-distance directions.",
            AstropyWarning,
            stacklevel=3,
        )
        diff_cart = cart
        distance = None
    else:
        diff_cart = cart - location_cart
        distance = diff_cart.norm()

    az, alt = _compute_altaz_from_itrs(diff_cart, rotation)
    alt_q = u.Quantity(alt, u.rad, copy=False)
    az_q = u.Quantity(az, u.rad, copy=False)

    if isinstance(observed_frame, AltAz):
        if distance is None:
            rep = UnitSphericalRepresentation(lon=az_q, lat=alt_q, copy=False)
        else:
            rep = SphericalRepresentation(lon=az_q, lat=alt_q, distance=distance, copy=False)
        return observed_frame.realize_frame(rep)

    lat_geodetic = observed_frame.location.geodetic[1].to_value(u.rad)
    ha, dec = erfa.ae2hd(az, alt, lat_geodetic)
    ha_q = u.Quantity(ha, u.rad, copy=False)
    dec_q = u.Quantity(dec, u.rad, copy=False)
    if distance is None:
        rep = UnitSphericalRepresentation(lon=ha_q, lat=dec_q, copy=False)
    else:
        rep = SphericalRepresentation(lon=ha_q, lat=dec_q, distance=distance, copy=False)
    return observed_frame.realize_frame(rep)


def _observed_angles(observed_coo):
    usrepr = observed_coo.represent_as(UnitSphericalRepresentation)
    if isinstance(observed_coo, AltAz):
        az = usrepr.lon.to_value(u.rad)
        alt = usrepr.lat.to_value(u.rad)
        az = np.mod(az, 2.0 * np.pi)
        return az, alt

    ha = usrepr.lon.to_value(u.rad)
    dec = usrepr.lat.to_value(u.rad)
    lat_geodetic = observed_coo.location.geodetic[1].to_value(u.rad)
    az, alt = erfa.hd2ae(ha, dec, lat_geodetic)
    az = np.mod(az, 2.0 * np.pi)
    return az, alt


@frame_transform_graph.transform(FunctionTransformWithFiniteDifference, AltAz, ITRS)
@frame_transform_graph.transform(FunctionTransformWithFiniteDifference, HADec, ITRS)
def observed_to_itrs(observed_coo, itrs_frame):
    _require_location(observed_coo)
    _require_observed_obstime(observed_coo)
    _check_obstime_match(observed_coo.obstime, itrs_frame.obstime, observed_coo.__class__.__name__)
    _warn_no_refraction(observed_coo)

    rotation = itrs_to_observed_mat(observed_coo)
    location_cart = observed_coo.location.get_itrs(obstime=observed_coo.obstime).cartesian

    az, alt = _observed_angles(observed_coo)
    cos_alt = np.cos(alt)
    east = cos_alt * np.sin(az)
    north = cos_alt * np.cos(az)
    up = np.sin(alt)

    is_unitspherical = (
        isinstance(observed_coo.data, UnitSphericalRepresentation)
        or observed_coo.cartesian.x.unit == u.one
    )

    if is_unitspherical:
        warnings.warn(
            "Unit-spherical observed inputs are treated as infinite-distance directions.",
            AstropyWarning,
            stacklevel=3,
        )
        enu = np.stack([east, north, up], axis=0)
        ecef = np.tensordot(rotation.T, enu, axes=([1], [0]))
        rep = CartesianRepresentation(
            x=u.Quantity(ecef[0], u.one, copy=False),
            y=u.Quantity(ecef[1], u.one, copy=False),
            z=u.Quantity(ecef[2], u.one, copy=False),
            copy=False,
        ).represent_as(UnitSphericalRepresentation)
        return itrs_frame.realize_frame(rep)

    distance_unit = location_cart.x.unit
    distance_vals = observed_coo.distance.to_value(distance_unit)
    enu = np.stack([east, north, up], axis=0) * distance_vals
    ecef = np.tensordot(rotation.T, enu, axes=([1], [0]))
    topo = CartesianRepresentation(
        x=u.Quantity(ecef[0], distance_unit, copy=False),
        y=u.Quantity(ecef[1], distance_unit, copy=False),
        z=u.Quantity(ecef[2], distance_unit, copy=False),
        copy=False,
    )
    cart = location_cart + topo
    return itrs_frame.realize_frame(cart)
