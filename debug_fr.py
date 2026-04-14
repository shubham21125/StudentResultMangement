import sys
try:
    import face_recognition_models
    print("face_recognition_models imported successfully")
except Exception as e:
    print(f"Failed to import face_recognition_models: {e}")
    sys.exit(1)

try:
    import face_recognition
    print("face_recognition imported successfully")
except Exception as e:
    print(f"Failed to import face_recognition: {e}")
    import traceback
    traceback.print_exc()
