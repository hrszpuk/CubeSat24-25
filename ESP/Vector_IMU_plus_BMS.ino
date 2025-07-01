#include <Adafruit_ICM20948.h>
#include <Adafruit_ICM20X.h>
#include <math.h>
#include <ArduinoJson.h>

// IMU
Adafruit_ICM20948 icm;
Adafruit_Sensor *icm_temp, *icm_accel, *icm_gyro, *icm_mag;

// Magnetic declination in degrees
const float DECLINATION_ANGLE = 0.92;

// Calibration
bool calibrated = false;
const int CALIBRATION_SAMPLES = 300;
float magXmin, magXmax, magYmin, magYmax, magZmin, magZmax;
float magXoffset = 0, magYoffset = 0, magZoffset = 0;
float magXscale = 1.0, magYscale = 1.0, magZscale = 1.0;

// Yaw accumulation
float totalYaw = 0;    // Total yaw in degrees (including full turns)
float prevYaw = 0;     // Previous yaw in degrees (-180 to 180)
int turnCount = 0;     // Full rotations (+CW, -CCW)

bool imu_found = false;


// BMS
#define BMS_thermistor_pin 3  // ADC Pin
#define BMS_voltage_pin 0  // Voltage Reference Pin
#define BMS_current_pin 1  // Current Sensor Pin

const float series_thermistor_resistor = 10000.0; // 22kΩ Change for thermistor series resistance
const float nominal_thermistor_resistance = 10000.0; // Resistance at 25°C
const float nominal_temp = 25.0; // In Celsius
const float b_coefficient = 3950.0; // 3950NTC gradient datasheet
const float thermistor_voltage_input = 3.3;

const float current_sensor_coefficient = 1 / 0.066; // ACS712 30A datasheet https://www.az-delivery.uk/products/acs712-stromsensor-mit-30a

const float adc_scaler = 3.3 / 4095.0; // max voltage / 2^(adc bits)

float get_bms_temp() {

  int adc_value = analogReadMilliVolts(BMS_thermistor_pin);
  float voltage = adc_value * adc_scaler;

  float resistance = series_thermistor_resistor * (voltage /(thermistor_voltage_input - voltage)); // taking ADC at x: vcc--resistor--x--thermistor--gnd
  float temp_kelvin = 1.0 / (1.0 / (nominal_temp + 273.15) + log(resistance / nominal_thermistor_resistance) / b_coefficient);
  float temp_celsius = temp_kelvin - 273.15;

  return temp_celsius;
};

float get_bms_voltage() {

  int adc_value = analogReadMilliVolts(BMS_voltage_pin); // can be floating and settle around 1-1.25V when ungrounded, make sure there is a stable ground source here
  float voltage = adc_value * adc_scaler;

  float battery_voltage = voltage * 3.2 ; // using the midpoint of an identical resistance potential divider to step down voltage to readable range

  return battery_voltage;
};


float get_bms_current() { // using theoretical calcs with ACS712 current sensor
  int adc_value = analogReadMilliVolts(BMS_current_pin);
  float voltage = adc_value * adc_scaler;

  float battery_current = voltage * current_sensor_coefficient; // 1 / coefficient

  return battery_current;
};

void calibrateMagnetometer() {
  Serial.println("Starting calibration... Rotate the sensor!");
  Serial1.println("Starting calibration... Rotate the sensor!");
  delay(2000);

  sensors_event_t mag;
  icm_mag->getEvent(&mag);
  magXmin = magXmax = mag.magnetic.x;
  magYmin = magYmax = mag.magnetic.y;
  magZmin = magZmax = mag.magnetic.z;

  for (int i = 0; i < CALIBRATION_SAMPLES; i++) {
    icm_mag->getEvent(&mag);
    magXmin = min(magXmin, mag.magnetic.x);
    magXmax = max(magXmax, mag.magnetic.x);
    magYmin = min(magYmin, mag.magnetic.y);
    magYmax = max(magYmax, mag.magnetic.y);
    magZmin = min(magZmin, mag.magnetic.z);
    magZmax = max(magZmax, mag.magnetic.z);
    if (i % 50 == 0) Serial.print(i/5 + "%");
    delay(50);
  }

  // Calculate offsets & scale factors
  magXoffset = (magXmin + magXmax) / 2;
  magYoffset = (magYmin + magYmax) / 2;
  magZoffset = (magZmin + magZmax) / 2;

  float avgRange = ((magXmax - magXmin) + (magYmax - magYmin) + (magZmax - magZmin)) / 3;
  magXscale = avgRange / (magXmax - magXmin);
  magYscale = avgRange / (magYmax - magYmin);
  magZscale = avgRange / (magZmax - magZmin);

  calibrated = true;
  Serial.println("\nCalibration complete!");
  Serial1.println("\nCalibration complete!");
}

