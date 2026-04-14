import cv2
import numpy as np

try:
    detector = cv2.FaceDetectorYN.create(
        "model.onnx", # This won't work yet, but let's see if the class exists
        "",
        (320, 320)
    )
    print("CV2 FaceDetectorYN exists")
except AttributeError:
    print("CV2 FaceDetectorYN does NOT exist")
except Exception as e:
    print(f"CV2 Error: {e}")
