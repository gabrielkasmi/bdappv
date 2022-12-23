#!/usr/bin/env python
import os

import matplotlib.pyplot as plt
import numpy as np
from skimage.feature import peak_local_max

from lib.model import Point, ClickResult
from lib.utils import get_image, main_process, Phase, Campaign, Arg

SIGMA=25
WIDTH=400
HEIGHT=400
DEFAULT_THRESHOLD=2.0

X=None
Y=None



def process_img(
        img, out_folder=None, display=False, threshold=DEFAULT_THRESHOLD, sigma=SIGMA, campaign=Campaign.GOOGLE,
        clicks_to_draw=None,
        selected_idx=None,
        **kargs):
    """

    :param img: Image object  metea data of image being processed
    :param out: Output folder for output image : None if no output is requested
    :param display: If true Display resulting output image
    :param threshold: Threshold for detection of points. Eirger as absolute number (if > 1) or ratio of number of clicks (<1)
    :param sigma: size of the kernels
    :param campaign: "google" or "ign" : only used ig display=True, for showing source image
    :return: result clicks or None if no match is found
    """

    global X, Y

    if X is None :
        X, Y = np.meshgrid(np.arange(0, WIDTH), np.arange(0, HEIGHT))

    nb_clicks = len(img.clicks)

    # Clicks coordinates
    click_x = np.array(list(click.x for click in img.clicks))
    click_y = np.array(list(click.y for click in img.clicks))

    # Work matrix
    matrix = np.zeros((WIDTH, HEIGHT))

    # Draw kernels at clicks
    for x, y in zip(click_x, click_y):
        kernel = 1 / (2 * np.pi * sigma) * np.exp(-0.5 * ((X - x) ** 2 + (Y - y) ** 2) / (sigma ** 2))
        matrix += kernel / np.max(kernel)

    # Find maximas
    res = peak_local_max(matrix)
    maxy = res[:, 0]
    maxx = res[:, 1]

    if threshold < 1 :
        threshold = threshold * nb_clicks

    # Add them to model
    out = ClickResult(img.id)

    for x, y in zip(maxx, maxy):
        score = matrix[y, x]

        if score > threshold:
            pt = Point(x, y, score=score)
            out.clicks.append(pt)

    if clicks_to_draw is None :
        clicks_to_draw = out.clicks

    # Plots
    if out_folder or display:

        #fig = plt.figure(figsize=(16, 12))
        fig = plt.gcf()

        maxx = np.array([click.x for click in clicks_to_draw])
        maxy = np.array([click.y for click in clicks_to_draw])
        maxv = np.array([click.score for click in clicks_to_draw])

        maxidx = selected_idx if selected_idx is not None else np.argmax(maxv)
        maxv = maxv[maxidx]

        path = get_image(img.id, phase=Phase.CLICK, campaign=campaign)
        image = plt.imread(path)

        def draw_points():

            plt.plot(click_x, click_y, 'r*', markersize=5, label="annotations")
            plt.scatter(maxx, maxy, s=200, color=(0, 0, 0), marker='x', linewidth=1, label="selected points  (> %0.1f)" % threshold)
            plt.scatter(maxx[maxidx:maxidx + 1], maxy[maxidx:maxidx + 1],
                label="maximum consensus (%0.1f)" % maxv,
                s=200, color=(0, 1, 0), marker='x', linewidth=2)

            plt.legend(loc='upper left')

        heat_ax = plt.subplot2grid((1, 2), (0, 1))
        draw_points()
        matrix[matrix < 0.1] = np.nan
        heat_plt = plt.imshow(matrix)

        img_ax = plt.subplot2grid((1, 2), (0, 0))
        draw_points()
        plt.imshow(image)

        cax = fig.add_axes([heat_ax.get_position().x1 + 0.01, heat_ax.get_position().y0, 0.02, heat_ax.get_position().height])
        cbar = plt.colorbar(heat_plt, cax=cax)  # Similar to fig.colorbar(im, cax = cax)
        cbar.set_label(r'Point annotation consensus (-)', fontsize=12)

        if out_folder :
            plt.savefig(os.path.join(out_folder,'%s.png' % img.id))
        else:
            fig.show()

    if len(out.clicks) == 0 :
        return None
    else :
        return out


if __name__ == '__main__':

    threshold_arg = Arg('--threshold', '-t', type=float, default=DEFAULT_THRESHOLD,
                        help="Threshold value as absolute number of clicks (if >1) or ratio of number of clicks (if <1). 2 by default")

    main_process(process_img, [threshold_arg])

