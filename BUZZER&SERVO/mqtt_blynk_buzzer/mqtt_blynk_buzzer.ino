// ข้อมูลของ Blynk //
#define BLYNK_TEMPLATE_ID "TMPL6a_T5jX_o"
#define BLYNK_TEMPLATE_NAME "Quickstart Template"
#define BLYNK_AUTH_TOKEN "xTmmlPS70wji2pGx3Cy8XkgFPJeC4nyA"

// นำเข้า Library //
#include <PubSubClient.h> // Library สำหรับ MQTT //
#include <BlynkSimpleEsp8266.h>  // Library ของ Blynk สำหรับ ESP8266 //
#include <ESP8266WiFi.h> // Library Wifi สำหรับ ESP8266 //
#include <WiFiManager.h> // Library ของ WifiManager //

// ตั้ง PIN ของ Buzzer และ LED ประจำบอร์ด ESP8266 //
#define BUZZER_PIN D1
#define LED_PIN D2

// กำหนด Server ของ MQTT //
const char* mqtt_server = "192.168.43.182"; // ในที่นี้ใช้เป็น IP ของคอมอะตู่เอง สามารถเปลี่ยนไปเป็น IP ของคอมตัวเอง หรือ รายพายได้ // //(192.168.1.46)//

// สร้าง Object มาเก็บค่า Wifi และ MQTT เพื่อไปใช้ต่อไป //
WiFiClient espClient;
PubSubClient client(espClient);

// ตัวแปรประเภท bool สำหรับเปิด-ปิด buzzer และ LED //
bool buzzerActive = false;

void setup() {
  Serial.begin(115200);
  pinMode(BUZZER_PIN, OUTPUT); // ตั้งค่า BUZZER_PIN ให้เป็นประเภท Output จะได้ส่งเสียงกรีดร้องได้ //
  pinMode(LED_PIN, OUTPUT); // ตั้งค่า LED_PIN ให้เป็นประเภท Output จะได้เปิดไฟเทคได้ //
  WiFiManager wifiManager; // ประกาศตัวแปร wifiManager มาเป็นตัวแทนของ Library WiFiManager และนำไปใช้งานต่อไป //

  // ในตอนแรกจะไม่สามารถหา Wifi เจอ (ไม่มีบันทึกข้อมูลการเชื่อมต่อที่ (192.168.4.1) 
  // ให้เชื่อมต่อ Wifi "ESPBUZZER_AP" แล้วนำ IP ในวงเล็บไปพิมพ์ในบราวเซอร์ได้เลย 
  // เสร็จแล้วตั้งค่าใส่รหัสของ Wifi 2.4G ให้เรียบร้อย เพื่อให้บอร์ดจดจำค่าไว้ในการเชื่อมต่อครั้งถัดไป)
  if (!wifiManager.autoConnect("ESPBUZZER_AP")) {  // กรณีหา Wifi ในระบบไม่เจอจะสร้าง Access Point ขึ้นมาเอง (ใช้ Access Point ตัวนี้เชื่อมต่อให้เรียบร้อยแล้วเขาไปแก้ไขการเชื่อมต่อไวไฟได้ที่ (192.168.4.1) บนบราวเซอร์ )
    Serial.println("Failed to connect to Wi-Fi...");
    ESP.restart();
  } else {
    Serial.println("Connected to Wi-Fi");
  }

  Blynk.begin(BLYNK_AUTH_TOKEN, WiFi.SSID().c_str(), WiFi.psk().c_str()); // คำสั่งเริ่มใช้งาน Blynk //
  Serial.println("Connected to Blynk");

  Blynk.virtualWrite(V1, buzzerActive ? 1 : 0); // เชื่อมต่อสถานะของปุ่ม Switch ใน Blynk กับตัวแปร buzzerActive //
  Blynk.virtualWrite(V3, "No thief detected yet."); // ตั้งค่า String ของ Label ใน Blynk ให้เป็นค่าเริ่มต้นคือ "No thief detected yet" //

  // ตั้งค่า mqtt //
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

// ฟังก์ชันที่รับค่ามาจาก MQTT Broker แล้วนำมาแปลงค่า State ของ buzzerActive //
void callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println("Message Received: " + message);

  if (message == "Activate") { // ถ้าข้อความที่ Inject เข้ามาเป็น "Activate" จะเปลี่ยน buzzerActive เป็น TRUE //
    buzzerActive = true;
  } else if (message == "Deactivate") { // ถ้าข้อความที่ Inject เข้ามาเป็น "Deactivate" จะเปลี่ยน buzzerActive เป็น FALSE //
    buzzerActive = false;
    digitalWrite(LED_PIN, LOW); // ปิดไฟ //
    noTone(BUZZER_PIN);  // ปิดเสียง Buzzer //
  }
}

