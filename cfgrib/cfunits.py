
from __future__ import absolute_import, division, print_function, unicode_literals

import typing as T  # noqa


PRESSURE_CONVERSION_RULES = {
    ('Pa', 'pascal'): 1.,
    ('hPa', 'hectopascal', 'hpascal', 'millibar', 'mbar'): 100.,
    ('decibar', 'dbar'): 10000.,
    ('bar',): 100000.,
    ('atmosphere', 'atm'): 101325.,
}  # type: T.Dict[T.Tuple, float]


class ConversionError(Exception):
    pass


def simple_conversion_factor(source_units, target_units, rules):
    # type: (str, str, T.Dict[T.Tuple, float]) -> float
    conversion_factor = 1.
    seen = 0
    for pressure_units, factor in rules.items():
        if source_units in pressure_units:
            conversion_factor /= factor
            seen += 1
        if target_units in pressure_units:
            conversion_factor *= factor
            seen += 1
    if seen != 2:
        raise ConversionError('Cannot convert from %r to %r' % (source_units, target_units))
    return conversion_factor


def convert_units(data, target_units, source_units):
    # type: (T.Any, str, str) -> T.Any
    if target_units == source_units:
        return data
    for rules in [PRESSURE_CONVERSION_RULES]:
        try:
            return data * simple_conversion_factor(target_units, source_units, rules)
        except ConversionError:
            pass
    raise ConversionError('Cannot convert from %r to %r' % (source_units, target_units))


def are_convertible(source_units, target_units):
    # type: (str, str) -> bool
    try:
        convert_units(1, source_units, target_units)
    except ConversionError:
        return False
    return True
