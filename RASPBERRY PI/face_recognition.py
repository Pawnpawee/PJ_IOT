import cv2
import dlib
import numpy as np
import os
import time
import paho.mqtt.client as mqtt

# ฟังก์ชันสำหรับตรวจสอบว่ามีโฟลเดอร์หรือไม่ ถ้าไม่มีจะสร้างขึ้นมา
def assure_path_exists(path):
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)

# โหลด face detector ของ dlib และตัวจดจำใบหน้าด้วย LBPHFaceRecognizer
face_detector = dlib.get_frontal_face_detector()
recognizer = cv2.face.LBPHFaceRecognizer_create()
assure_path_exists("saved_model/")  # ตรวจสอบโฟลเดอร์ของโมเดลที่บันทึก
recognizer.read('saved_model/s_model.yml')  # โหลดโมเดลที่บันทึกไว้

# กำหนดรูปแบบฟอนต์สำหรับแสดงชื่อ
font = cv2.FONT_HERSHEY_SIMPLEX

# เริ่มต้นการจับภาพจากกล้องเว็บแคม
cam = cv2.VideoCapture(0, cv2.CAP_V4L2)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # กำหนดความกว้างของเฟรม
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)  # กำหนดความสูงของเฟรม

# กำหนดเกณฑ์ความมั่นใจสำหรับการตรวจจับ
CONFIDENCE_THRESHOLD = 90  # ยิ่งมากยิ่งหละหลวม เช่น 100 ก็จะเกิดข้อผิดพลาดได้ เช่นตรวจ ID2 เป็น ID1 แทน 

# การตั้งค่า MQTT
MQTT_BROKER = "192.168.43.182"  # IP ของ MQTT Broker
MQTT_PORT = 1883
MQTT_TOPIC_ALERT = "alert/thief"  # หัวข้อสำหรับส่งข้อความเตือน

# สร้าง client ของ MQTT
mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

# ตัวแปรสำหรับติดตามเวลาที่ตรวจพบใบหน้าที่ไม่รู้จัก
unknown_start_time = None
unknown_detected = False

# ฟังก์ชันสำหรับวาดกรอบและแสดงชื่อบนใบหน้า
def draw_rectangle_and_label(im, face, name, color):
    x, y, w, h = (face.left(), face.top(), face.width(), face.height())
    cv2.rectangle(im, (x, y), (x + w, y + h), color, 2)  # วาดกรอบ
    cv2.putText(im, name, (x, y - 10), font, 0.75, (255, 255, 255), 2)  # แสดงชื่อ

while True:
    ret, im = cam.read()  # อ่านเฟรมจากกล้อง
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)  # แปลงภาพเป็นขาวดำ
    gray = cv2.equalizeHist(gray)  # ปรับ histogram ให้ภาพมีความสว่างสมดุล

    faces = face_detector(gray)  # ตรวจจับใบหน้า
    unknown_detected_this_frame = False

    for face in faces:
        x, y, w, h = (face.left(), face.top(), face.width(), face.height())

        # ตัดส่วนของใบหน้าให้อยู่ในขอบเขตภาพ
        x = max(0, x)
        y = max(0, y)
        w = min(w, gray.shape[1] - x)
        h = min(h, gray.shape[0] - y)

        if w > 0 and h > 0:  # ตรวจสอบว่าขนาดใบหน้ามีค่า valid
            face_region = gray[y:y + h, x:x + w]
            face_region = cv2.resize(face_region, (150, 150))  # ปรับขนาดใบหน้าให้เท่ากัน

            Id, confidence = recognizer.predict(face_region)  # คาดเดาใบหน้าว่าใช่คนใน ID ไหม

            if confidence <= CONFIDENCE_THRESHOLD:
                if Id in [1, 2, 3, 4]:  # ตรวจสอบว่า ID อยู่ในกลุ่มที่รู้จัก
                    name = ["Atom", "New", "Tonpai", "Kukkai"][Id - 1]
                    color = (0, 255, 0)  # กำหนดสีกรอบเป็นเขียวสำหรับคนรู้จัก
                    unknown_start_time = None
                else:
                    name = "Unknown"
                    color = (0, 0, 255)  # กำหนดสีกรอบเป็นแดงสำหรับคนไม่รู้จัก
                    unknown_detected_this_frame = True
                    if unknown_start_time is None:
                        unknown_start_time = time.time()
            else:
                name = "Unknown"
                color = (0, 0, 255)  # กำหนดสีกรอบเป็นแดงสำหรับคนไม่รู้จัก
                unknown_detected_this_frame = True
                if unknown_start_time is None:
                    unknown_start_time = time.time()

            draw_rectangle_and_label(im, face, name, color)  # วาดกรอบและแสดงชื่อ

            # ถ้าใบหน้าที่ไม่รู้จักถูกตรวจจับเกิน 3 วินาที ให้ส่งข้อความเตือน
            if unknown_start_time is not None and time.time() - unknown_start_time >= 3:
                mqtt_client.publish(MQTT_TOPIC_ALERT, "Activate")  # ส่งข้อความเตือน และข้อความนั้นจะทำให้ buzzer กับ Servo ทำงาน
                unknown_start_time = None

    # ถ้าไม่มีใบหน้าที่ไม่รู้จักในเฟรมนี้
    if not unknown_detected_this_frame and unknown_start_time is not None:
        mqtt_client.publish(MQTT_TOPIC_ALERT, "Deactivate")  # ยกเลิกการเตือน
        unknown_start_time = None

    cv2.imshow('Face Recognition', im)  # แสดงภาพพร้อมผลลัพธ์

    if cv2.waitKey(10) & 0xFF == ord('q'):  # กด 'q' เพื่อออกจากโปรแกรม
        break

cam.release()  # ปิดการใช้งานกล้อง
mqtt_client.disconnect()  # ตัดการเชื่อมต่อ MQTT
cv2.destroyAllWindows()  # ปิดหน้าต่างแสดงผล