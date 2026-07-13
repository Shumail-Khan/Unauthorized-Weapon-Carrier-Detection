from ultralytics import YOLO

model = YOLO("./models/V2_best.pt")

model.export(
    format="onnx",
    imgsz=640,
    simplify=True
)