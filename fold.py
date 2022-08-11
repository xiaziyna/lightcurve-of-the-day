import pandas as pd
import lightkurve as lk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from scipy.ndimage import maximum_filter1d
plt.close()


def evan_metric(data):
    # adhoc metric for evaluating how good a folded curve looks
    # should be better than 5 for good lightcurves

    filtmax = maximum_filter1d(data, size=500)
    filtmin = -maximum_filter1d(-data, size=500)
    filtrange = np.abs(filtmax - filtmin)

    return np.nanmax(filtrange) / np.nanmedian(filtrange)


data = pd.read_csv('cumulative_2022.08.04_22.18.20.tab', sep='\t')
data = data.dropna()

# x = data[(data.koi_period > 10) & (data.koi_period < 40) & (data.koi_prad > 10)].sample().squeeze()
x = data[(data.koi_period > 4) & (data.koi_period < 12) & (data.koi_prad > 3)].sample().squeeze()
x = data[data.kepid == 3532985].squeeze()

first_q = x.koi_quarters.index('1', 2) + 1
orig = lk.search_lightcurve(f"KIC {x.kepid}", author='Kepler', quarter=first_q, exptime='long').download()
# filter out bad datapoints
orig.flux[orig.quality > 0] = np.nan
orig.pdcsap_flux[orig.quality > 0] = np.nan
flat, trend = orig.flatten(window_length=301, return_trend=True)
# detrend long-term variation
periodogram = orig.to_periodogram(method="bls", period=np.arange(0.5, 20, 0.01))
best_fit_period = periodogram.period_at_max_power
# phase folding
folded = flat.fold(period=best_fit_period, epoch_time=periodogram.transit_time_at_max_power)

# %% plot

print('id:', x.kepid)
plt.figure()
plt.plot(orig.time.value, orig.pdcsap_flux.value, 'o')
plt.figure()
plt.plot(folded.time.value, folded.pdcsap_flux.value, 'o')
print('evan metric:', evan_metric(folded.pdcsap_flux))
plt.show()
