
from __future__ import absolute_import, division, print_function, unicode_literals

import functools
import typing as T  # noqa

import xarray as xr  # noqa

from . import cfunits


COORD_MODEL = {}  # type: T.Dict[str, T.Dict[str, T.Any]]
TRANSLATORS = {}  # type: T.Dict[str, T.Callable]


def match_values(match_value_func, mapping):
    # type: (T.Callable[[T.Any], bool], T.Dict[str, T.Any]) -> T.List[str]
    matched_names = []
    for name, value in mapping.items():
        if match_value_func(value):
            matched_names.append(name)
    return matched_names


def translator(
        default_out_name, default_units, is_cf_type, cf_type, data, coord_model=COORD_MODEL
):
    # type: (str, str, T.Callable, str, xr.DataArray, dict) -> xr.DataArray
    out_name = coord_model.get(cf_type, {}).get('out_name', default_out_name)
    units = coord_model.get(cf_type, {}).get('units', default_units)
    matches = match_values(is_cf_type, data.coords)
    if len(matches) > 1:
        raise ValueError("Found more than one CF coordinate with type %r." % cf_type)
    if not matches:
        return data
    match = matches[0]
    for name in data.coords:
        if name == out_name and name != match:
            raise ValueError("Found non CF compliant coordinate with type %r" % cf_type)
    data = data.rename({match: out_name})
    coord = data.coords[out_name]
    if 'units' in coord.attrs:
        data.coords[out_name] = cfunits.convert_units(coord, units, coord.attrs['units'])
        data.coords[out_name].attrs['untis'] = units
    return data


VALID_LAT_UNITS = ['degrees_north', 'degree_north', 'degree_N', 'degrees_N', 'degreeN', 'degreesN']


def is_latitude(coord):
    # type: (xr.Coordinate) -> bool
    return coord.attrs.get('units') in VALID_LAT_UNITS


TRANSLATORS['latitude'] = functools.partial(
    translator, 'latitude', 'degrees_north', is_latitude,
)


VALID_LON_UNITS = ['degrees_east', 'degree_east', 'degree_E', 'degrees_E', 'degreeE', 'degreesE']


def is_longitude(coord):
    # type: (xr.Coordinate) -> bool
    return coord.attrs.get('units') in VALID_LON_UNITS


TRANSLATORS['longitude'] = functools.partial(
    translator, 'longitude', 'degrees_east', is_longitude,
)


def is_forecast_reference_time(coord):
    # type: (xr.Coordinate) -> bool
    return coord.attrs.get('standard_name') == 'forecast_reference_time'


TRANSLATORS['forecast_reference_time'] = functools.partial(
    translator, 'time', 'seconds since 1970-01-01T00:00:00+00:00', is_forecast_reference_time,
)


def is_forecast_period(coord):
    # type: (xr.Coordinate) -> bool
    return coord.attrs.get('standard_name') == 'forecast_period'


TRANSLATORS['forecast_period'] = functools.partial(
    translator, 'step', 'h', is_forecast_period,
)


def is_valid_time(coord):
    # type: (xr.Coordinate) -> bool
    if coord.attrs.get('standard_name') == 'time':
        return True
    elif str(coord.dtype) == 'datetime64[ns]' and 'standard_name' not in coord.attrs:
        return True
    return False


TRANSLATORS['valid_time'] = functools.partial(
    translator, 'valid_time', 'seconds since 1970-01-01T00:00:00+00:00', is_valid_time,
)


def is_vertical_pressure(coord):
    # type: (xr.Coordinate) -> bool
    return cfunits.are_convertible(coord.attrs.get('units', ''), 'Pa')


TRANSLATORS['vertical_pressure'] = functools.partial(
    translator, 'level', 'hPa', is_vertical_pressure,
)


def is_realization(coord):
    # type: (xr.Coordinate) -> bool
    return coord.attrs.get('standard_name') == 'realization'


TRANSLATORS['realization'] = functools.partial(
    translator, 'number', '1', is_realization,
)


def translate(data, coord_model=COORD_MODEL, translators=TRANSLATORS):
    # type: (xr.Dataset, T.Dict, T.Dict) -> xr.Dataset
    for cf_name, translator in translators.items():
        data = translator(cf_name, data, coord_model=coord_model)
    return data


def ensure_valid_time_present(data, valid_time_name='valid_time'):
    # type: (xr.Dataset, str) -> T.Tuple[str, str, str]
    valid_times = match_values(is_valid_time, data.coords)
    times = match_values(is_forecast_reference_time, data.coords)
    steps = match_values(is_forecast_period, data.coords)
    time = step = ''
    if not valid_times:
        if not times:
            raise ValueError("Not enough information to ensure a 'valid_time'.")
        valid_time = valid_time_name
        time = times[0]
        if steps:
            step = steps[0]
            data.coords[valid_time] = data.coords[time] + data.coords[step]
        else:
            data.coords[valid_time] = data.coords[time]
        data.coords[valid_time].attrs['standard_name'] = 'time'
    else:
        valid_time = valid_times[0]
    return valid_time, time, step


def ensure_valid_time(data):
    # type: (xr.Dataset) -> xr.Dataset
    valid_time, time, step = ensure_valid_time_present(data)
    if valid_time not in data.dims:
        if data.coords[time].size == data.coords[valid_time].size:
            return data.swap_dims({time: valid_time})
        if data.coords[step].size == data.coords[step].size:
            return data.swap_dims({step: valid_time})
    return data