// ฟังก์ชันใน Blynk เพื่อทำให้ปุ่ม Switch ที่ใช้ Datastream V1 ควบคุม buzzerActive ได้ //
BLYNK_WRITE(V1) {
  int buttonState = param.asInt(); // รับค่า state ของ ปุ่ม switch ถ้า 1 คือ เปิด 0 คือ ปิด //

  if (buttonState == 1) { // ถ้าค่าที่ส่งมาเป็น 1 จะทำการลั่นเสียงกรีดร้องของ Buzzer //
    buzzerActive = true;  
  } else { // ถ้าค่าที่ส่งมาเป็น 0 จะทำการปิดเสียงของ Buzzer //
    buzzerActive = false; 
  }
}

void loop() {

  // รันกระบวนการทำงานของตัว Blynk //
  Blynk.run();
  // เงื่อนไขไว้เช็คว่ายังเชื่อมค่อกับ MQTT อยู่ไหม //
  if (!client.connected()) {
    while (!client.connect("ESP8266Client")) {
      delay(500);
    }
    client.subscribe("alert/thief");  // สับตะไคร้ไปยัง topic "alert/thief" //
  }
  client.loop();

  Blynk.virtualWrite(V1, buzzerActive ? 1 : 0); // เชื่อมปุ่มใน Blynk เข้ากับ buzzerActive ที่รับค่ามาจาก MQTT เข้าด้วยกัน ทำให้ปิดเปิดแบบล้ำๆได้ //

   if (buzzerActive) { // ถ้า buzzerActive เป็น TRUE // // ตัวนี้จะดำเนินการเป็นลูปจนกว่า State ของ buzzerActive จะเปลี่ยน //
    Blynk.logEvent("alert","Thief Detected!"); // แจ้งเตือนไปยัง Event ที่ชื่อ alert โดยข้อความคือ "Thief Detected" //
    Blynk.virtualWrite(V3, "Thief Detected!"); // เปลี่ยนข้อความใน Label บน dashboard ของ Blynk ให้เป็น "Thief Detected" //
    tone(BUZZER_PIN, 1500);  // เปิดใช้งานเสียงเพรียกหาแห่งความเวทนา //
    digitalWrite(LED_PIN, HIGH); // เปิดไฟเทคจาก Raise Up //
    delay(100); // ค้างไป 0.1 วินาที //
    noTone(BUZZER_PIN); // ปิดใช้งานเสียงเพรียกหาแห่งความเวทนา //
    digitalWrite(LED_PIN, LOW); // ปิดไฟเทคจาก Raise Up //
    delay(100); // ค้างไป 0.1 วินาที //
  }else{ // ถ้า buzzerActive เป็น False //
    Blynk.virtualWrite(V3, "No thief detected yet."); // เปลี่ยนข้อความใน Label บน dashboard ของ Blynk ให้เป็น "No thief detected yet." //
    noTone(BUZZER_PIN); // ปิดใช้งานเสียงเพรียกหาแห่งความเวทนา //
    digitalWrite(LED_PIN, LOW); // ปิดไฟเทคจาก Raise Up //
  }
}