import os
import cv2
import face_recognition
import pickle

# Path to your folder containing the 11 images
path = 'astudents_images'

images = []
names = []

# Load images and store their names
for file in os.listdir(path):
    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
        img = cv2.imread(f'{path}/{file}')
        images.append(img)
        names.append(os.path.splitext(file)[0])  # name without extension

print("✅ Loaded images:", names)

# Function to find encodings
def find_encodings(images):
    encode_list = []
    for img in images:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodes = face_recognition.face_encodings(img_rgb)
        if len(encodes) > 0:
            encode_list.append(encodes[0])
        else:
            print("⚠️ No face detected in one image. Skipping...")
    return encode_list

# Generate encodings
encode_list_known = find_encodings(images)

print(f"✅ Encoding complete for {len(encode_list_known)} faces.")

# Save encodings and names for later use
with open('encodings.pkl', 'wb') as f:
    pickle.dump((encode_list_known, names), f)

print("💾 Encodings saved successfully as 'encodings.pkl'")