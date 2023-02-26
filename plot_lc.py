from astropy.io import fits
import numpy.ma as ma
import numpy as np
import pickle
import os
import sys
import matplotlib as mpl
if os.environ.get('DISPLAY','') == '':
    mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import scipy.special as spec
import pandas as pd
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

from matplotlib import rc
rc('text', usetex=True)
rc('font',**{'family':'serif','serif':['Times']})

def threshold_positive(data):
    std_ = np.nanstd(data)
    diff = np.ediff1d(data)
    thresh = 3*std_
    mask = np.ones(len(data), dtype=bool)
    for j in range(len(data)-1):
        if np.abs(diff[j]) > thresh: mask[j+1] = 0
        if np.abs(data[j]) > thresh: mask[j] = 0
    std_ = np.nanstd(data[mask])
    thresh =  3*std_
    for j in range(len(data)):
        if data[j] > thresh: data[j] = np.random.normal(0, std_)
    return data

def get_exo():
    """
    Returns a cleaned lightcurve, phase folded about the transit event with a +- 4 dur window: 'trunc_flux' and an associated array of times 'trunc_times', as well as the parameters of the exoplanet:
    'trunc flux'- Normalized flux (transit depth in ppm)
    'trunc times' - Times [days]
    'start/end_time_ind' - the index of the first and last in-transit flux value
    'window' - length of window [days]
    parameters ~ k_id, prd, time0bk, dur, radius_p_s_ratio, radius_p, lc.kepmag, lc.ra_obj, lc.dec_obj, depth
    """
    #BJD-2454833
    lc_sample_time = 29.424
    BKJD_start_time = 2454833 # offset of Kepler start time in BJD
    data = pd.read_csv('cumulative_2023.02.25_10.21.50.tab', sep='\t', dtype={'koi_quarters': str})
    data = data.dropna()

    x = data[(data.koi_period > 4) & (data.koi_period < 12) & (data.koi_prad > 3) & ((data.koi_quarters.apply(lambda val: sum(map(int, list(val)))))>12)].sample().squeeze()

    prd = x.koi_period
    time0bk = x.koi_time0bk
    dur = x.koi_duration
    depth = x.koi_depth
    radius_p_s_ratio = x.koi_ror
    radius_p = x.koi_prad
    k_id = x.kepid
    print (k_id)

    lc_files = lk.search_lightcurve(f"KIC {k_id}", author='Kepler', cadence = "long").download_all()
    print ('elapse')
    flux = []
    for lcf in lc_files:
        lc_flux = lcf.pdcsap_flux.to_value()
        lc_median = np.nanmedian(lc_flux)
        lc_clean = threshold_positive(lc_flux - lc_median) + lc_median 
        flux.extend(lc_clean/lc_median)

    flux = np.array(flux)

    lc = lc_files.stitch()
    lc_times = lc.time.to_value(format='bkjd')# or 'bjd'

    period = int(prd*1440/lc_sample_time)
    dur_sample = int(dur*60/lc_sample_time)
    epoch = int(time0bk*1440/lc_sample_time)
    #lc.radius, star rad

    lc_cad = lc.cadenceno # time in units of long cadence samples
    lc_cad = lc_cad[lc.quality == 0]
    flux = flux[lc.quality == 0]
    lc_times = lc_times[lc.quality == 0]

    sort = np.sort((lc_times - time0bk)%prd)
    sort_ind = np.argsort((lc_times - time0bk-(prd/2))%prd)

    width = 4 #no of transit durations to plot
    half_window = width*np.ceil(dur)/24
    window = 2*half_window

    trunc_sort_ind = sort_ind[(sort > prd/2 - half_window) & (sort < prd/2 + half_window)]
    trunc_sort = sort[(sort > prd/2 - half_window) & (sort < prd/2 + half_window)]
    trunc_flux = flux[trunc_sort_ind]
    start_transit_ind = np.argmax(trunc_sort>(prd/2 - dur/12))
    end_transit_ind = np.argmax(trunc_sort>(prd/2 + dur/12))

#    plt.figure()
#    plt.scatter(trunc_sort, trunc_flux, s=.2, label = 'phase folded data (KepID: %s, p: %s[D] d: %s[h], epoch: %s[BJD-%s])' % (int(k_id), "{:.2f}".format(float(prd)), int(dur),"{:.2f}".format(time0bk), int(BKJD_start_time)))
#    plt.ylabel('Flux - median')
#    plt.xlabel('Time since transit midpoint[h]')
#    if dur<5:
#        plt.xticks(np.linspace((prd/2) - half_window, (prd/2) + half_window + (1/24), 2*int(width*np.ceil(dur))+1 ), np.arange(-int(width*np.ceil(dur)), int(width*np.ceil(dur))+1, 1, dtype='int'))
#    else:
#        plt.xticks(np.linspace((prd/2) - half_window, (prd/2) + half_window + (2/24), 4*int(width*np.ceil(dur))+2 ), np.arange(-int(width*np.ceil(dur)), int(width*np.ceil(dur))+2, 2, dtype='int'))
#    plt.legend(loc = 'lower right')
#    plt.show()
    return (trunc_flux, trunc_sort, start_transit_ind, end_transit_ind, window, k_id, prd, time0bk, dur, radius_p_s_ratio, radius_p, lc.kepmag, lc.ra_obj, lc.dec_obj, depth)
#=================================

trunc_flux, trunc_sort, start_transit_ind, end_transit_ind, window, k_id, prd, time0bk, dur, radius_p_s_ratio, radius_p, kepmag, ra_obj, dec_obj, depth = get_exo()

# time, t
#c = s_grav_2, cmap = 'winter'

#Planet param format
print ('Kepler ID: %s, Period[days]: %s, Epoch[BKJD]: %s, Duration[hr]: %s, Radius planet/star: %s, Radius planet[Earth rad]: %s, Kepler mag: %s, RA: %s, Dec: %s' % (int(k_id), "{:.2f}".format(float(prd)), "{:.2f}".format(float(time0bk)), int(dur), "{:.3f}".format(float(radius_p_s_ratio)), "{:.2f}".format(float(radius_p)),  "{:.2f}".format(float(kepmag)), "{:.2f}".format(float(ra_obj)), "{:.2f}".format(float(dec_obj))))

