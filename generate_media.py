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
    r_mapped = (dist / star_radius)**(1.3)
    # inner = (255, 155, 50)
    # outer = (182, 11, 0)
    inner = np.array(temp2rgb(lc_info.teff))
    outer = inner / 1.5
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


redco = [
    1.62098281e-82, -5.03110845e-77, 6.66758278e-72, -4.71441850e-67,
    1.66429493e-62, -1.50701672e-59, -2.42533006e-53, 8.42586475e-49,
    7.94816523e-45, -1.68655179e-39, 7.25404556e-35, -1.85559350e-30,
    3.23793430e-26, -4.00670131e-22, 3.53445102e-18, -2.19200432e-14,
    9.27939743e-11, -2.56131914e-07,  4.29917840e-04, -3.88866019e-01,
    3.97307766e+02]
greenco = [
    1.21775217e-82, -3.79265302e-77, 5.04300808e-72, -3.57741292e-67,
    1.26763387e-62, -1.28724846e-59, -1.84618419e-53, 6.43113038e-49,
    6.05135293e-45, -1.28642374e-39, 5.52273817e-35, -1.40682723e-30,
    2.43659251e-26, -2.97762151e-22, 2.57295370e-18, -1.54137817e-14,
    6.14141996e-11, -1.50922703e-07,  1.90667190e-04, -1.23973583e-02,
    -1.33464366e+01]
blueco = [
    2.17374683e-82, -6.82574350e-77, 9.17262316e-72, -6.60390151e-67,
    2.40324203e-62, -5.77694976e-59, -3.42234361e-53, 1.26662864e-48,
    8.75794575e-45, -2.45089758e-39, 1.10698770e-34, -2.95752654e-30,
    5.41656027e-26, -7.10396545e-22, 6.74083578e-18, -4.59335728e-14,
    2.20051751e-10, -7.14068799e-07,  1.46622559e-03, -1.60740964e+00,
    6.85200095e+02]

redco = np.poly1d(redco)
greenco = np.poly1d(greenco)
blueco = np.poly1d(blueco)

def temp2rgb(temp):
    """Convert blackboxy color to RGB value

    Args:
        temp (float): temperature in Kelvin

    Returns
        rgb (tuple): color of black body

    Taken from https://stackoverflow.com/questions/21977786#45497817
    """

    red = redco(temp)
    green = greenco(temp)
    blue = blueco(temp)

    if red > 255:
        red = 255
    elif red < 0:
        red = 0
    if green > 255:
        green = 255
    elif green < 0:
        green = 0
    if blue > 255:
        blue = 255
    elif blue < 0:
        blue = 0

    color = (int(red),
             int(green),
             int(blue))
    print(color)
    return color
