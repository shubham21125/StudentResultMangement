import setuptools
try:
    import face_recognition
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
