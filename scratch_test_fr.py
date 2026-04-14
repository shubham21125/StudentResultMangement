try:
    import face_recognition
    import numpy as np
    import dlib
    print(f"Dlib version: {dlib.__version__}")
    print(f"Face Recognition version: {face_recognition.__version__}")
    
    # Try to load models directly
    import face_recognition_models
    print(f"Models path: {face_recognition_models.__file__}")
    
    # Test a simple function
    # image = face_recognition.load_image_file("some_image.jpg")
    # face_locations = face_recognition.face_locations(image)
    print("Import successful and modules found!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
