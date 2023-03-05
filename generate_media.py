import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
import textwrap

from get_lightcurve import get_lightcurve

def generate_text(lc_info):
    """Generate text about a lightcurve for social media

    Args:
        lc_info (pandas Series): lightcurve information from get_lightcurve

    """
    return textwrap.dedent(f"""\
    Kepler ID: {lc_info.kepid}
    Orbital Period: {lc_info.koi_period} days
    Transit Duration: {lc_info.koi_duration} hours
    Planet Size: {lc_info.koi_prad} Earth radii
    Location: {lc_info.ra} RA {lc_info.dec} DEC
    """)

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
    transit.set_xticks(np.arange(w*ppu))
    transit.set_yticks(np.arange(h*ppu))
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
    # r_mapped = (dist / star_radius)**(1.3)
    r_mapped = dist**1.3
    # r_mapped[mask] = 0
    inner = (255, 155, 50)
    outer = (182, 11, 0)
    transit_img = r_mapped[:, :, None] * outer + (1 - r_mapped[:, :, None]) * inner
    transit_img[mask] = (0, 0, 0)

    # transit.imshow(transit_img.astype('uint8'), aspect='equal')
    transit.imshow(transit_img.astype(int), aspect='equal')
    planet = plt.Circle((0, 0), lc_info.koi_ror * star_radius * ppu, color='k')
    transit.add_artist(planet)
    transit.axis(False)

    # import ipdb
    # ipdb.set_trace()

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
    # make transparent background
    inset.patch.set_alpha(0)
    inset.axis(False)

    # ----- Lightcurve Plot -----

    # grab actual transit part of data
    half_window = 4 * lc_info.koi_duration / 24 # size of plotted window (days)
    # window boundaries (days)
    w_start = lc_info.koi_period / 2 - half_window
    w_end = lc_info.koi_period / 2 + half_window
    # transit boundaries (days)
    t_start = lc_info.koi_period / 2 - (lc_info.koi_duration / 24) / 2
    t_end = lc_info.koi_period / 2 + (lc_info.koi_duration / 24) / 2

    transit = (w_start <= lc.folded_time) & (lc.folded_time < w_end)
    curve.plot(lc.transit_hours[transit], lc.flux_clean[transit], 'wo', markersize=1)
    curve.set_yticks([])
    curve.set_xlabel('Time to transit (h)')
    curve.margins(x=0)
    curve_t = curve.axvline(x=0, ls='--', alpha=0)

    # import ipdb
    # ipdb.set_trace()

    def animate(t):
        # which objects need updating
        artists = []

        # --- Transit graphic ---
        # only draw planet during transit frames
        if t_start <= t < t_end:
            planet.set_alpha(1)
            planet.set_center((
                # planet x position
                (t - t_start) / (lc_info.koi_duration / 24) * star_radius * 2 * ppu,
                # planet y position
                h * ppu//2
            ))
            artists.append(planet)
        elif planet.get_alpha() == 1:
            planet.set_alpha(0)
            artists.append(planet)

        # --- Orbit inset diagram ---
        # make planet orbit star, starting at pi/2
        c = p_dist * np.cos(2 * np.pi * t / lc_info.koi_period + np.pi / 2)
        s = p_dist * np.sin(2 * np.pi * t / lc_info.koi_period + np.pi / 2)
        planet_inset.set_center((0.5 + c, 0.5 + s))
        artists.append(planet_inset)

        # --- Lightcurve cursor ---
        # only show cursor during window frames
        if w_start <= t < w_end:
            curve_t.set_alpha(1)
            # fraction of window complete
            w_frac = (t - w_start) / (2 * half_window)
            xlim = curve.get_xlim()
            t = w_frac * (xlim[1] - xlim[0]) + xlim[0]
            curve_t.set_xdata([t, t])
            artists.append(curve_t)
        elif curve_t.get_alpha() == 1:
            curve_t.set_alpha(0)
            artists.append(curve_t)

        return artists


    # total animation frames
    times = np.concatenate((
        np.linspace(0, w_start, 100),
        np.linspace(w_start, w_end, 200),
        np.linspace(w_end, lc_info.koi_period, 100)
    ))

    # plt.tight_layout()
    anim = animation.FuncAnimation(fig, animate, frames=times, interval=15, blit=True)
    return anim

