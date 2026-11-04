import os
import sys
import cv2
import numpy as np
from PIL import Image

folder = r"c:\Users\Friends\Desktop\Pixabay1000"
files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))][:20]

for idx, f in enumerate(files):
    fpath = os.path.join(folder, f)
    with Image.open(fpath) as img:
        w, h = img.size
        rgb = img.convert("RGB")
        thumb = rgb.resize((160, 160))
        arr = np.array(thumb)
    
    # BGR for cv2
    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    
    # Masks
    # Foliage / Green Flora
    green_mask = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))
    green_ratio = cv2.countNonZero(green_mask) / (160 * 160)
    
    # Sky / Water Blue
    blue_mask = cv2.inRange(hsv, np.array([90, 40, 40]), np.array([135, 255, 255]))
    blue_ratio = cv2.countNonZero(blue_mask) / (160 * 160)
    
    # Skin tone (Human Presence)
    skin_mask = cv2.inRange(hsv, np.array([0, 30, 60]), np.array([25, 170, 255]))
    skin_ratio = cv2.countNonZero(skin_mask) / (160 * 160)
    
    # Red spectrum (Fruits / Flowers / Accents)
    red1 = cv2.inRange(hsv, np.array([0, 70, 50]), np.array([10, 255, 255]))
    red2 = cv2.inRange(hsv, np.array([170, 70, 50]), np.array([180, 255, 255]))
    red_ratio = (cv2.countNonZero(red1) + cv2.countNonZero(red2)) / (160 * 160)
    
    # Edges (Structure / Detail complexity)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = cv2.countNonZero(edges) / (160 * 160)
    
    # Categorization logic
    is_human = skin_ratio > 0.08 and edge_density < 0.25
    is_flora = green_ratio > 0.18
    is_marine_sky = blue_ratio > 0.30
    
    category = "General / Studio"
    if is_human:
        category = "Human Subject / Portrait"
    elif is_flora:
        category = "Botanical / Flora / Nature"
    elif is_marine_sky:
        category = "Landscape / Sky & Water"
    elif red_ratio > 0.15:
        category = "Vibrant / Fruit / Accent"
        
    print(f"[{idx+1:2d}] {f[:22]}... | Cat: {category:<26} | Green: {green_ratio*100:4.1f}% | Blue: {blue_ratio*100:4.1f}% | Skin: {skin_ratio*100:4.1f}% | Red: {red_ratio*100:4.1f}%")
