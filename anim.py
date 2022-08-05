import pandas as pd
import lightkurve as lk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
plt.close()




data = pd.read_csv('cumulative_2022.08.04_22.18.20.tab', sep='\t')
data = data.dropna()

# x = data[(data.koi_period > 10) & (data.koi_period < 40) & (data.koi_prad > 10)].sample().squeeze()
x = data[(data.koi_period > 4) & (data.koi_period < 12) & (data.koi_prad > 3)].sample().squeeze()

first_q = x.koi_quarters.index('1', 2) + 1
lcf = lk.search_lightcurve(f"KIC {x.kepid}", author='Kepler', quarter=first_q).download()
lc_flux = lcf.pdcsap_flux
lc_flux[lcf.quality > 0] = np.nan

lc_times = lcf.time.to_value(format='jd') - 2454833
ylab = 'pdcsap_flux [e'+r'$^-$'+'s'+r'$^{-1}$'+']'
xlab = 'Time - 2454833 [BKID days]'
tit = f"Q:{first_q}, KID:{x.kepid}, Period (days):{x.koi_period}, Radius[$\odot$]:{x.koi_prad}"

fig = plt.figure()
xdata, ydata = [], []
ln, = plt.plot([], [], 'o-b', clip_on=False, markersize=1, linewidth=2)
plt.xlim(lc_times[0], lc_times[-1])
plt.ylim(np.nanmin(lc_flux.to_value()), np.nanmax(lc_flux.to_value()))
plt.xlabel(xlab)
plt.ylabel(ylab)
plt.title(tit)

def update(frame):
    ln.set_data(lc_times[:frame], lc_flux[:frame])
    ln.set_clip_on(False)
    print(frame)
    return ln,

fps = 45
anim = FuncAnimation(
    fig, update, frames=np.arange(len(lc_times)),
    # init_func=init,
    blit=True,
    interval=1000//fps,
)

plt.show()
# writergif = PillowWriter(fps=fps)
# anim.save('picture.gif', writergif)
