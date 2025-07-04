#include <Adafruit_ICM20948.h>
#include <Adafruit_ICM20X.h>
#include <math.h>
#include <ArduinoJson.h>
#include <SimpleKalmanFilter.h>


// Pin Assignments
#define BMS_thermistor_pin 0  // ADC Pin
#define BMS_voltage_pin 1  // Voltage Reference Pin
#define BMS_current_pin 3  // Current Sensor Pin

// IMU Initialisation
Adafruit_ICM20948 icm;
Adafruit_Sensor *icm_temp, *icm_accel, *icm_gyro, *icm_mag;


// ADCS Boolean Logic
bool calibrated = false;
bool imu_found = false;

// EPS Constants
const float series_thermistor_resistor = 10000.0; // 22kΩ Change for thermistor series resistance
const float nominal_thermistor_resistance = 10000.0; // Resistance at 25°C
const float nominal_temp = 25.0; // In Celsius
const float b_coefficient = 3950.0; // 3950NTC gradient datasheet
const float thermistor_voltage_input = 3.3;
const float current_sensor_coefficient = 1 / 0.066; // ACS712 30A datasheet https://www.az-delivery.uk/products/acs712-stromsensor-mit-30a
const float adc_scaler = 9.7 / 4095.0; // max voltage / 2^(adc bits)

// JSON Vars
StaticJsonDocument<256> doc; // JSON doc

//// Generic Functions ////

float to_degrees(float radians) {
  return radians * 180 / M_PI;
}

float to_radians(float degrees) {
  return degrees * M_PI / 180;
}

void serial_msg(String msg) {
  Serial.println(msg);
  Serial1.println(msg);
}

//// Generic Functions END ////

//// Kalman Filter - Optional ////

struct KalmanFilter {
  float x; // estimate
  float p; // error
  float q; // process noise
  float r; // measurement noise

  void init( float estimate, float error, float process_noise, float measurement_noise ) {
    x = estimate;
    p = error;
    q = process_noise;
    r = measurement_noise;
  }

  void adc_init( int pin ) {
    float initialSum = 0;
    for (int i = 0; i < 20; i++) {
      initialSum += analogRead(pin);
      delay(5);
    }
    x = initialSum / 20;
  }

 float update(float measurement) {
    // Predict
    float P_pred =  p + q;
    // Kalman Gain
    float k = P_pred / (P_pred + r);
    // Update estimate
    x = x + k * (measurement - x);
    // Update covariance
    p = (1 - k) * P_pred;
    Serial.println(k);
    return x;
  }
};

//// Kalman Filter END ////

//// Data Accumilation ////

float accel_x, accel_y, accel_z;
float gyro_x, gyro_y, gyro_z;
float bms_current, bms_voltage, bms_temp;

float gyro_z_offset;

float yaw;

void get_data(int n) {
  // Reset all values to 0;
  accel_x = 0;
  accel_y = 0;
  accel_z = 0;
  gyro_x = 0;
  gyro_y = 0;
  gyro_z = 0;
  bms_current = 0;
  bms_voltage = 0;
  bms_temp = 0;

  // setting (i < 20) and delay(5) keeps response time to 0.1s
  for (int i = 0; i < n; i++) {
    if (imu_found) {
      sensors_event_t accel, gyro, mag;
      icm_accel->getEvent(&accel);
      icm_gyro->getEvent(&gyro);
      icm_mag->getEvent(&mag);

      accel_x += accel.acceleration.x;
      accel_y += accel.acceleration.y;
      accel_z += accel.acceleration.z;

      gyro_x += gyro.gyro.x;
      gyro_y += gyro.gyro.y;
      gyro_z += gyro.gyro.z;
    }

    bms_current += analogRead(BMS_current_pin);
    bms_voltage += analogRead(BMS_voltage_pin);
    bms_temp += analogRead(BMS_thermistor_pin);

    delay(1);
  }
  // Resolves average
  accel_x /= n;
  accel_y /= n;
  accel_z /= n;
  gyro_x /= n;
  gyro_y /= n;
  gyro_z /= n;
  bms_current /= n;
  bms_voltage /= n;
  bms_temp /= n;
}
//// Data Accumilation END ////

//// Process Raw Data ////

void process_eps_data() {
  // using this will convert raw adc average data into readings
  bms_current = abs(bms_current * adc_scaler - 2.5) * current_sensor_coefficient;
  if (bms_voltage >= 200) {
    bms_voltage *= adc_scaler*3.2; // potential divider ratio
  }
  else {
    bms_voltage = 0;
  }
  bms_temp *= adc_scaler; // edit later for emission formula
  // Calculate thermistor resistance using voltage divider formula
  float resistance = (bms_temp * series_thermistor_resistor) / (3.3 - bms_temp);

  // Apply the B-parameter equation to get temperature in Kelvin
  float steinhart;
  steinhart = resistance / nominal_thermistor_resistance;          // (R/R₀)
  steinhart = log(steinhart);                          // ln(R/R₀)
  steinhart /= b_coefficient;                           // 1/B * ln(R/R₀)
  steinhart += 1.0 / (nominal_temp + 283.15);    // + (1/T₀)
  steinhart = 1.0 / steinhart;                         // Invert
  bms_temp = steinhart - 273.15;             // Convert to °C

}

