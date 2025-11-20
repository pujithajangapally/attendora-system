import face_recognition

image_path = "astudents_images/110_charanaditya.jpeg"  # replace <name>
image = face_recognition.load_image_file(image_path)
encodings = face_recognition.face_encodings(image)
print("Number of faces detected:", len(encodings))