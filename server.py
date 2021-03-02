from threading import Thread
from PIL import Image
from glob import glob
import os
from utils.poincare import calculate_singularities
from utils.segmentation import create_segmented_and_variance_images
from utils.normalization import normalize
from utils.gabor_filter import gabor_filter
from utils.frequency import ridge_freq
from utils import orientation
from utils.crossing_number import calculate_minutiaes
from tqdm import tqdm
from utils.skeletonize import skeletonize
import numpy as np
import base64
import flask
import uuid
import time
import json
import sys
import io
import cv2 as cv
import requests

from flask import Flask, jsonify
from flask_swagger import swagger

SERVER_SLEEP = 0.25
CLIENT_SLEEP = 0.25

app = flask.Flask(__name__,
                  static_url_path='',
                  static_folder='./output/')


@app.route("/spec")
def spec():
    return swagger(app)


def process(nameImage):
    # result = fingerprint_pipline('101_3.tif')
    output_dir = './output/'
    block_size = 16

    im = cv.imread('./input/'+nameImage, 0)
    normalized_img = normalize(im.copy(), float(100), float(100))

    # ROI and normalisation
    (segmented_img, normim, mask) = create_segmented_and_variance_images(
        normalized_img, block_size, 0.2)

    # orientations
    angles = orientation.calculate_angles(
        normalized_img, W=block_size, smoth=False)
    orientation_img = orientation.visualize_angles(
        segmented_img, mask, angles, W=block_size)

    # find the overall frequency of ridges in Wavelet Domain
    freq = ridge_freq(normim, mask, angles, block_size,
                      kernel_size=5, minWaveLength=5, maxWaveLength=15)

    # create gabor filter and do the actual filtering
    gabor_img = gabor_filter(normim, angles, freq)

    # thinning oor skeletonize
    thin_image = skeletonize(gabor_img)

    # minutias
    (minutias, result_minutias) = calculate_minutiaes(thin_image)

    # singularities
    (singularities_img, result_singulares) = calculate_singularities(
        thin_image, angles, 1, 15, mask)

    # visualize pipeline stage by stage
    output_imgs = [im, normalized_img, segmented_img,
                   orientation_img, gabor_img, thin_image, minutias, singularities_img]
    for i in range(len(output_imgs)):
        if len(output_imgs[i].shape) == 2:
            output_imgs[i] = cv.cvtColor(output_imgs[i], cv.COLOR_GRAY2RGB)
    results = np.concatenate([np.concatenate(output_imgs[:4], 1), np.concatenate(
        output_imgs[4:], 1)]).astype(np.uint8)

    cv.imwrite(output_dir+nameImage+'.png', results)
    return result_minutias, result_singulares
    # cv.waitKeyEx()


@app.route("/classification", methods=["POST"])
def classification():
    if flask.request.method == "POST":
        r_hand = flask.request.json['r_hand']
        l_hand = flask.request.json['l_hand']
        print(r_hand)
        result = {}

        for i in range(len(r_hand)):
            response = requests.get(
                'https://finger-api-node.herokuapp.com/files/'+r_hand[i]['image'])
            if(response.status_code == 200):
                f = open('./input/'+r_hand[i]['image'], 'wb')
                f.write(response.content)
                f.close()
            (minutiae, singularity) = process(r_hand[i]['image'])
            aux = {
                'minutiae': minutiae,
                'singularity': singularity,
                'image': 'https://finger-api-python.herokuapp.com/'+r_hand[i]['image']
            }
            result[r_hand[i]['fing']] = aux

        for i in range(len(l_hand)):
            response = requests.get(
                'https://finger-api-node.herokuapp.com/files/'+l_hand[i]['image'])
            if(response.status_code == 200):
                f = open('./input/'+l_hand[i]['image'], 'wb')
                f.write(response.content)
                f.close()
            (minutiae, singularity) = process(l_hand[i]['image'])

            aux = {
                'minutiae': minutiae,
                'singularity': singularity,
                'image': 'https://finger-api-python.herokuapp.com/'+l_hand[i]['image']
            }
            result[l_hand[i]['fing']] = aux

        return flask.jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
