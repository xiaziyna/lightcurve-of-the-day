import pandas as pd
import numpy as np
import pickle
import lightkurve as lk
import matplotlib.pyplot as plt

def get_curve():
    data = pd.read_csv('cumulative_2022.08.04_22.18.20.tab', sep='\t')
    data = data.dropna()

    # x = data[(data.koi_period > 10) & (data.koi_period < 40) & (data.koi_prad > 10)].sample().squeeze()
    x = data[(data.koi_period > 4) & (data.koi_period < 12) & (data.koi_prad > 3)].sample().squeeze()

    first_q = x.koi_quarters.index('1', 2) + 1
    lcf = lk.search_lightcurve(f"KIC {x.kepid}", author='Kepler', quarter=first_q).download()
    lc_flux = lcf.pdcsap_flux
    lc_flux[lcf.quality > 0] = np.nan
    lc_times = lcf.time.to_value(format='jd') - 2454833
    ylabel = 'pdcsap_flux [e'+r'$^-$'+'s'+r'$^{-1}$'+']'
    xlabel = 'Time - 2454833 [BKID days]'
    title = f"Q:{first_q}, KID:{x.kepid}, Period (days):{x.koi_period}, Radius[$\odot$]:{x.koi_prad}"

    return {
        "lc_flux": lc_flux,
        "lc_times": lc_times,
        "ylabel": ylabel,
        "xlabel": xlabel,
        "title": title
    }



#'+r'$\tau = 10$'+',
# % (t_id, "{:.2f}".format(tstat)
#
#
# plt.rcParams['text.usetex'] = True
# plt.scatter(lc_times[:48*30], lc_flux[:48*30], s=0.7)
# plt.xlabel(xlabel)
# plt.ylabel(ylabel)
# plt.title(title)
# plt.show()
