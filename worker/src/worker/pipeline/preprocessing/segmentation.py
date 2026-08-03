import cv2
import numpy as np

MIN_REGION_AREA_RATIO = 0.08
CLOSE_KERNEL_SIZE = (35, 55)
HORIZONTAL_OVERLAP_RATIO = 0.35


def _horizontal_overlap_ratio(left: tuple[int, int], right: tuple[int, int]) -> float:
    left_x, left_w = left
    right_x, right_w = right
    left_end = left_x + left_w
    right_end = right_x + right_w
    overlap = max(0, min(left_end, right_end) - max(left_x, right_x))
    shorter = max(1, min(left_w, right_w))
    return overlap / shorter


def _cluster_by_column(boxes: list[tuple[int, int, int, int]]) -> int:
    clusters: list[tuple[int, int]] = []
    for x, _y, w, _h in sorted(boxes, key=lambda box: box[0]):
        placed = False
        for index, (cluster_x, cluster_w) in enumerate(clusters):
            if _horizontal_overlap_ratio((x, w), (cluster_x, cluster_w)) >= HORIZONTAL_OVERLAP_RATIO:
                new_x = min(cluster_x, x)
                new_w = max(cluster_x + cluster_w, x + w) - new_x
                clusters[index] = (new_x, new_w)
                placed = True
                break
        if not placed:
            clusters.append((x, w))
    return len(clusters)


def count_receipts(gray: np.ndarray) -> int:
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, CLOSE_KERNEL_SIZE)
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    image_area = float(gray.shape[0] * gray.shape[1])
    boxes = [
        cv2.boundingRect(contour)
        for contour in contours
        if cv2.contourArea(contour) > MIN_REGION_AREA_RATIO * image_area
    ]
    if not boxes:
        return 0
    return _cluster_by_column(boxes)
