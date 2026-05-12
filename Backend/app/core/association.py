import math

IOU_THRESHOLD = 0.01
PROXIMITY_THRESHOLD = 250

def compute_iou(A, B):
    xA = max(A["x1"], B["x1"])
    yA = max(A["y1"], B["y1"])
    xB = min(A["x2"], B["x2"])
    yB = min(A["y2"], B["y2"])

    inter = max(0, xB-xA) * max(0, yB-yA)
    if inter == 0:
        return 0

    areaA = (A["x2"]-A["x1"]) * (A["y2"]-A["y1"])
    areaB = (B["x2"]-B["x1"]) * (B["y2"]-B["y1"])

    return inter / (areaA + areaB - inter)


def center_distance(A, B):
    ax = (A["x1"] + A["x2"]) // 2
    ay = (A["y1"] + A["y2"]) // 2
    bx = (B["x1"] + B["x2"]) // 2
    by = (B["y1"] + B["y2"]) // 2

    return math.sqrt((ax-bx)**2 + (ay-by)**2)


def is_linked(person_box, obj_box):
    return (
        compute_iou(person_box, obj_box) > IOU_THRESHOLD or
        center_distance(person_box, obj_box) < PROXIMITY_THRESHOLD
    )