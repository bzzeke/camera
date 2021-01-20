import numpy as np
from math import exp

class YoloParams:
    def __init__(self, param, sides):
        self.num = param.get('num', 3)
        self.coords = param.get('coord', 4)
        self.classes = param.get('classes', 80)
        self.sides = sides
        self.anchors = param.get('anchors', [10.0, 13.0, 16.0, 30.0, 33.0, 23.0, 30.0, 61.0, 62.0, 45.0, 59.0, 119.0, 116.0, 90.0, 156.0, 198.0, 373.0, 326.0])
        self.isYoloV3 = False

        mask = param.get('mask', None)
        if mask:
            self.num = len(mask)
            masked_anchors = []
            for idx in mask:
                masked_anchors += [self.anchors[idx * 2], self.anchors[idx * 2 + 1]]
            self.anchors = masked_anchors
            self.isYoloV3 = True

def intersection_over_union(box_1, box_2):
    width_of_overlap_area = min(box_1["xmax"], box_2["xmax"]) - max(box_1["xmin"], box_2["xmin"])
    height_of_overlap_area = min(box_1["ymax"], box_2["ymax"]) - max(box_1["ymin"], box_2["ymin"])
    if width_of_overlap_area < 0 or height_of_overlap_area < 0:
        area_of_overlap = 0
    else:
        area_of_overlap = width_of_overlap_area * height_of_overlap_area
    box_1_area = (box_1["ymax"] - box_1["ymin"]) * (box_1["xmax"] - box_1["xmin"])
    box_2_area = (box_2["ymax"] - box_2["ymin"]) * (box_2["xmax"] - box_2["xmin"])
    area_of_union = box_1_area + box_2_area - area_of_overlap
    if area_of_union == 0:
        return 0
    return area_of_overlap / area_of_union


def parse_yolo_region(predictions, input_size, original_size, params, threshold):

    objects = list()
    size_normalizer = input_size if params.isYoloV3 else params.sides
    bbox_size = params.coords + 1 + params.classes
    original_y, original_x = original_size

    for row, col, n in np.ndindex(params.sides[0], params.sides[1], params.num):

        bbox = predictions[0, n * bbox_size:(n + 1) * bbox_size, row, col]
        x, y, width, height, object_probability = bbox[:5]
        class_probabilities = bbox[5:]
        if object_probability < threshold:
            continue

        x = (col + x) / params.sides[1]
        y = (row + y) / params.sides[0]

        try:
            width = np.exp(width)
            height = np.exp(height)
        except OverflowError:
            continue

        width = width * params.anchors[2 * n] / size_normalizer[0]
        height = height * params.anchors[2 * n + 1] / size_normalizer[1]

        for class_id, class_probability in enumerate(class_probabilities):
            confidence = object_probability * class_probability
            if confidence > threshold:
                objects.append({
                    "xmin": int((x - width / 2) * original_x),
                    "ymin": int((y - height / 2) * original_y),
                    "xmax": int((x + width / 2) * original_x),
                    "ymax": int((y + height / 2) * original_y),
                    "confidence": confidence,
                    "class_id": class_id
                })

    return objects
