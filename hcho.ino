#include <SensirionI2cSfa3x.h>

#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "WiFi SSID";
const char* password = "WiFi Password";


SensirionI2cSfa3x sfa3x;
const int16_t SFA_ADDRESS = 0x5D;

void setup() {

  Serial.begin(115200);
  while (!Serial) {
    delay(100);
  }


  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  // init I2C
  Wire.begin();

  // wait until sensor is ready
  delay(10);

  // start SFA measurement in periodic mode, will update every 0.5 s
  Wire.beginTransmission(SFA_ADDRESS);
  Wire.write(0x00);
  Wire.write(0x06);
  Wire.endTransmission();


  uint16_t error;
  char errorMessage[256];

  sfa3x.begin(Wire, SFA_ADDRESS);

  // Start Measurement
  error = sfa3x.startContinuousMeasurement();
  if (error) {
    Serial.print("Error trying to execute startContinuousMeasurement(): ");
    errorToString(error, errorMessage, 256);
    Serial.println(errorMessage);
  }


  // module is not outputing HCHO for the first 10 s after powering up
  delay(10000);
}

void loop() {
  float hcho, temperature, humidity;
  uint8_t data[9], counter;

  // send read data command
  Wire.beginTransmission(SFA_ADDRESS);
  Wire.write(0x03);
  Wire.write(0x27);
  Wire.endTransmission();

  //wait time before reading for the values should be more than 2ms
  delay(10);

  // read measurement data:
  // 2 bytes formaldehyde, 1 byte CRC, scale factor 5
  // 2 bytes RH, 1 byte CRC, scale factor 100
  // 2 bytes T, 1 byte CRC, scale factor 200
  // stop reading after 9 bytes (not used)
  Wire.requestFrom(SFA_ADDRESS, 9);
  counter = 0;
  while (Wire.available()) {
    data[counter++] = Wire.read();
  }

  // floating point conversion according to datasheet
  hcho = (float)((int16_t)data[0] << 8 | data[1]) / 5;
  // convert RH in %
  humidity = (float)((int16_t)data[3] << 8 | data[4]) / 100;
  // convert T in degC
  temperature = (float)((int16_t)data[6] << 8 | data[7]) / 200;

  String url = "{{HomeAssistant IP + Port + 接口地址}}";
  HTTPClient http;
  http.begin(url);
  http.addHeader("Content-Type", "application/json");  // 必须设置 JSON 头
  String requestBody = "{\"hcho\":" + String(hcho) + ",\"humidity\":" + String(humidity) + ",\"temperature\":" + String(temperature) + "}";

  int httpCode = http.POST(requestBody);  // 发送 POST 请求


  if (httpCode > 0) {
    String payload = http.getString();
    Serial.println(httpCode);
    Serial.println(payload);
  } else {
    Serial.println("Error on HTTP request");
  }

  http.end();
  delay(60000);
}