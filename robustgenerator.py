"""
Robust encoder + DB updater for Attendora.

What it does:
- Reads images from IMAGES_FOLDER
- Extracts roll_no robustly (handles "101.jpg" or "101_name.jpg")
- Trims DB roll_no and matches tolerant (TRIM)
- Detects faces (must be exactly 1 face)
- Generates 128-d encoding and stores as float32 bytes in encoding BLOB column
- Logs detailed reason when skipping a file

Edit only: DB config and IMAGES_FOLDER
Run: python generate_and_insert_encodings.py
"""

import os
import sys
import cv2
import numpy as np
import face_recognition
import mysql.connector

# -------- CONFIG (EDIT) --------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Mysql_123",   # <-- change
    "database": "attendora_db"              # <-- change if necessary
}
IMAGES_FOLDER = "astudents_images"      # folder with your images

# -------- DB helpers --------
def get_db_conn():
    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        autocommit=True
    )

def get_db_rolls_set(conn):
    cur = conn.cursor()
    cur.execute("SELECT TRIM(CAST(roll_no AS CHAR)) FROM students")
    rows = [str(r[0]).strip() for r in cur.fetchall()]
    cur.close()
    return set(rows)

# -------- Main processing --------
def process_all():
    if not os.path.isdir(IMAGES_FOLDER):
        print("ERROR: images folder not found:", IMAGES_FOLDER)
        sys.exit(1)

    conn = get_db_conn()
    db_rolls = get_db_rolls_set(conn)
    print("Roll numbers in DB (sample up to 20):", list(db_rolls)[:20])

    files = sorted([f for f in os.listdir(IMAGES_FOLDER) if f.lower().endswith((".jpg",".jpeg",".png"))])
    if not files:
        print("No image files found in", IMAGES_FOLDER)
        conn.close()
        return

    cur = conn.cursor()
    succeeded = []
    skipped = []

    for fname in files:
        fpath = os.path.join(IMAGES_FOLDER, fname)
        # robust roll extraction: take first token before underscore or dot
        base = os.path.splitext(fname)[0]
        roll_candidate = base.split("_")[0].strip()
        print("\nProcessing file:", fname, "-> extracted roll:", roll_candidate)

        # check DB match (tolerant)
        if str(roll_candidate) not in db_rolls:
            # try numeric cast variants, e.g. leading zeros or int->str
            try:
                if str(int(roll_candidate)) in db_rolls:
                    roll_no = str(int(roll_candidate))
                else:
                    print("  ❌ Roll not found in DB (exact). Skipping file.")
                    skipped.append((fname, "roll_not_found"))
                    continue
            except Exception:
                print("  ❌ Roll not found in DB. Skipping file.")
                skipped.append((fname, "roll_not_found"))
                continue
        else:
            roll_no = str(roll_candidate)

        # load image via cv2 to detect if file corrupt
        img_bgr = cv2.imread(fpath)
        if img_bgr is None:
            print("  ❌ Could not read image (corrupt or unsupported). Skipping.")
            skipped.append((fname, "bad_image"))
            continue

        # convert to RGB for face_recognition
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        # face locations
        face_locs = face_recognition.face_locations(img_rgb)
        if len(face_locs) == 0:
            print("  ❌ No face detected. Skipping.")
            skipped.append((fname, "no_face"))
            continue
        if len(face_locs) > 1:
            print("  ❌ Multiple faces detected. Skipping (use single-face image).")
            skipped.append((fname, "multiple_faces"))
            continue

        # get encoding
        encs = face_recognition.face_encodings(img_rgb, face_locs)
        if not encs:
            print("  ❌ face_encodings returned empty. Skipping.")
            skipped.append((fname, "encoding_failed"))
            continue

        enc = encs[0]
        if enc.shape[0] != 128:
            print(f"  ❌ Wrong encoding length: {enc.shape[0]}. Skipping.")
            skipped.append((fname, "wrong_length"))
            continue

        # convert to float32 bytes for compact storage: 128 * 4 = 512 bytes
        enc_bytes = enc.astype(np.float32).tobytes()

        # Update DB (use TRIM in WHERE to avoid whitespace mismatch)
        try:
            cur.execute("UPDATE students SET encoding = %s WHERE TRIM(CAST(roll_no AS CHAR)) = %s", (enc_bytes, roll_no))
            conn.commit()
            if cur.rowcount == 0:
                # fallback: try a more permissive match
                print("  ⚠ Warning: update affected 0 rows (unexpected). Trying numeric match.")
                cur.execute("UPDATE students SET encoding = %s WHERE CAST(roll_no AS SIGNED) = %s", (enc_bytes, roll_no))
                conn.commit()
                if cur.rowcount == 0:
                    print("  ❌ Still no row updated. Skipping.")
                    skipped.append((fname, "db_update_failed"))
                    continue
            print(f"  ✅ Encoding saved for roll_no {roll_no}")
            succeeded.append((fname, roll_no))
        except Exception as e:
            print("  ❌ DB error while updating:", e)
            skipped.append((fname, "db_exception"))
            continue

    cur.close()
    conn.close()

    print("\n=== SUMMARY ===")
    print("Succeeded:", len(succeeded))
    for s in succeeded[:20]:
        print(" ", s)
    print("Skipped:", len(skipped))
    for s in skipped[:50]:
        print(" ", s)

if __name__ == "__main__":
    process_all()