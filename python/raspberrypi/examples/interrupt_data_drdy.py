# -*- coding: utf-8 -*
'''!
  @file  interrupt_data_drdy.py
  @brief  Get the sensor data through interrupt
  @details  Configure the sensor interrupt mode, interrupt occurs when a new data is uploaded into the sensor
  @copyright  Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
  @license  The MIT License (MIT)
  @author  [qsjhyy](yihuan.huang@dfrobot.com)
  @version  V1.0
  @date  2021-10-28
  @url  https://github.com/DFRobot/DFRobot_ENS160
'''
from __future__ import print_function
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from DFRobot_ENS160 import *

'''
  # Select communication interface I2C, please comment out SPI interface. And vise versa.
  # I2C : For Fermion version, I2C communication address setting: 
  #         connect SDO pin to GND, I2C address is 0×52 now;
  #         connect SDO pin to VCC(3v3), I2C address is 0x53 now
  # SPI : Set up digital pin according to the on-board pin connected with SPI chip-select pin.
'''
sensor = DFRobot_ENS160_I2C(i2c_addr = 0x53, bus = 1)
# sensor = DFRobot_ENS160_SPI(cs=8, bus=0, dev=0, speed=2000000)


global flag
flag = 0

def int_callback(channel):
  global flag
  flag = 1

# Use GPIO port to monitor sensor interrupt
gpio_int = 27
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(gpio_int, GPIO.IN)
GPIO.add_event_detect(gpio_int, GPIO.RISING, callback=int_callback)


def setup():
  while (sensor.begin() == False):
    print ('Please check that the device is properly connected')
    time.sleep(3)
  print("sensor begin successfully!!!")

  '''
    # Interrupt config (INT)
    # mode Interrupt mode to be set, perform OR operation on the following to get mode:
    #   Interrupt setting (the interrupt occur when a new data is uploaded): e_INT_mode_DIS-disable interrupt, e_INT_mode_EN-enable interrupt
    #   Interrupt pin output driving mode: e_INT_pin_OD-Open drain output, e_INT_pin_PP-Push pull output
    #   Interrupt pin active level: e_INT_pin_active_low-Active low, e_INT_pin_active_high-Active high
  '''
  sensor.set_INT_mode(sensor.e_INT_mode_EN | 
                      sensor.e_INT_pin_PP | 
                      sensor.e_INT_pin_active_high)


def loop():
  global flag
  if(flag == 1):
    flag = 0
    '''
      # Get the air quality index calculated on the basis of UBA
      # Return value: 1-Excellent, 2-Good, 3-Moderate, 4-Poor, 5-Unhealthy
    '''
    print("Air quality index : %u" %(sensor.get_AQI))

    '''
      # Get TVOC concentration
      # Return value range: 0–65000, unit: ppb
    '''
    print("Concentration of total volatile organic compounds : %u ppb" %(sensor.get_TVOC_ppb))

    '''
      # Get CO2 equivalent concentration calculated according to the detected data of VOCs and hydrogen (eCO2 – Equivalent CO2)
      # Return value range: 400–65000, unit: ppm
      # Five levels: Excellent(400 - 600), Good(600 - 800), Moderate(800 - 1000), 
      #               Poor(1000 - 1500), Unhealthy(> 1500)
    '''
    print("Carbon dioxide equivalent concentration : %u ppm" %(sensor.get_ECO2_ppm))

    print()
    time.sleep(0.5)


if __name__ == "__main__":
  setup()
  while True:
    loop()
