import cv2 as cv
import numpy as np


def minutiae_at(pixels, i, j, kernel_size):
    if pixels[i][j] == 1:

        if kernel_size == 3:
            cells = [(-1, -1), (-1, 0), (-1, 1),        # p1 p2 p3
                     (0, 1),  (1, 1),  (1, 0),          # p8    p4
                     (1, -1), (0,-1), (-1, -1)]        # p7 p6 p5
        else:
            cells = [(-2, -2), (-2, -1), (-2, 0), (-2, 1), (-2, 2),                # p1 p2 p3
                     (-1, 2), (0, 2),  (1, 2),  (2, 2), (2,1), (2, 0),             # p8    p4
                     (2, -1), (2, -2), (1, -2), (0, -2), (-1, -2), (-2, -2)]       # p7 p6 p5

        values = [pixels[i + l][j + k] for k, l in cells]

        crossings = 0
        for k in range(0, len(values)-1):
            crossings += abs(values[k] - values[k + 1])
        crossings //= 2

        if crossings == 1:
            return "ending"
        if crossings == 3:
            return "bifurcation"
    return "none"


def D10(image, i, j):
    if(image[i][j] == 1):
        return 1
    return 0


def calculate_minutiaes(im, kernel_size=3):
    biniry_image = np.zeros_like(im)
    biniry_image[im < 10] = 1.0
    biniry_image = biniry_image.astype(np.int8)

    (y, x) = im.shape
    result = cv.cvtColor(im, cv.COLOR_GRAY2RGB)
    colors = {"ending": (150, 0, 0), "bifurcation": (0, 150, 0)}
    ending = 0
    bifurcation = 0
    lines = 0

    for i in range(1, x - kernel_size//2):
        for j in range(1, y - kernel_size//2):
            minutiae = minutiae_at(biniry_image, j, i, kernel_size)
            if(int(y/2) == j):
                lines += D10(biniry_image, i, j)
            if(minutiae == "ending"):
                ending += 1
            if(minutiae == "bifurcation"):
                bifurcation += 1
            if minutiae != "none":
                cv.circle(result, (i, j), radius=2,
                          color=colors[minutiae], thickness=2)

    print(lines)
    minutiae_result = {'ending': ending,
                       'bifurcation': bifurcation, 'lines': lines}
    return result, minutiae_result
