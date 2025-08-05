import os
import dlib
from PIL import Image
from PIL.ExifTags import TAGS

FOTO_PATH = "voorbeeldfoto.jpg"
MODEL_DIR = os.path.join("face_recognition_models", "models")
SHAPE_PREDICTOR_PATH = os.path.join(MODEL_DIR, "shape_predictor_68_face_landmarks.dat")
FACE_RECOGNITION_MODEL_PATH = os.path.join(MODEL_DIR, "dlib_face_recognition_resnet_model_v1.dat")

print("[TEST] Start directe test met dlib")

# EXIF uitlezen
try:
    image = Image.open(FOTO_PATH)
    exif = image._getexif()
    if exif:
        for tag, value in exif.items():
            if TAGS.get(tag) == 'DateTimeOriginal':
                print(f"[EXIF] Datum origineel: {value}")
    else:
        print("[EXIF] Geen EXIF metadata gevonden.")
except Exception as e:
    print(f"[EXIF FOUT] {e}")

# Gezichtsdetectie met dlib
try:
    img = dlib.load_rgb_image(FOTO_PATH)
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(SHAPE_PREDICTOR_PATH)
    encoder = dlib.face_recognition_model_v1(FACE_RECOGNITION_MODEL_PATH)

    gezichten = detector(img, 1)
    print(f"[GEZICHT] Aantal gezichten gevonden: {len(gezichten)}")

    for i, face in enumerate(gezichten):
        landmarks = predictor(img, face)
        vector = encoder.compute_face_descriptor(img, landmarks)
        print(f"[GEZICHT {i+1}] Eerste 5 waarden van encoding: {vector[:5]}")

except Exception as e:
    print(f"[Dlib fout] {e}")
