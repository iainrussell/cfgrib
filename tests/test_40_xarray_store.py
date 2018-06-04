
from __future__ import absolute_import, division, print_function, unicode_literals

import os.path

import xarray as xr

from eccodes_grib import xarray_store

SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'sample-data')
TEST_DATA = os.path.join(SAMPLE_DATA_FOLDER, 'era5-levels-members.grib')


def test_GribDataStore():
    datastore = xarray_store.GribDataStore.fromstream(TEST_DATA)
    expected = {'number': 10, 'dataDate': 2, 'dataTime': 2, 'topLevel': 2, 'i': 7320}
    assert datastore.get_dimensions() == expected


def test_xarray_open_dataset():
    datastore = xarray_store.GribDataStore.fromstream(TEST_DATA)
    res = xr.open_dataset(datastore)

    assert res.attrs['edition'] == 1
    assert res.i.attrs['gridType'] == 'regular_ll'
    # assert res['paramId_130'].attrs['units'] == 'K'

    assert res['t'].mean() > 0.