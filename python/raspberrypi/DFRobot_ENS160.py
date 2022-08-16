# -*- coding: utf-8 -*
'''!
  @file  DFRobot_ENS160.py
  @brief  Define infrastructure of DFRobot_ENS160 class
  @details  This is a Digital Metal-Oxide Multi-Gas Sensor. It can be controlled by I2C and SPI port.
  @n        Detection of a variety of gases, such as volatile organic compounds (VOCs), including ethanol, 
  @n        toluene, as well as hydrogen and nitrogen dioxide, has superior selectivity and accuracy.
  @copyright  Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
  @license  The MIT License (MIT)
  @author  [qsjhyy](yihuan.huang@dfrobot.com)
  @version  V1.0
  @date  2021-10-28
  @url  https://github.com/DFRobot/DFRobot_ENS160
'''
import sys
import time

import smbus
import spidev
import RPi.GPIO as GPIO

import logging
from ctypes import *


logger = logging.getLogger()
# logger.setLevel(logging.INFO)   # Display all print information
logger.setLevel(logging.FATAL)   # If you don’t want to display too many prints, only print errors, please use this option
ph = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - [%(filename)s %(funcName)s]:%(lineno)d - %(levelname)s: %(message)s")
ph.setFormatter(formatter) 
logger.addHandler(ph)


## 0b00011101 = x^8+x^4+x^3+x^2+x^0 (x^8 is implicit)
POLY = 0x1D
## ENS160 chip version
ENS160_PART_ID = 0x160

# ENS160 Register address
## This 2-byte register contains the part number in little endian of the ENS160.
ENS160_PART_ID_REG = 0x00
## This 1-byte register sets the Operating Mode of the ENS160.
ENS160_OPMODE_REG = 0x10
## This 1-byte register configures the action of the INTn pin.
ENS160_CONFIG_REG = 0x11
## This 1-byte register allows some additional commands to be executed on the ENS160.
ENS160_COMMAND_REG = 0x12
## This 2-byte register allows the host system to write ambient temperature data to ENS160 for compensation.
ENS160_TEMP_IN_REG = 0x13
## This 2-byte register allows the host system to write relative humidity data to ENS160 for compensation.
ENS160_RH_IN_REG = 0x15
## This 1-byte register indicates the current STATUS of the ENS160.
ENS160_DATA_STATUS_REG = 0x20
## This 1-byte register reports the calculated Air Quality Index according to the UBA.
ENS160_DATA_AQI_REG = 0x21
## This 2-byte register reports the calculated TVOC concentration in ppb.
ENS160_DATA_TVOC_REG = 0x22
## This 2-byte register reports the calculated equivalent CO2-concentration in ppm, based on the detected VOCs and hydrogen.
ENS160_DATA_ECO2_REG = 0x24
## This 2-byte register reports the calculated ethanol concentration in ppb.
ENS160_DATA_ETOH_REG = 0x22
## This 2-byte register reports the temperature used in its calculations (taken from TEMP_IN, if supplied).
ENS160_DATA_T_REG = 0x30
## This 2-byte register reports the relative humidity used in its calculations (taken from RH_IN if supplied).
ENS160_DATA_RH_REG = 0x32
## This 1-byte register reports the calculated checksum of the previous DATA_ read transaction (of n-bytes).
ENS160_DATA_MISR_REG = 0x38
## This 8-byte register is used by several functions for the Host System to pass data to the ENS160.
ENS160_GPR_WRITE_REG = 0x40
## This 8-byte register is used by several functions for the ENS160 to pass data to the Host System.
ENS160_GPR_READ_REG = 0x48

# OPMODE(Address 0x10) register mode
## DEEP SLEEP mode (low power standby).
ENS160_SLEEP_MODE  = 0x00
## IDLE mode (low-power).
ENS160_IDLE_MODE = 0x01
## STANDARD Gas Sensing Modes.
ENS160_STANDARD_MODE = 0x02

# CMD(0x12) register command
## reserved. No command.
ENS160_COMMAND_NOP = 0x00
## Get FW Version Command.
ENS160_COMMAND_GET_APPVER = 0x0E
## Clears GPR Read Registers Command.
ENS160_COMMAND_CLRGPR = 0xCC