void updateYaw(float currentYaw) {
  if (currentYaw - prevYaw > 180.0) turnCount--;      // Crossed -180 → +180 (CCW)
  else if (currentYaw - prevYaw < -180.0) turnCount++; // Crossed +180 → -180 (CW)
  prevYaw = currentYaw;
  totalYaw = currentYaw + turnCount * 360.0;          // Accumulated yaw
}

float roundToTwoDecimalPlaces(float value) {
  return round(value * 100.0) / 100.0;
}

void setup() {
  analogReadResolution(12); // Set ADC resolution to 12 bits
  pinMode(BMS_thermistor_pin, INPUT);
  pinMode(BMS_voltage_pin, INPUT);
  pinMode(BMS_current_pin, INPUT);
  
  Serial.begin(9600);
  Serial1.begin(9600, SERIAL_8N1, 20, 21);

  Wire.begin(5, 4);  // SDA=5, SCL=4

  if (!icm.begin_I2C()) {
    Serial.println("Failed to find ICM20948!");
    Serial1.println("Failed to find ICM20948!");
    imu_found = false;
  }
  else 
  {
    imu_found = true;
  }

  if (imu_found == true){
    icm_temp = icm.getTemperatureSensor();
    icm_accel = icm.getAccelerometerSensor();
    icm_gyro = icm.getGyroSensor();
    icm_mag = icm.getMagnetometerSensor();
  }
}

StaticJsonDocument<256> doc; // JSON doc

void loop() {
  // Check for calibration commands
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.equalsIgnoreCase("CALIBRATE") && imu_found == true) calibrateMagnetometer();
  }
  if (Serial1.available()) {
    String cmd = Serial1.readStringUntil('\n');
    cmd.trim();
    if (cmd.equalsIgnoreCase("CALIBRATE") && imu_found == true) calibrateMagnetometer();
  }

  // Clear the JSON document for new data
  doc.clear();

  // Populate the JSON document
  JsonArray gyroscope = doc.createNestedArray("gyroscope");
  JsonArray orientation = doc.createNestedArray("orientation");

  if (imu_found == true){
    sensors_event_t accel, gyro, mag;
    icm_accel->getEvent(&accel);
    icm_gyro->getEvent(&gyro);
    icm_mag->getEvent(&mag);

    // Apply calibration
    float magX = (mag.magnetic.x - magXoffset) * magXscale;
    float magY = (mag.magnetic.y - magYoffset) * magYscale;

    // Calculate orientation
    float currentYaw = atan2(magY, magX) * 180.0 / PI + DECLINATION_ANGLE;
    updateYaw(currentYaw);
    float pitch = atan2(-accel.acceleration.x, 
                      sqrt(accel.acceleration.y * accel.acceleration.y + 
                            accel.acceleration.z * accel.acceleration.z)) * 180.0 / PI;
    float roll = atan2(accel.acceleration.y, accel.acceleration.z) * 180.0 / PI;

    gyroscope.add(roundToTwoDecimalPlaces(gyro.gyro.x));
    gyroscope.add(roundToTwoDecimalPlaces(gyro.gyro.y));
    gyroscope.add(roundToTwoDecimalPlaces(gyro.gyro.z));

    orientation.add(roundToTwoDecimalPlaces(totalYaw));
    orientation.add(roundToTwoDecimalPlaces(pitch));
    orientation.add(roundToTwoDecimalPlaces(roll));
  }

  float bms_temp = get_bms_temp();
  float bms_voltage = get_bms_voltage();
  float bms_current = get_bms_current();

  doc["bms_voltage"] = get_bms_voltage();
  doc["bms_current"] = get_bms_current();
  doc["bms_temp"] = get_bms_temp();

  // Serialize the JSON document directly to Serial1
  // This is the most efficient way as it avoids creating an intermediate String object.
  size_t bytesSentSerial1 = serializeJson(doc, Serial1);
  size_t bytesSentSerial = serializeJson(doc, Serial);

  Serial1.println(); // Add a newline after the JSON object for better readability in a terminal
  Serial.println();

  delay(100);  // Adjust based on your needs
}
