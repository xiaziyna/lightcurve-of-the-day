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
    Returns a cleaned lightcurve 'flux' and an associated array of times 'lc_times', as well as the parameters of the exoplanet:
    parameters ~ k_id, pd, time0bk, dur, radius_p_s_ratio, radius_p, lc.kepmag, lc.ra_obj, lc.dec_obj, depth
    """
    x = data[(data.koi_period > 4) & (data.koi_period < 12) & (data.koi_prad > 3) & ((data.koi_quarters.apply(lambda val: sum(map(int, list(val)))))>12)].sample().squeeze()

    pd = x.koi_period
    time0bk = x.koi_time0bk
    dur = x.koi_duration
    depth = x.koi_depth
    radius_p_s_ratio = x.koi_ror
    radius_p = x.koi_prad
    k_id = x.kepid

    lc_files = lk.search_lightcurve(f"KIC {k_id}", author='Kepler', cadence = "long").download_all()

    flux = []
    for lcf in lc_files:
        lc_flux = lcf.pdcsap_flux.to_value()
        lc_median = np.nanmedian(lc_flux)
        lc_clean = threshold_positive(lc_flux - lc_median) + lc_median 
        flux.extend(lc_clean/lc_median)

    flux = np.array(flux)

    lc = lc_files.stitch()
    lc_times = lc.time.to_value(format='bkjd')# or 'bjd'

    period = int(pd*1440/lc_sample_time)
    dur_sample = int(dur*60/lc_sample_time)
    epoch = int(time0bk*1440/lc_sample_time)
    #lc.radius, star rad

    lc_cad = lc.cadenceno # time in units of long cadence samples
    lc_cad = lc_cad[lc.quality == 0]
    flux = flux[lc.quality == 0]
    lc_times = lc_times[lc.quality == 0]

    return (flux, lc_times, k_id, pd, time0bk, dur, radius_p_s_ratio, radius_p, lc.kepmag, lc.ra_obj, lc.dec_obj, depth)

#=================================
# EXOPLANET DATA FORMAT

#BJD-2454833
lc_sample_time = 29.424
BKJD_start_time = 2454833 # offset of Kepler start time in BJD
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

data = pd.read_csv('cumulative_2023.02.25_10.21.50.tab', sep='\t', dtype={'koi_quarters': str})
data = data.dropna()

#=================================

flux, lc_times, k_id, pd, time0bk, dur, radius_p_s_ratio, radius_p, kepmag, ra_obj, dec_obj, depth = get_exo()

width = 4 #no of transit durations to plot
sort = np.sort((lc_times - time0bk)%pd)
sort_ind = np.argsort((lc_times - time0bk-(pd/2))%pd)

trunc_sort_ind = sort_ind[(sort > pd/2 - width*np.ceil(dur)/24) & (sort < pd/2 + width*np.ceil(dur)/24)]
trunc_sort = sort[(sort > pd/2 - width*np.ceil(dur)/24) & (sort < pd/2 + width*np.ceil(dur)/24)]

plt.figure()
plt.scatter(trunc_sort, flux[trunc_sort_ind], s=.2, label = 'phase folded data (KepID: %s, p: %s[D] d: %s[h], epoch: %s[BJD-%s])' % (int(k_id), "{:.2f}".format(float(pd)), int(dur),"{:.2f}".format(time0bk), int(BKJD_start_time)))
plt.ylabel('Flux - median')
#plt.ylim((1-(2*depth*(10**-6)), 1+depth*(10**-6)))
#plt.xlim(pd/2 - width*np.ceil(dur)/24, pd/2 + width*np.ceil(dur)/24)
plt.xlabel('Time since transit midpoint[hr]')
if dur<5:
    plt.xticks(np.linspace(pd/2 - width*np.ceil(dur)/24, (pd/2 + width*np.ceil(dur)/24) + (1/24), int(2*width*np.ceil(dur))+1 ), np.arange(-width*np.ceil(dur), width*np.ceil(dur)+1,1, dtype='int'))
else:
    plt.xticks(np.linspace(pd/2 - width*np.ceil(dur)/24, (pd/2 + width*np.ceil(dur)/24) + (2/24), int(width*np.ceil(dur))+1 ), np.arange(-width*np.ceil(dur), width*np.ceil(dur)+2,2, dtype='int'))
plt.legend(loc = 'lower right')
plt.show()

#Planet param format
print ('Kepler ID: %s, Period[days]: %s, Epoch[BKJD]: %s, Duration[hr]: %s, Radius planet/star: %s, Radius planet[Earth rad]: %s, Kepler mag: %s, RA: %s, Dec: %s' % (int(k_id), "{:.2f}".format(float(pd)), "{:.2f}".format(float(time0bk)), int(dur), "{:.3f}".format(float(radius_p_s_ratio)), "{:.2f}".format(float(radius_p)),  "{:.2f}".format(float(kepmag)), "{:.2f}".format(float(ra_obj)), "{:.2f}".format(float(dec_obj))))


