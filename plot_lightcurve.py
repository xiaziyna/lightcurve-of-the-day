import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation

from get_lightcurve import get_lightcurve

def generate_animation(lc, lc_info):
    """Generate animation

    Args:
        lc (pandas DataFrame): lightcurve DataFrame from get_lightcurve
        lc_info (pandas Series): lightcurve information from get_lightcurve
    """

    plt.close()
    plt.style.use('dark_background')
    fig, (transit, curve) = plt.subplots(2, 1)
    # manually position inset graphic
    inset = fig.add_axes([.6, .55, .3, .3])

    # ----- Transit Graphic -----

    # pixels per 'window size' unit
    ppu = 256
    # window size in 'window size' units
    w = 6
    h = 2
    x_axis = np.linspace(-w//2, w//2, w*ppu)
    y_axis = np.linspace(-h//2, h//2, h*ppu)
    transit.set_xticklabels(x_axis)
    transit.set_yticklabels(y_axis)

    # star size/position (window units)
    star_radius = 2
    center_x, center_y = (-1, 0)
    # draw the star as an image with imshow
    xx, yy = np.meshgrid(x_axis, y_axis)
    dist = np.sqrt((xx - center_x)**2 + (yy - center_y)**2)
    mask = dist > star_radius

    # adjust star color gradient
    r_mapped = dist**(1.3)
    inner = (255, 155, 50)
    outer = (182, 11, 0)
    transit_img = r_mapped[:, :, None] * outer + (1 - r_mapped[:, :, None]) * inner
    transit_img = transit_img.astype(int)
    transit_img[mask] = (0, 0, 0)

    transit.imshow(transit_img, aspect='equal')
    planet = plt.Circle((0, 0), lc_info.koi_ror * star_radius * ppu, color='k')
    transit.add_artist(planet)
    transit.axis(False)

    # ----- Orbit Inset Graphic -----

    star = plt.Circle((0.5, 0.5), 0.05, color='r')
    # planet distance from star
    p_dist = .25
    inset.axvline(x=0.5, ymin=0, ymax=0.5, ls='--', zorder=0)
    orbit = plt.Circle((0.5, 0.5), p_dist, fill=False, alpha=.5)
    planet_inset = plt.Circle((0.5, 0.5), 0.02, color='b')
    inset.add_artist(star)
    inset.add_artist(orbit)
    inset.add_artist(planet_inset)
    inset.set_aspect('equal')
    inset.axis(False)

    # ----- Lightcurve Plot -----

    # grab actual transit part of data
    half_window = 4 * lc_info.koi_duration * 24 # size of plotted window (days)
    w_start = lc_info.koi_period / 2 - half_window
    w_end = lc_info.koi_period / 2 + half_window
    t_start = lc_info.koi_period / 2 - (lc_info.koi_duration * 24) / 2
    t_end = lc_info.koi_period / 2 + (lc_info.koi_duration * 24) / 2
    lc = lc[(lc.folded_time > w_start) & (lc.folded_time < w_end)]

    # FIXME: add correct xticks
    curve.plot(lc.transit_hours, lc.flux_clean, 'wo', markersize=1)
    curve.set_yticks([])
    curve.set_xlabel('Time to transit (h)')
    curve.margins(x=0)
    curve_t = curve.axvline(x=0, ls='--')

    # total animation frames
    n_tot = 400
    # center of transit
    n_center = n_tot // 2
    # window start/end times
    n_w0 = n_center - math.floor((half_window / lc_info.koi_period) * n_tot)
    n_w1 = n_center + math.ceil((half_window / lc_info.koi_period) * n_tot)
    # transit start/end times
    start_ind = lc.folded_time.searchsorted(t_start)
    end_ind = lc.folded_time.searchsorted(t_end)
    n_t0 = n_w0 + math.floor(start_ind / len(lc) * (n_w1 - n_w0))
    n_t1 = n_w0 + math.floor(end_ind / len(lc) * (n_w1 - n_w0))

    def animate(n):
        artists = []

        # --- Transit graphic ---
        # only draw planet during transit frames
        if n in range(n_t0, n_t1):
            planet.set_alpha(1)
            p_frac = (n + 1 - n_t0) / (n_t1 - n_t0)
            planet.set_center((
                p_frac*star_radius*2*ppu,
                h*ppu//2
            ))
        else:
            planet.set_alpha(0)

        # --- Orbit inset diagram ---
        # make planet orbit star, starting at pi/2
        c = p_dist * np.cos(2 * np.pi * n / n_tot + np.pi / 2)
        s = p_dist * np.sin(2 * np.pi * n / n_tot + np.pi / 2)
        planet_inset.set_center((0.5 + c, 0.5 + s))

        # --- Lightcurve cursor ---
        # only show cursor during window frames
        if n in range(n_w0, n_w1):
            curve_t.set_alpha(1)
            # fraction of window complete
            w_frac = (n - n_w0) / (n_w1 - n_w0)
            t = w_frac * curve.get_xlim()[1] + (1 - w_frac) * curve.get_xlim()[0]
            curve_t.set_xdata([t, t])
        else:
            curve_t.set_alpha(0)
        return planet_inset, planet, curve_t

    # plt.tight_layout()
    anim = animation.FuncAnimation(fig, animate, frames=n_tot, interval=7.5, blit=True)
    return anim

lc, lc_info = get_lightcurve(test=True)
# print('Kepler ID: %s, Period[days]: %s, Epoch[BKJD]: %s, Duration[hr]: %s, Radius planet/star: %s, Radius planet[Earth rad]: %s, Kepler mag: %s, RA: %s, Dec: %s' % (int(k_id), "{:.2f}".format(float(prd)), "{:.2f}".format(float(time0bk)), int(dur), "{:.3f}".format(float(radius_p_s_ratio)), "{:.2f}".format(float(radius_p)),  "{:.2f}".format(float(kepmag)), "{:.2f}".format(float(ra_obj)), "{:.2f}".format(float(dec_obj))))
anim = generate_animation(lc, lc_info)
# mywriter = animation.FFMpegWriter(fps=60)
# anim.save('/tmp/out.mp4', writer=mywriter)
# anim.save('/tmp/out.gif',writer='imagemagick',fps=90);
plt.show()
plt.close()
