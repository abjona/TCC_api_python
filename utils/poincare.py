from utils import orientation
import math
import cv2 as cv
import numpy as np


def poincare_index_at(i, j, angles, tolerance):

    cells = [(-1, -1), (-1, 0), (-1, 1),         # p1 p2 p3
             (0, 1),  (1, 1),  (1, 0),           # p8    p4
             (1, -1), (0, -1), (-1, -1)]         # p7 p6 p5

    angles_around_index = [math.degrees(
        angles[i - k][j - l]) for k, l in cells]
    index = 0

    for k in range(0, 8):

        difference = angles_around_index[k] - angles_around_index[k + 1]

        if difference > 90:
            difference -= 180
        elif difference < -90:
            difference += 180

        index += difference

    if ((180 - tolerance) <= index <= (180 + tolerance)):
        return "delta"
    if ((-180 - tolerance) <= index <= (-180 + tolerance)):
        return "loop"
    if ((360 - tolerance) <= index <= (360 + tolerance)):
        return "whorl"
    return "none"


def calculate_singularities(im, angles, tolerance, W, mask):
    result = cv.cvtColor(im, cv.COLOR_GRAY2RGB)

    # DELTA: RED, LOOP: ORANGE, WHORL:INK
    colors = {
        "loop": (0, 128, 255),
        "delta": (0, 0, 255),
        "whorl": (255, 153, 255)
    }

    singularity_result = {"loop": 0, "delta": 0, "whorl": 0}
    singularity_points = []
    listPoints = []

    pont1,pont2 = {},{}

    for i in range(3, len(angles) - 2):             # Y
        for j in range(3, len(angles[i]) - 2):      # x
            # mask any singularity outside of the mask
            mask_slice = mask[(i-2)*W:(i+3)*W, (j-2)*W:(j+3)*W]
            mask_flag = np.sum(mask_slice)

            if mask_flag == (W*5)**2:
                singularity = poincare_index_at(i, j, angles, tolerance)
                
                pt1 = (j+0)*W
                pt2 = (i+0)*W
                pt3 = (j+1)*W
                pt4 = (i+1)*W

                if singularity != "none" :
                    # print(singularity)
                    cv.rectangle(result, ((j+0)*W, (i+0)*W),
                                 ((j+1)*W, (i+1)*W), colors[singularity], 2)
                    if (pt1 not in listPoints):
                        singularity_result[singularity] += 1
                        pont1[singularity], pont2[singularity] = pt1, pt2
                        listPoints.append((j+0)*W)
                        listPoints.append((i+0)*W)
                        listPoints.append((j+1)*W)
                        listPoints.append((i+1)*W)

    print(singularity_result)
    if(singularity_result["loop"] == 1 and singularity_result["delta"] == 1):
        x1, y1 = pont1["loop"], pont2["loop"]
        x2, y2 = pont1["delta"], pont2["delta"]

        print(x1, y1)
        print(x2, y2)

        teste = x2 - x1
        teste2 = y2 - y1
        print(teste, "/", teste2)

    return result, singularity_result
