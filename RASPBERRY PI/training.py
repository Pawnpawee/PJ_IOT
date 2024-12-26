import cv2
import os
import dlib
import numpy as np
from PIL import Image

# ฟังก์ชันตรวจสอบการมีอยู่ของโฟลเดอร์ หากไม่มีจะสร้างขึ้นมา
def assure_path_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

# ฟังก์ชันดึงภาพและจากโฟลเดอร์ที่ใช้เก็บรูปภาพ
def get_images_and_labels(path):
    # ดึงเส้นทางของภาพทั้งหมดที่เป็น .jpg, .png, .jpeg
    image_paths = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(('.jpg', '.png', '.jpeg'))]
    if not image_paths:  # หากไม่มีไฟล์ภาพในโฟลเดอร์
        raise ValueError("No training images found in the specified directory.")

    face_samples = []  # เก็บภาพใบหน้าที่ตรวจจับได้
    ids = []  # เก็บ ID ที่เกี่ยวข้องกับภาพใบหน้าเพื่อไปใช้ในขั้นตอน face_recognition
    failed_images = []  # เก็บไฟล์ที่ประมวลผลล้มเหลว

    for image_path in image_paths:  # วนลูปในแต่ละภาพจนกว่าจะครบ
        try:
            # เปิดภาพและแปลงเป็น grayscale
            PIL_img = Image.open(image_path).convert('L')
            img_numpy = np.array(PIL_img, 'uint8')  # แปลงเป็น numpy array เพื่อประมวลผลได้ดียิ่งขึ้น

            # ดึง ID จากชื่อไฟล์
            try:
                id = int(os.path.split(image_path)[-1].split(".")[1])  # ID อยู่ในชื่อไฟล์ เช่น Person.1.jpg ถ้าเป็น ID = 2 ชื่อไฟล์ก็จะเป็น Person.2.jpg
            except (ValueError, IndexError):  # หากรูปแบบชื่อไฟล์ไม่ถูกต้อง
                print(f"Skipping file with invalid format: {image_path}")
                failed_images.append(image_path)
                continue

            # ตรวจจับใบหน้าด้วย dlib
            detector = dlib.get_frontal_face_detector()
            faces = detector(img_numpy)

            if len(faces) == 0:  # หากไม่พบใบหน้า
                print(f"No face detected in: {image_path}")
                failed_images.append(image_path)
                continue

            # วนลูปในใบหน้าที่ตรวจจับได้
            for face in faces:
                x, y, w, h = (face.left(), face.top(), face.width(), face.height())
                # ครอปส่วนของใบหน้า
                face_region = img_numpy[y:y+h, x:x+w]
                face_region = cv2.resize(face_region, (150, 150))  # ปรับขนาดรูปภาพเป็น 150x150
                face_region = cv2.equalizeHist(face_region)  # ใช้ histogram equalization เพื่อปรับปรุงแสง
                face_samples.append(face_region)  # เพิ่มภาพใบหน้าในรายการ
                ids.append(id)  # เพิ่ม ID ในรายการ

            print(f"Processed image: {image_path}, ID: {id}")

        except Exception as e:  # หากเกิดข้อผิดพลาดระหว่างการประมวลผล
            print(f"Error processing image {image_path}: {e}")
            failed_images.append(image_path)

    # แสดงสรุปการประมวลผล
    print(f"\nProcessed {len(face_samples)} faces successfully.")
    if failed_images:
        print(f"Failed to process {len(failed_images)} images. Check logs for details.")

    return face_samples, ids

# สร้างตัวจดจำใบหน้าด้วย Local Binary Patterns Histogram (LBPH)
recognizer = cv2.face.LBPHFaceRecognizer_create(radius=2, neighbors=8, grid_x=8, grid_y=8)

if __name__ == "__main__":
    try:
        training_data_path = 'training_data'  # เส้นทางโฟลเดอร์ข้อมูลการฝึก
        print("Starting training process...")

        # ดึงใบหน้ามาจากข้อมูลการฝึก
        faces, ids = get_images_and_labels(training_data_path)

        if len(faces) == 0 or len(ids) == 0:  # หากไม่มีใบหน้าหรือป้ายกำกับ
            raise ValueError("No valid faces or labels found. Ensure training data is prepared correctly.")

        # เริ่มการฝึกตัวจดจำใบหน้า
        print("Training the recognizer...")
        recognizer.train(faces, np.array(ids))

        # บันทึกโมเดลที่ฝึกสำเร็จ
        model_path = 'saved_model/s_model.yml'
        assure_path_exists('saved_model/')  # สร้างโฟลเดอร์หากไม่มี
        recognizer.write(model_path)  # บันทึกโมเดล
        print(f"Model saved at: {model_path}")

    except Exception as e:  # หากเกิดข้อผิดพลาดในขั้นตอนใดๆ
        print(f"Error during training: {e}")