// ADCS Measurement Vars - just kept the adcs vars close to the calibration and process funcs
// Boolean logic moved to top

void calibrate() {
  // Mostly the same code as before
  serial_msg("Starting calibration... DONT rotate the sensor!");
  delay(500);
  // Added the get_data function for more stable readings
  yaw = 0;
  get_data(1000);
  gyro_z_offset = gyro_z;

  calibrated = true;
  serial_msg("\nCalibration complete!");
}

void zero() {
  yaw = 0;
  serial_msg("\nZero-ed!");
}

// Create a Kalman filter instance for gyro_x
// Arguments: (processNoise, measurementNoise, estimatedError)
//SimpleKalmanFilter kalmanGyroX(0.01, 0.1, 0.01);

unsigned long previous_time = 0;

void process_adcs_data() {
  if (imu_found == true){
    JsonArray gyroscope = doc.createNestedArray("gyroscope");
    JsonArray orientation = doc.createNestedArray("orientation");
    //JsonArray accelerometer = doc.createNestedArray("accelerometer");

    unsigned long current_time = millis();
    unsigned long dt = current_time - previous_time;
    previous_time = current_time;
    get_data(10);

    gyro_z -= gyro_z_offset;

    //float filtered_gyro_x = kalmanGyroX.updateEstimate(gyro_x);
    float position_change = to_degrees(gyro_z * dt / 1000);

    yaw += position_change;

    // Normalize accelerometer
    float norm = sqrt(accel_x * accel_x + accel_y * accel_y + accel_z * accel_z);
    float ax = accel_x / norm;
    float ay = accel_y / norm;
    float az = accel_z / norm;

    // Normalize to [-180, 180]
    if (yaw < -180.0) {
      yaw += 360.0;
    }
    if (yaw > 180.0) {
      yaw -= 360.0;
    }

    // Pitch and roll
    float pitch = atan2(-accel_x, sqrt(accel_y * accel_y + accel_z * accel_z)) * 180.0 / M_PI;
    float roll = atan2(accel_y, accel_z) * 180.0 / M_PI;

    gyroscope.add(gyro_z);

    orientation.add(yaw); //totalYaw

  }
}

//// Process Raw Data END ////

void setup() {

  // Telemetry
  Serial.begin(9600);
  Serial1.begin(9600, SERIAL_8N1, 20, 21);

  Wire.begin(5, 4);  // SDA=5, SCL=4

  // Initialise ADCs
  analogReadResolution(12); // Set ADC resolution to 12 bits
  analogSetPinAttenuation(BMS_voltage_pin, ADC_11db);  // ~0–3.3 V
  analogSetPinAttenuation(BMS_current_pin, ADC_11db);
  analogSetPinAttenuation(BMS_thermistor_pin, ADC_11db);

  pinMode(BMS_thermistor_pin, INPUT);
  pinMode(BMS_voltage_pin, INPUT);
  pinMode(BMS_current_pin, INPUT);

  // Initialise IMU
  if (!icm.begin_I2C()) {
    serial_msg("Failed to find ICM20948!");
    imu_found = false;
  }
  else {
    imu_found = true;
  }

  if (imu_found == true){
    icm_temp = icm.getTemperatureSensor();
    icm_accel = icm.getAccelerometerSensor();
    icm_gyro = icm.getGyroSensor();
    icm_mag = icm.getMagnetometerSensor();
  }
}


void loop() {
  // Check for calibration commands
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (imu_found == true) {
      if (cmd.equalsIgnoreCase("CALIBRATE")) {
        calibrate();
      } else if(cmd.equalsIgnoreCase("ZERO")) {
        zero();
      }
    }
  }
  if (Serial1.available()) {
    String cmd = Serial1.readStringUntil('\n');
    cmd.trim();
    if (imu_found == true) {
      if (cmd.equalsIgnoreCase("CALIBRATE")) {
        calibrate();
      } else if(cmd.equalsIgnoreCase("ZERO")) {
        zero();
      }
    }
  }
  // Clear the JSON document for new data
  doc.clear();

  // Process IMU Data
  process_adcs_data();

  // process EPS Data
  process_eps_data();

  // JSON Shenanigans
  doc["bms_voltage"] = bms_voltage;
  doc["bms_current"] = bms_current;
  doc["bms_temp"] = bms_temp;

  // Serialize the JSON document directly to Serial1
  // This is the most efficient way as it avoids creating an intermediate String object.
  size_t bytesSentSerial1 = serializeJson(doc, Serial1);
  size_t bytesSentSerial = serializeJson(doc, Serial);

  Serial1.println(","); // Add a newline after the JSON object for better readability in a terminal
  Serial.println();

  delay(10);
}
