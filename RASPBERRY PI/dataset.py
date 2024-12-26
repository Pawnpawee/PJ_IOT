import cv2
import dlib
import os
import time
import numpy as np

# ฟังก์ชันที่เอาไว้เช็ค path directory ว่ามีไหมถ้ามีให้ทำการสร้าง
def assure_path_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

FRAME_WIDTH = 320 # ขนาดความกว้างของกล้อง
FRAME_HEIGHT = 240 # ขนาดของความยาวของกล้อง
FACE_ID = 1 # ID ของหน้าที่อยากให้จดจำ (เปลี่ยนIDเมื่อเปลี่ยนคน)
IMAGE_COUNT_LIMIT = 300 # จำนวนรูปภาพที่จะทำการแคป
SAVE_DIR = "training_data/" # สร้างโฟลเดอร์ training_data/ มาเก็บรูปภาพที่แคปเจอร์
PADDING = 20 # ขนาด padding ของภาพที่ครอปตอนแคปหน้าจอ(โค้ดนี้มันจะไม่แคปเต็มหน้าจอ มันจะทำการแคปเจอร์แล้วcropให้เหลือแค่หน้า)
ANGLE_VARIATIONS = [-15, 0, 15] # มุมองศาที่รองรับในการแคปเจอร์(รองรับการหันที่มากขึ้น(หรือเปล่า?))

# ติดตั้ง webcam
vid_cam = cv2.VideoCapture(0, cv2.CAP_V4L2)
if not vid_cam.isOpened():
    raise Exception("Could not open webcam. Ensure the webcam is connected and accessible.")

# เซ็ตขนาดของกล้องเว็บแคม
vid_cam.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
vid_cam.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

face_detector = dlib.get_frontal_face_detector() # เริ่มใช้งาน library dlib สำหรับ face detector

assure_path_exists(SAVE_DIR) # เช็คว่ามี path ที่ชื่อ "training_data/"ไหม ถ้าไม่มีทำการสร้างใหม่

count = 0 # จำนวนนับที่จะนำไปใช้ในเงื่อนไขที่แคปเจอร์ไม่เกิน 300 รูป

print("Starting image capture. Press 'q' to quit early.") # ข้อความแสดงผล

# ฟังก์ชันที่จะรับภาพที่อยู่ในตอนแคปเจอร์มาหมุนแล้วหาจุดศูนย์กลางของภาพผ่านการหมุนเรื่อยๆ และเก็บไว้ในลิสต์ หลังจากนั้นเมื่อสิ้นสุดฟังก์ชันทำการคืนค่ารูปภาพกลับไป
def augment_image(image):
    augmented_images = []
    for angle in ANGLE_VARIATIONS:
        center = (image.shape[1] // 2, image.shape[0] // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, matrix, (image.shape[1], image.shape[0]))
        augmented_images.append(rotated)
    return augmented_images


while True:  # วนลูปจนกว่าจะได้ภาพครบตามที่กำหนด
    success, image_frame = vid_cam.read()  # อ่านเฟรมจากกล้อง
    if not success:  # หากไม่สามารถอ่านเฟรมได้
        print("Failed to capture frame. Retrying...")  # แจ้งเตือนว่าเฟรมล้มเหลวและลองใหม่
        continue  # ข้ามไปยังการอ่านเฟรมถัดไป

    # แปลงภาพจาก BGR เป็นภาพระดับสีเทา
    gray = cv2.cvtColor(image_frame, cv2.COLOR_BGR2GRAY)
    # ปรับปรุง histogram ของภาพเทาให้มีการกระจายแสงที่สมดุลมากขึ้น
    gray = cv2.equalizeHist(gray)

    # ตรวจจับใบหน้าโดยใช้ dlib
    faces = face_detector(gray, 1)  # 1 เป็นพารามิเตอร์เพิ่มความละเอียดเพื่อความแม่นยำ

    for face in faces:  # วนลูปตรวจสอบใบหน้าที่ตรวจจับได้
        # ดึงตำแหน่งและขนาดของกรอบใบหน้าที่ตรวจพบ
        x, y, w, h = (face.left(), face.top(), face.width(), face.height())
        # เพิ่ม padding รอบกรอบใบหน้าเพื่อขยายขอบเขต
        x_pad = max(x - PADDING, 0)  # ไม่ให้ค่าติดลบ
        y_pad = max(y - PADDING, 0)
        w_pad = min(w + 2 * PADDING, gray.shape[1] - x_pad)  # ไม่ให้เกินขนาดภาพ
        h_pad = min(h + 2 * PADDING, gray.shape[0] - y_pad)

        # ครอปเฉพาะส่วนใบหน้าจากภาพระดับสีเทา
        cropped_face = gray[y_pad:y_pad + h_pad, x_pad:x_pad + w_pad]
        # ปรับขนาดใบหน้าให้เป็น 150x150 พิกเซล
        normalized_face = cv2.resize(cropped_face, (150, 150))

        # สร้างภาพเพิ่มเติมจากใบหน้าที่ถูกครอป
        for augmented_face in augment_image(normalized_face):
            # สร้างเส้นทางไฟล์เพื่อบันทึกภาพ
            image_path = os.path.join(SAVE_DIR, f"Person.{FACE_ID}.{count + 1}.jpg")
            cv2.imwrite(image_path, augmented_face)  # บันทึกภาพ
            count += 1  # เพิ่มตัวนับภาพที่บันทึกสำเร็จ
            print(f"Captured image {count}/{IMAGE_COUNT_LIMIT}")  # แสดงสถานะการบันทึกภาพ
            if count >= IMAGE_COUNT_LIMIT:  # หากเก็บภาพครบตามที่กำหนดแล้ว
                break  # ออกจากลูป

        # วาดกรอบรอบใบหน้าที่ตรวจจับได้ในเฟรม
        cv2.rectangle(image_frame, (x_pad, y_pad), (x_pad + w_pad, y_pad + h_pad), (255, 0, 0), 2)

    # แสดงผลเฟรมในหน้าต่างที่ชื่อว่า 'Face Capture'
    cv2.imshow('Face Capture', image_frame)

    # ตรวจสอบว่ากดปุ่ม 'q' หรือบันทึกภาพครบตามที่กำหนดหรือไม่
    if cv2.waitKey(100) & 0xFF == ord('q') or count >= IMAGE_COUNT_LIMIT:
        break  # ออกจากลูปหลัก

    time.sleep(0.1)  # หน่วงเวลาเล็กน้อยเพื่อให้กล้องมีเวลาจับภาพถัดไป

# ปล่อยกล้องและปิดหน้าต่างการแสดงผล
vid_cam.release()
cv2.destroyAllWindows()

# แสดงข้อความยืนยันการบันทึกภาพเสร็จสิ้น
print(f"Image capture completed. {count} images saved in {SAVE_DIR}.")