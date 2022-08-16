# DFRobot_ENS160
* [中文版](./README_CN.md)

The ENS160 is a digital multi-gas sensor solution, based on metal oxide (MOX) technology 
with four MOX sensor elements. Each sensor element has independent hotplate control to 
detect a wide range of gases e.g. volatile organic compounds (VOCs) including ethanol, 
toluene, as well as hydrogen and nitrogen dioxide with superior selectivity and accuracy.
For indoor air quality applications, the ENS160 supports intelligent algorithms to digitally 
process raw sensor measurements on-chip. These algorithms calculate CO2-equivalents, 
TVOC, air quality indices (AQIs) and perform humidity and temperature compensation, as 
well as baseline management – all on chip! Moreover, a development option is available 
to digitally output raw sensor measurements from each sensor element for customization. 
The LGA-packaged device includes an SPI or I²C slave interface with separate VDDIO to 
communicate with a main host processor. The ENS160 is a proven and maintenance-free 
technology, designed for high volume and reliability.

![产品实物图](../../resources/images/ENS160.png)


## Product Link (https://www.dfrobot.com/search-ens160.html)
    SKU: SEN0514/SEN0515


## Table of Contents

* [Summary](#summary)
* [Installation](#installation)
* [Methods](#methods)
* [Compatibility](#compatibility)
* [History](#history)
* [Credits](#credits)


## Summary

* TrueVOC™ air quality detection with industry-leading purity and stability, providing multiple outputs e.g. eCO21, TVOC and AQIs2in compliance with worldwide IAQ3-signal standards
* Independent sensor heater control for highest selectivity (e.g. to ethanol, toluene, acetone, NO2) and outstanding background discrimination
* Immunity to siloxanes and humidity
* Hassle-free on-chip heater drive control and data processing – no need for external libraries – no mainboard-CPU performance impacts
* Interrupt on threshold for low-power applications
* Wide operating ranges: temperature: -40 to +85°C; humidity: 5 to 95%5; VDD: 1.71 to 1.98V; VDDIO 1.71 to 3.6V
* The library supports the SPI/I2C communication.


## Installation

To use the library, first download the library file, paste it into the directory you specified, then open the Examples folder and run the demo in that folder.


## Methods

```python

    '''!
      @brief Initialize sensor
      @return  Return init status
      @retval True indicate initialization succeed
      @retval False indicate initialization failed
    '''
    def begin(self):

    '''!
      @brief Configure power mode
      @param mode Configurable power mode:
      @n       ENS160_SLEEP_MODE: DEEP SLEEP mode (low power standby)
      @n       ENS160_IDLE_MODE: IDLE mode (low-power)
      @n       ENS160_STANDARD_MODE: STANDARD Gas Sensing Modes
    '''
    def set_PWR_mode(self, mode):

    '''!
      @brief Interrupt config (INT)
      @param mode Interrupt mode to be set, perform OR operation on the following to get mode:
      @n       The interrupt occur when new data appear in DATA_XXX register (can get new measured data): e_INT_mode_DIS, disable interrupt; e_INT_mode_EN, enable interrupt
      @n       Interrupt pin output driving mode: e_INT_pin_OD, open drain; e_INT_pin_PP, push pull
      @n       Interrupt pin active level: e_INT_pin_active_low, active low; e_INT_pin_active_high, active high
    '''
    def set_INT_mode(self, mode):

    '''!
      @brief Users write ambient temperature and relative humidity into ENS160 for calibration and compensation of the measured gas data.
      @param ambient_temp Compensate the current ambient temperature, float type, unit: C
      @param relative_humidity Compensate the current ambient humidity, float type, unit: %rH
    '''
    def set_temp_and_hum(self, ambient_temp, relative_humidity):

    '''!
      @brief This API is used to get all the sensor status
      @return Status structure sensor_status, Whose members are:
      @n        status: High indicates that an OPMODE is running;
      @n        stater: High indicates that an error is detected;
      @n        validity_flag: 0: Normal operation, 1: Warm-Up phase, 
      @n                      2: Initial Start-Up phase, 3: Invalid output;
      @n        data_drdy: Measured data ready;
      @n        GPR_drdy: General purpose register data ready
    '''
    def get_ENS160_status(self):

    '''!
      @brief Get the air quality index calculated on the basis of UBA
      @return Return value range: 1-5 (Corresponding to five levels of Excellent, Good, Moderate, Poor and Unhealthy respectively)
    '''
    @property
    def get_AQI(self):

    '''!
      @brief Get TVOC concentration
      @return Return value range: 0–65000, unit: ppb
    '''
    @property
    def get_TVOC_ppb(self):

    '''!
      @brief Get CO2 equivalent concentration calculated according to the detected data of VOCs and hydrogen (eCO2 – Equivalent CO2)
      @return Return value range: 400–65000, unit: ppm
      @note Five levels: Excellent(400 - 600), Good(600 - 800), Moderate(800 - 1000), 
      @n                  Poor(1000 - 1500), Unhealthy(> 1500)
    '''
    @property
    def get_ECO2_ppm(self):

```


## Compatibility

* RaspberryPi Version

| Board        | Work Well | Work Wrong | Untested | Remarks |
| ------------ | :-------: | :--------: | :------: | ------- |
| RaspberryPi2 |           |            |    √     |         |
| RaspberryPi3 |           |            |    √     |         |
| RaspberryPi4 |     √     |            |          |         |

* Python Version

| Python  | Work Well | Work Wrong | Untested | Remarks |
| ------- | :-------: | :--------: | :------: | ------- |
| Python2 |     √     |            |          |         |
| Python3 |     √     |            |          |         |


## History

- 2021/10/28 - Version 1.0.0 released.
- 2022/04/20 - Version 1.0.1 released.


## Credits

Written by qsjhyy(yihuan.huang@dfrobot.com), 2021. (Welcome to our [website](https://www.dfrobot.com/))

