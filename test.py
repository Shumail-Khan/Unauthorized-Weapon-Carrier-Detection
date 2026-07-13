import cv2
import time
from ultralytics import YOLO

model = YOLO("./Backend/models/V2_best.pt")

img = cv2.imread("./test.png")

start = time.time()

for _ in range(50):
    model(img)

print("Average:",
      (time.time() - start) / 50)