class DFRobot_ENS160(object):
    '''!
      @brief Define DFRobot_ENS160 basic class
      @details Drive the gas sensor
    '''

    # Interrupt pin active signal level
    e_INT_pin_active_low = 0<<6   ## Active low
    e_INT_pin_active_high = 1<<6   ## Active high

    # Interrupt pin output driving mode
    e_INT_pin_OD = 0<<5   ## Open drain
    e_INT_pin_PP = 1<<5   ## Push / Pull

    # The status of interrupt pin when new data appear in General Purpose Read Registers
    e_INT_GPR_drdy_DIS = 0<<3   ## Disable
    e_INT_GPR_drdy_EN = 1<<3   ## Enable

    # The status of interrupt pin when new data appear in DATA_XXX
    e_INT_data_drdy_DIS = 0<<1   ## Disable
    e_INT_data_drdy_EN = 1<<1   ## Enable

    # Interrupt pin main switch mode
    e_INT_mode_DIS = 0   ## Disable
    e_INT_mode_EN = 1   ## Enable

    # The sensor operating status
    e_normal_operation = 0   ## Normal operation; 
    e_warm_up_phase = 1   ## Warm-Up phase; 
    e_initial_start_up_phase = 2   ## Initial Start-Up phase; 
    e_invalid_output = 3   ## Invalid output

    class sensor_status(Structure):
        '''
          @brief Sensor status flag is buffered into "DATA_STATUS (Address 0x20)" register
          @note Register structure:
          @n -----------------------------------------------------------------------------------
          @n |    b7    |   b6   |    b5   |    b4   |    b3   |    b2   |    b1    |    b0    |
          @n -----------------------------------------------------------------------------------
          @n |  STATAS  | STATER |     reserved      |   VALIDITY FLAG   |  NEWDAT  |  NEWGPR  |
          @n -----------------------------------------------------------------------------------
          status: 0: Indicates not running normally
                  1: Indicates that an OPMODE is running
          stater: 0: Indicates that no error was detected
                  1: Indicates that an error is detected
                  E.g. Invalid Operating Mode has been selected
          validity_flag: 00: Normal operation
                         01: Warm-Up phase
                         10: Initial Start-Up phase
                         11: Invalid output
          data_drdy: 0: General purpose register data not ready
                     1: General purpose register data ready
          GPR_drdy: 0: General purpose register data not ready
                    1: General purpose register data ready
        '''
        _pack_ = 1
        _fields_ = [('GPR_drdy',c_ubyte,1),
                    ('data_drdy',c_ubyte,1),
                    ('validity_flag',c_ubyte,2),
                    ('reserved',c_ubyte,2),
                    ('stater',c_ubyte,1),
                    ('status',c_ubyte,1)]
        def __init__(self):
            '''!
              @brief sensor_status structure init
            '''
            self.GPR_drdy = 0
            self.data_drdy = 0
            self.validity_flag = 0
            self.stater = 0
            self.status = 0

        def set_list(self, data):
            '''!
              @brief Assign the structure
              @param data uint8_t data to be assigned
            '''
            buf = (c_ubyte * len(data))()
            for i in range(len(data)):
                buf[i] = data[i]
            memmove(addressof(self), addressof(buf), len(data))

        def get_list(self):
            '''!
              @brief Obtain the structure value
              @return Return the structure value
            '''
            return list(bytearray(string_at( addressof(self), sizeof(self) )))

    def __init__(self):
        '''!
          @brief Module init
        '''
        self.misr = 0   # Mirror of DATA_MISR (0 is hardware default)
        self.sensor_status = self.sensor_status()   # The structure class for storing the sensor status, uint8_t

    def begin(self):
        '''!
          @brief Initialize sensor
          @return  Return init status
          @retval True indicate initialization succeed
          @retval False indicate initialization failed
        '''
        ret = True
        chip_id = self._read_reg(ENS160_PART_ID_REG, 2)
        logger.info( ((chip_id[1] << 8) | chip_id[0]) )
        if ENS160_PART_ID != ((chip_id[1] << 8) | chip_id[0]):
            ret = False
        self.set_PWR_mode(ENS160_STANDARD_MODE)
        self.set_INT_mode(0x00)
        return ret

    def set_PWR_mode(self, mode):
        '''!
          @brief Configure power mode
          @param mode Configurable power mode:
          @n       ENS160_SLEEP_MODE: DEEP SLEEP mode (low power standby)
          @n       ENS160_IDLE_MODE: IDLE mode (low-power)
          @n       ENS160_STANDARD_MODE: STANDARD Gas Sensing Modes
        '''
        self._write_reg(ENS160_OPMODE_REG, mode)
        time.sleep(0.02)

    def set_INT_mode(self, mode):
        '''!
          @brief Interrupt config(INT)
          @param mode Interrupt mode to be set, perform OR operation on the following to get mode:
          @n       The interrupt occur when new data appear in DATA_XXX register (can get new measured data): e_INT_mode_DIS, disable interrupt; e_INT_mode_EN, enable interrupt
          @n       Interrupt pin output driving mode: e_INT_pin_OD, open drain; e_INT_pin_PP, push pull
          @n       Interrupt pin active level: e_INT_pin_active_low, active low; e_INT_pin_active_high, active high
        '''
        mode |= (self.e_INT_data_drdy_EN | self.e_INT_GPR_drdy_DIS)
        self._write_reg(ENS160_CONFIG_REG, mode)
        time.sleep(0.02)

    def set_temp_and_hum(self, ambient_temp, relative_humidity):
        '''!
          @brief Users write ambient temperature and relative humidity into ENS160 for calibration and compensation of the measured gas data.
          @param ambient_temp Compensate the current ambient temperature, float type, unit: C
          @param relative_humidity Compensate the current ambient humidity, float type, unit: %rH
        '''
        temp = int((ambient_temp + 273.15) * 64 + 0.5)
        rh = int(relative_humidity * 512 + 0.5)

        buf = [0, 0, 0, 0]
        buf[0] = temp & 0xFF
        buf[1] = (temp & 0xFF00) >> 8
        buf[2] = rh & 0xFF
        buf[3] = (rh & 0xFF00) >> 8

        self._write_reg(ENS160_TEMP_IN_REG, buf)

    def _send_command(self, mode):
        '''!
          @brief Sensor GPR clear command and command of obtaining FW version number
          @param mode Sensor three basic commands:
          @n       ENS160_COMMAND_NOP: null command
          @n       ENS160_COMMAND_GET_APPVER: Get FW Version Command.
          @n       ENS160_COMMAND_CLRGPR: Clears GPR Read Registers Command.
        '''
        # Save the previous mode
        old_mode = self._read_reg(ENS160_OPMODE_REG, 1)[0]

        self.set_PWR_mode(ENS160_IDLE_MODE);   # commands will only be actioned in IDLE mode (OPMODE 0x01).
        self._write_reg(ENS160_COMMAND_REG, mode)
        self.set_PWR_mode(old_mode);   # Restore to the previous mode

    def get_ENS160_status(self):
        '''!
          @brief This API is used to get the sensor operating status
          @return Operating status:
          @n        eNormalOperation: Normal operation; 
          @n        eWarmUpPhase: Warm-Up phase; 
          @n        eInitialStartUpPhase: Initial Start-Up phase; 
          @n        eInvalidOutput: Invalid output
        '''
        self.sensor_status.set_list(self._read_reg(ENS160_DATA_STATUS_REG, 1))
        return self.sensor_status.validity_flag

    @property
    def get_AQI(self):
        '''!
          @brief Get the air quality index calculated on the basis of UBA
          @return Return value range: 1-5 (Corresponding to five levels of Excellent, Good, Moderate, Poor and Unhealthy respectively)
        '''
        return self._read_reg(ENS160_DATA_AQI_REG, 1)[0]

    @property
    def get_TVOC_ppb(self):
        '''!
          @brief Get TVOC concentration
          @return Return value range: 0–65000, unit: ppb
        '''
        buf = self._read_reg(ENS160_DATA_TVOC_REG, 2)
        return ((buf[1] << 8) | buf[0])

    @property
    def get_ECO2_ppm(self):
        '''!
          @brief Get CO2 equivalent concentration calculated according to the detected data of VOCs and hydrogen (eCO2 – Equivalent CO2)
          @return Return value range: 400–65000, unit: ppm
          @note Five levels: Excellent(400 - 600), Good(600 - 800), Moderate(800 - 1000), 
          @n                  Poor(1000 - 1500), Unhealthy(> 1500)
        '''
        buf = self._read_reg(ENS160_DATA_ECO2_REG, 2)
        return ((buf[1] << 8) | buf[0])

    def _get_MISR(self):
        '''!
          @brief Get the current crc check code of the sensor
          @return The current crc check code of the sensor
        '''
        return self._read_reg(ENS160_DATA_MISR_REG, 1)[0]

    def _calc_MISR(self, data):
        '''!
          @brief Calculate the current crc check code and compare it with the MISR read from the sensor
          @param data The measured data just obtained from the sensor
          @return The current calculated crc check code
        '''
        misr_xor= ( (self.misr<<1) ^ data ) & 0xFF
        if( (self.misr & 0x80) == 0 ):
          self.misr = misr_xor
        else:
          self.misr = misr_xor ^ POLY
        return self.misr

    def _write_reg(self, reg, data):
        '''!
          @brief writes data to a register
          @param reg register address
          @param data written data
        '''
        # Low level register writing, not implemented in base class
        raise NotImplementedError()

    def _read_reg(self, reg, length):
        '''!
          @brief read the data from the register
          @param reg register address
          @param length read data length
          @return read data list
        '''
        # Low level register writing, not implemented in base class
        raise NotImplementedError()


