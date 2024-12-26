// ข้อมูลของ Blynk
#define BLYNK_TEMPLATE_ID "TMPL6a_T5jX_o"      // Template ID ของ Blynk
#define BLYNK_TEMPLATE_NAME "Quickstart Template" // ชื่อ Template ใน Blynk
#define BLYNK_AUTH_TOKEN "xTmmlPS70wji2pGx3Cy8XkgFPJeC4nyA" // Token สำหรับการเชื่อมต่อกับ Blynk

// นำเข้าไลบรารีที่จำเป็น
#include <ESP8266WiFi.h>          // ไลบรารีสำหรับการเชื่อมต่อ WiFi บน ESP8266
#include <BlynkSimpleEsp8266.h>   // ไลบรารี Blynk สำหรับ ESP8266
#include <Servo.h>                // ไลบรารีสำหรับควบคุมเซอร์โว
#include <PubSubClient.h>         // ไลบรารีสำหรับใช้งาน MQTT

Servo myservo; // สร้างออบเจ็กต์ Servo สำหรับควบคุมเซอร์โว

// ข้อมูลการเชื่อมต่อ WiFi
char ssid[] = "AndroidAP"; // ชื่อ WiFi ที่ต้องการเชื่อมต่อ
char pass[] = "hdkb3354";  // รหัสผ่าน WiFi

// ข้อมูลเซิร์ฟเวอร์ของ MQTT
const char* mqtt_server = "192.168.43.182"; // ที่อยู่ IP ของ MQTT Broker

// สร้างออบเจ็กต์สำหรับการเชื่อมต่อ WiFi และ MQTT
WiFiClient espClient;           // ออบเจ็กต์ WiFiClient
PubSubClient client(espClient); // ออบเจ็กต์ PubSubClient สำหรับใช้งาน MQTT

bool servoEnabled = false; // ตัวแปรสำหรับเก็บสถานะการทำงานของเซอร์โว (เปิด/ปิด)

// ฟังก์ชัน callback สำหรับรับข้อความจาก MQTT
void callback(char* topic, byte* payload, unsigned int length) {
  String message; // ตัวแปรสำหรับเก็บข้อความที่ได้รับ
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i]; // รวมข้อความจาก payload
  }
  Serial.println("Message Received: " + message); // แสดงข้อความที่ได้รับใน Serial Monitor

  // ตรวจสอบข้อความและควบคุมเซอร์โว
  if (message == "Activate") { 
    servoEnabled = true;
    myservo.write(50); // หมุนเซอร์โวไปที่ 50 องศา
    Serial.println("Servo: ON (50 degrees)"); // แสดงสถานะใน Serial Monitor
  } else if (message == "Deactivate") {
    servoEnabled = false;
    myservo.write(0); // หมุนเซอร์โวกลับไปที่ 0 องศา
    Serial.println("Servo: OFF (0 degrees)"); // แสดงสถานะใน Serial Monitor
  }
}

// ฟังก์ชันอ่านค่าจากแอป Blynk (Virtual Pin V2)
BLYNK_WRITE(V2) {
  int buttonState = param.asInt(); // อ่านค่าจากปุ่มในแอป Blynk
  if (buttonState == 1) { 
    servoEnabled = true;
    myservo.write(50); // หมุนเซอร์โวไปที่ 50 องศา
    Serial.println("Servo: ON (50 degrees)");
  } else {
    servoEnabled = false;
    myservo.write(0); // หมุนเซอร์โวกลับไปที่ 0 องศา
    Serial.println("Servo: OFF (0 degrees)");
  }
}

void setup() {
  Serial.begin(115200);  // เริ่มการสื่อสาร Serial สำหรับ Debug
  myservo.attach(D1);    // เชื่อมต่อเซอร์โวกับขา GPIO D1

  // ตั้งค่าการทำงานเริ่มต้นของเซอร์โว
  servoEnabled = false;  
  myservo.write(0); // ตั้งค่าเซอร์โวให้อยู่ที่ 0 องศา
  Serial.println("Servo: OFF (0 degrees)");

  // เริ่มการเชื่อมต่อ WiFi
  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) { // รอจนกว่าจะเชื่อมต่อ WiFi สำเร็จ
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to Wi-Fi"); // แสดงสถานะว่าเชื่อมต่อสำเร็จ

  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass); // เริ่มการเชื่อมต่อกับ Blynk
  Serial.println("Connected to Blynk");

  Blynk.virtualWrite(V2, 0); // ตั้งค่าเริ่มต้นของปุ่มในแอป Blynk

  client.setServer(mqtt_server, 1883); // ตั้งค่าเซิร์ฟเวอร์ของ MQTT
  client.setCallback(callback);       // กำหนดฟังก์ชัน callback สำหรับ MQTT
}

void reconnectMQTT() {
  while (!client.connected()) { // ตรวจสอบการเชื่อมต่อกับ MQTT Broker
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP8266Client_Servo")) { // พยายามเชื่อมต่อ
      Serial.println("connected");
      client.subscribe("alert/thief"); // สมัครสมาชิกกับ Topic "alert/thief"
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state()); // แสดงสถานะการเชื่อมต่อที่ล้มเหลว
      Serial.println(" try again in 5 seconds");
      delay(5000); // รอ 5 วินาทีเพื่อเชื่อมต่อใหม่
    }
  }
}

void loop() {
  if (!client.connected()) { // ตรวจสอบว่าการเชื่อมต่อ MQTT หลุดหรือไม่
    reconnectMQTT(); // ถ้าหลุดให้พยายามเชื่อมต่อใหม่
  }
  Blynk.virtualWrite(V2, servoEnabled ? 1 : 0); // อัพเดตสถานะของปุ่มในแอป Blynk
  client.loop(); // รันฟังก์ชัน loop ของ MQTT
  Blynk.run(); // รันฟังก์ชันของ Blynk
}
