/*!
 * @file  interruptDataDrdy.ino
 * @brief  Get the sensor data through interrupt (Use 3.3V main controller for Fermion version; this example is only applicable to Fermion version)
 * @details  Configure the sensor interrupt mode, interrupt occurs when a new data is uploaded into the sensor
 * @copyright  Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
 * @license  The MIT License (MIT)
 * @author  [qsjhyy](yihuan.huang@dfrobot.com)
 * @version  V1.0
 * @date  2021-10-27
 * @url  https://github.com/DFRobot/DFRobot_ENS160
 */
#include <DFRobot_ENS160.h>

#define I2C_COMMUNICATION  //I2C communication. Comment out this line of code if you want to use SPI communication.

#ifdef  I2C_COMMUNICATION
  /**
   *   For Fermion version, the default I2C address is 0x53, connect SDO pin to GND and I2C address will be 0x52
   */
  DFRobot_ENS160_I2C ENS160(&Wire, /*I2CAddr*/ 0x53);
#else
  /**
   * Set up digital pin according to the on-board pin connected with SPI chip-select pin
   * csPin Available Pins. For example: ESP32&ESP8266(D3), m0(6)
   */
  uint8_t csPin = D3;
  DFRobot_ENS160_SPI ENS160(&SPI, csPin);
#endif

/* Interrupt flag */
volatile uint8_t flag = 0;
/* External interrupt flag */
void interrupt()
{
  flag = 1;
}

void setup(void)
{
  Serial.begin(115200);

  // Init the sensor
  while( NO_ERR != ENS160.begin() ){
    Serial.println("Communication with device failed, please check connection");
    delay(3000);
  }
  Serial.println("Begin ok!");

  #if defined(ESP32) || defined(ESP8266)
    // D4 pin is used as interrupt pin by default, other non-conflicting pins can also be selected as external interrupt pins.
    attachInterrupt(digitalPinToInterrupt(D4)/* Query the interrupt number of the D4 pin */, interrupt, RISING);
  #elif defined(ARDUINO_SAM_ZERO)
    // Pin 5 is used as interrupt pin by default, other non-conflicting pins can also be selected as external interrupt pins
    attachInterrupt(digitalPinToInterrupt(5)/* Query the interrupt number of the 5 pin */, interrupt, RISING);
  #endif

  /**
   * Interrupt config (INT)
   * mode Interrupt mode to be set, perform OR operation on the following to get mode:
   *   Interrupt setting (the interrupt occur when a new data is uploaded): eINTModeDIS-Disable interrupt, eINTModeEN-Enable interrupt
   *   Interrupt pin output driving mode: eINTPinOD-Open drain output, eINTPinPP-Push pull output
   *   Interrupt pin active level: eINTPinActiveLow-Active low, eINTPinActiveHigh-Active high
   */
  ENS160.setINTMode(ENS160.eINTModeEN | 
                    ENS160.eINTPinPP | 
                    ENS160.eINTPinActiveHigh);

  Serial.println();
  delay(1000);
}

void loop()
{
  if(flag == 1){
    flag = 0;
    /**
     * Get the air quality index
     * Return value: 1-Excellent, 2-Good, 3-Moderate, 4-Poor, 5-Unhealthy
     */
    uint8_t AQI = ENS160.getAQI();
    Serial.print("Air quality index : ");
    Serial.println(AQI);

    /**
     * Get TVOC concentration
     * Return value range: 0–65000, unit: ppb
     */
    uint16_t TVOC = ENS160.getTVOC();
    Serial.print("Concentration of total volatile organic compounds : ");
    Serial.print(TVOC);
    Serial.println(" ppb");

    /**
     * Get CO2 equivalent concentration calculated according to the detected data of VOCs and hydrogen (eCO2 – Equivalent CO2)
     * Return value range: 400–65000, unit: ppm
     * Five levels: Excellent(400 - 600), Good(600 - 800), Moderate(800 - 1000), 
     *               Poor(1000 - 1500), Unhealthy(> 1500)
     */
    uint16_t ECO2 = ENS160.getECO2();
    Serial.print("Carbon dioxide equivalent concentration : ");
    Serial.print(ECO2);
    Serial.println(" ppm\n");
  }
}