class DFRobot_ENS160_I2C(DFRobot_ENS160):
    '''!
      @brief Define DFRobot_ENS160_I2C basic class
      @details Use I2C protocol to drive the pressure sensor
    '''

    def __init__(self, i2c_addr=0x53, bus=1):
        '''!
          @brief Module I2C communication init
          @param i2c_addr I2C communication address
          @param bus I2C bus
        '''
        self._addr = i2c_addr
        self.i2c = smbus.SMBus(bus)
        super(DFRobot_ENS160_I2C, self).__init__()

    def _write_reg(self, reg, data):
        '''!
          @brief writes data to a register
          @param reg register address
          @param data written data
        '''
        if isinstance(data, int):
            data = [data]
            #logger.info(data)
        self.i2c.write_i2c_block_data(self._addr, reg, data)

    def _read_reg(self, reg, length):
        '''!
          @brief read the data from the register
          @param reg register address
          @param length length of data to be read
          @return read data list
        '''
        return self.i2c.read_i2c_block_data(self._addr, reg, length)


class DFRobot_ENS160_SPI(DFRobot_ENS160):
    '''!
      @brief Define DFRobot_ENS160_SPI basic class
      @details Use SPI protocol to drive the pressure sensor
    '''

    def __init__(self, cs=8, bus=0, dev=0, speed=2000000):
        '''!
          @brief Module SPI communication init
          @param cs cs chip select pin
          @param bus SPI bus 
          @param dev SPI device number
          @param speed SPI communication frequency
        '''
        self._cs = cs
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self._cs, GPIO.OUT, initial=1)
        GPIO.output(self._cs, GPIO.LOW)
        self.spi = spidev.SpiDev()
        self.spi.open(bus, dev)
        self.spi.no_cs = True
        self.spi.max_speed_hz = speed
        super(DFRobot_ENS160_SPI, self).__init__()

    def _write_reg(self, reg, data):
        '''!
          @brief writes data to a register
          @param reg register address
          @param data written data
        '''
        if isinstance(data, int):
            data = [data]
            #logger.info(data)
        reg_addr = [(reg << 1) & 0xFE]
        GPIO.output(self._cs, GPIO.LOW)
        self.spi.xfer(reg_addr)
        self.spi.xfer(data)
        GPIO.output(self._cs, GPIO.HIGH)

    def _read_reg(self, reg, length):
        '''!
          @brief read the data from the register
          @param reg register address
          @param length length of data to be read 
          @return read data list
        '''
        reg_addr = [(reg << 1) | 0x01]
        GPIO.output(self._cs, GPIO.LOW)
        #logger.info(reg_addr)
        self.spi.xfer(reg_addr)
        time.sleep(0.01)
        # self.spi.readbytes(1)
        rslt = self.spi.readbytes(length)
        GPIO.output(self._cs, GPIO.HIGH)
        return rslt
