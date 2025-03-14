#

from bisect import bisect_left, bisect_right
import pandas as pd
import geopandas as gpd

from constants import NULL_TIME

def find_lt(a, x):
    'Find rightmost value less than x'
    i = bisect_left(a, x)
    if i:
        return a[i-1]
    else:
        return NULL_TIME

def find_le(a, x):
    'Find rightmost value less than or equal to x'
    i = bisect_right(a, x)
    if i:
        return a[i-1]
    else:
        return NULL_TIME

def find_gt(a, x):
    'Find leftmost value greater than x'
    i = bisect_right(a, x)
    if i != len(a):
        return a[i]
    else:
        return NULL_TIME

def find_ge(a, x):
    'Find leftmost item greater than or equal to x'
    i = bisect_left(a, x)
    if i != len(a):
        return a[i]
    else:
        return NULL_TIME

def gdf_concat(dfs):
    return gpd.GeoDataFrame(
        pd.concat(
            dfs,
            axis=0,
            verify_integrity=True,
            sort=True
        ),
        crs=dfs[0].crs
    )
