#!/usr/bin/env python3

import pandas as pd
import numpy as np
import lightkurve as lk

#=================================
# EXOPLANET DATA FORMAT
# koi_period, koi_time0 (BKJD), koo_dur, koi_depth, koi_ror, koi_prad,
# COLUMN kepid:          KepID
# COLUMN koi_period:     Orbital Period [days]
# COLUMN koi_time0bk:    Transit Epoch [BKJD]
# COLUMN koi_duration:   Transit Duration [hrs]
# COLUMN koi_depth:      Transit Depth [ppm]
# COLUMN koi_ror:        Planet-Star Radius Ratio
# COLUMN koi_prad:       Planetary Radius [Earth radii]
# COLUMN koi_quarters:   Quarters
# COLUMN koi_disposition: Exoplanet Archive Disposition
#=================================
#https://exoplanetarchive.ipac.caltech.edu/cgi-bin/TblView/nph-tblView?app=ExoTbls&config=cumulative
# Description of the columns in the list of all known KOI - cumulative.tab

def threshold_positive(x):
    """Find outliers and replace them with samples from a Gaussian"""
    data = np.copy(x)
    std = np.nanstd(data)
    absdiff = np.abs(np.diff(data, prepend=data[0]))
    thresh = 3 * std

    outlier = np.zeros(len(data), dtype=bool)
    outlier[data > thresh] = True
    outlier[absdiff > thresh] = True

    # replace outliers with randomly sampled values
    std_inliers = np.nanstd(data[~outlier])
    data[outlier] = np.random.normal(0, std_inliers, size=outlier.sum())

    return data

def get_lightcurve(test=False):
    """Return a lightcurve and its associated data

    Args:
        test (bool): always return the same lightcurve so it can be cached by
            lightkurve

    Returns:
        lc (pandas DataFrame): phase-folded and cleaned lightcurve in a pandas dataframe.
            The relevant column is 'flux_clean'
        lc_info (pandas Series): contains information about the specific
            lightcurve such as Kepler ID ('kepid'), orbital period ('koi_period'),
            transit duration ('koi_duration'), planet/star ratio ('koi_ror'),
    """

    lc_sample_time = 29.424
    BKJD_start_time = 2454833 # offset of Kepler start time in BJD
    data = pd.read_csv('cumulative_2023.02.25_10.21.50.tab', sep='\t', dtype={'koi_quarters': str})
    data = data.dropna()
    data['num_quarters'] = data.koi_quarters.apply(lambda x: sum(map(int, list(x))))

    # filter out bad lightcurve candidates
    data = data[
        (data.koi_period > 4) &
        (data.koi_period < 12) &
        (data.koi_prad > 3) &
        (data.num_quarters>12)
    ]

    # choose a lightcurve
    if test:
        lc_info = data.iloc[0]
    else:
        lc_info = data.sample().squeeze()

    # download data for lightcurve and optionally cache it
    lc_files = lk.search_lightcurve(
        f"KIC {lc_info.kepid}", author='Kepler', cadence = "long"
    ).download_all(download_dir='.' if test else None)

    lc_chunks = []
    for lcf in lc_files:
        lc_chunk = lcf.to_pandas()
        median = np.nanmedian(lc_chunk.flux)
        lc_chunk['flux_clean'] = (threshold_positive(lc_chunk.flux - median) + median) / median
        lc_chunks.append(lc_chunk)

    # stitch lightcurve data and filter out low quality data points
    lc = pd.concat(lc_chunks).query('quality == 0')

    # phase fold data points
    lc['folded_time'] = (
        lc.time.to_value(format='bkjd') - lc_info.koi_time0bk - lc_info.koi_period / 2
    ) % lc_info.koi_period
    lc = lc.sort_values('folded_time')

    # hours from middle of transit
    lc['transit_hours'] = (lc.folded_time - lc_info.koi_period / 2) / 24

    return lc, lc_info
