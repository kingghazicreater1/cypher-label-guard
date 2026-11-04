import os
import time
from typing import Dict, Any, List, Optional
import cv2
import numpy as np

COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator",
    "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
]

_NET_CACHE = None

def get_yolo_net():
    global _NET_CACHE
    if _NET_CACHE is not None:
        return _NET_CACHE

    candidates = [
        os.path.abspath("models/yolov5n.onnx"),
        os.path.abspath("models/yolov8n.onnx"),
        os.path.join(os.path.dirname(__file__), "models", "yolov5n.onnx"),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                net = cv2.dnn.readNetFromONNX(path)
                _NET_CACHE = net
                return _NET_CACHE
            except Exception:
                pass
    return None

def detect_with_local_yolo(raw_bytes: bytes, conf_threshold: float = 0.25, nms_threshold: float = 0.45) -> Optional[Dict[str, Any]]:
    """
    Zero-Retention In-Memory YOLO Detection via OpenCV DNN.
    Executes in ~30ms on CPU without GPU or heavy dependencies.
    """
    net = get_yolo_net()
    if net is None or not raw_bytes:
        return None

    start_ts = time.time()

    nparr = np.frombuffer(raw_bytes, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        return None

    img_h, img_w = img_bgr.shape[:2]

    # Letterbox input to 640x640 blob for YOLO
    blob = cv2.dnn.blobFromImage(img_bgr, 1 / 255.0, (640, 640), swapRB=True, crop=False)
    net.setInput(blob)
    preds = net.forward()

    if len(preds.shape) == 3:
        preds = preds[0]

    boxes = []
    confidences = []
    class_ids = []

    x_factor = img_w / 640.0
    y_factor = img_h / 640.0

    for row in preds:
        obj_conf = row[4]
        if obj_conf >= conf_threshold:
            class_scores = row[5:]
            class_id = int(np.argmax(class_scores))
            class_score = class_scores[class_id]
            final_conf = float(obj_conf * class_score)

            if final_conf >= conf_threshold:
                cx, cy, w, h = row[0], row[1], row[2], row[3]
                left = int((cx - 0.5 * w) * x_factor)
                top = int((cy - 0.5 * h) * y_factor)
                width = int(w * x_factor)
                height = int(h * y_factor)

                boxes.append([left, top, width, height])
                confidences.append(final_conf)
                class_ids.append(class_id)

    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

    detected_items = []
    detected_boxes = []
    primary_cand = None
    max_box_area = -1

    if len(indices) > 0:
        for idx in np.array(indices).flatten():
            box = boxes[idx]
            cid = class_ids[idx]
            conf = confidences[idx]
            label = COCO_CLASSES[cid] if 0 <= cid < len(COCO_CLASSES) else f"Object_{cid}"

            friendly_label = label.title()
            if label == "cell phone":
                friendly_label = "Smartphone"
            elif label == "clock":
                friendly_label = "Watch"
            elif label == "apple":
                friendly_label = "Apple (Fruit)"

            detected_items.append(friendly_label)
            area = box[2] * box[3]
            if area > max_box_area and label != "person":
                max_box_area = area
                primary_cand = friendly_label

            detected_boxes.append({
                "label": friendly_label,
                "confidence": round(conf * 100.0, 1),
                "box": [max(0, box[0]), max(0, box[1]), box[2], box[3]],
                "normalized_box": [
                    round(max(0, box[0]) / img_w, 4),
                    round(max(0, box[1]) / img_h, 4),
                    round(box[2] / img_w, 4),
                    round(box[3] / img_h, 4),
                ],
            })

    if not primary_cand and detected_items:
        primary_cand = detected_items[0]

    human_present = any(COCO_CLASSES[class_ids[i]] == "person" for i in np.array(indices).flatten()) if len(indices) > 0 else False
    FOOD_CLASSES = {"banana", "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "bottle", "cup"}
    is_edible = any(COCO_CLASSES[class_ids[i]] in FOOD_CLASSES for i in np.array(indices).flatten()) if len(indices) > 0 else False

    latency = round((time.time() - start_ts) * 1000.0, 1)

    return {
        "success": True,
        "primary_product": primary_cand or "Visual Specimen",
        "objects": detected_items,
        "item_count": len(detected_boxes),
        "human_present": human_present,
        "human_details": "Person detected via Local YOLO Bounding Box" if human_present else "None",
        "is_edible": is_edible,
        "boxes": detected_boxes,
        "latency_ms": latency,
        "model": "YOLOv5n-ONNX (Local CPU Zero-Retention)",
    }
