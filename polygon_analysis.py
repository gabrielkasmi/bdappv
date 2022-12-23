#!/usr/bin/env python

import os

import cv2
import matplotlib.pyplot as plt
import numpy as np

from lib.model import Polygon, Point, Image, SurfaceResult
from lib.utils import get_image, main_process, Arg, Campaign, Phase

WIDTH=400
HEIGHT=400
DEFAULT_THRESHOLD=0.45
THRESHOLD_AREA=100

IMAGE_TYPE_THRES="threshold"
IMAGE_TYPE_POLY="polygon"
IMAGE_TYPE_ALL="all"

def draw_polys(polys, label, selected_idx=None, color="red") :
    first=True
    for idx, poly in enumerate(polys):
        points = poly.points
        color = "red" if (idx == selected_idx) else color
        for i in range(-1, len(points) - 1):
            x = [points[i].x, points[i + 1].x]
            y = [points[i].y, points[i + 1].y]

            if first :
                first = False
            else:
                label = None

            plt.plot(x, y, marker="+", color=color, label=label)

def points2cv2(points) :
    """Transform list of points to be used by opencv2"""
    return np.array([[pt.x, pt.y] for pt in points]).astype(np.int32)

def process_img(
        img : Image, threshold=DEFAULT_THRESHOLD, out=None,
        image_type=IMAGE_TYPE_THRES, display=False, campaign=Campaign.GOOGLE,
        polys_to_draw=None,
        selected_idx=None, **kwargs):

        matrix = np.zeros((WIDTH, HEIGHT))

        res = SurfaceResult(img.id)

        # No input polygon ? Not part of phase 2 : skip.
        if len(img.polygons) == 0 :
            return None

        # Draw polygons
        for poly in img.polygons :

            pts = list((pt.x, pt.y) for pt in poly.points)

            poly_img = np.zeros((WIDTH, HEIGHT), np.uint8)
            cv2.fillPoly(poly_img, np.array([pts]), 1)

            matrix += poly_img

        # Blur image to prevent noise
        matrix = cv2.blur(matrix, (3, 3))

        nb_actors = len(set(poly.action.actorId for poly in img.polygons))

        # Threshold < 1 is ratio of number of actors
        if threshold < 1 :
            threshold = threshold * nb_actors

        # Apply threshold
        ret, thres = cv2.threshold(matrix, threshold, 255, 0)
        thres = thres.astype(np.uint8)

        # Find polygons in the resulting threshold mask
        contours, _ = cv2.findContours(thres, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours :

            area = cv2.contourArea(contour)
            if area < THRESHOLD_AREA :
                continue

            epsilon = 0.01 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            points = list(Point(pt[0][0], pt[0][1]) for pt in approx)

            # Compute score as mean of values within polygon
            poly_mask = np.zeros((WIDTH, HEIGHT), np.int8)
            pts = points2cv2(points)
            cv2.fillPoly(poly_mask, [pts], 1)

            # Mean value
            score = np.sum(matrix * poly_mask) / np.sum(poly_mask)

            # Update output
            poly = Polygon(score=score, area=area)
            poly.points = points

            res.polygons.append(poly)

        if out :

            if image_type == IMAGE_TYPE_THRES :
                out_img = thres

            elif image_type == IMAGE_TYPE_ALL :
                out_matrix = (matrix * 255 / nb_actors).astype(np.uint8)
                out_matrix[thres == 0] = 0

                out_img = cv2.applyColorMap(out_matrix, cv2.COLORMAP_OCEAN)
                for poly in res.polygons :
                  cv2.polylines(out_img, [points2cv2(poly.points)], True, (0, 0, 255))


            elif image_type == IMAGE_TYPE_POLY :
                out_img = np.zeros((WIDTH, HEIGHT), np.uint8)
                for poly in res.polygons:
                    cv2.fillPoly(out_img, [points2cv2(poly.points)], (255,))

            cv2.imwrite(os.path.join(out, "%s.png" % img.id), out_img)

        # Plots
        if display :

            fig = plt.gcf()

            path = get_image(img.id, phase=Phase.SURF, campaign=campaign)
            image = plt.imread(path)

            heat_ax = plt.subplot2grid((1, 2), (0, 1))
            matrix[matrix < 0.1] = np.nan
            heat_plt = plt.imshow(matrix)
            # draw_polys(polys, selected_idx)

            plt.subplot2grid((1, 2), (0, 0))
            plt.imshow(image)

            # Annotations in red
            draw_polys(img.polygons, color="red", label="annotations")

            # Selected poly in blue
            selected_polys = polys_to_draw if polys_to_draw else res.polygons
            draw_polys(selected_polys, color="blue", label="selected polygons (> %0.1f)" % threshold, selected_idx=selected_idx)

            plt.legend(loc='upper left')

            # Scale
            cax = fig.add_axes(
                [heat_ax.get_position().x1 + 0.01, heat_ax.get_position().y0, 0.02, heat_ax.get_position().height])
            cbar = plt.colorbar(heat_plt, cax=cax)  # Similar to fig.colorbar(im, cax = cax)
            cbar.set_label(r'polygon annotation consensus (-)', fontsize=12)

            plt.show()

        # Only return matches
        if len(res.polygons) == 0:
            return None
        else:
            return res



if __name__ == '__main__':

    threshold_arg = Arg('--threshold', '-t', type=float, default=DEFAULT_THRESHOLD,
                        help="Threshold value as fraction of number of actors. %.2f by default" % DEFAULT_THRESHOLD)
    image_type = Arg('--image-type', '-it', choices=[IMAGE_TYPE_POLY, IMAGE_TYPE_THRES, IMAGE_TYPE_ALL], default=IMAGE_TYPE_THRES,
                        help="Type of output images. "
                             "'polygon' : Outputs binary image of best polygon. "
                             "'threshold (default)' : Outputs binary image of threshold (before detection of polygon). "
                             "'all' : Outputs both raw level of detection in gray and final polygon in red.")

    main_process(process_img, [threshold_arg, image_type])