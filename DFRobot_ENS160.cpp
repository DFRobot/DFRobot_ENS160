/*!
 * @file DFRobot_ENS160.cpp
 * @brief  Define the infrastructure DFRobot_ENS160 class
 * @n This is a Digital Metal-Oxide Multi-Gas Sensor. It can be controlled by I2C and SPI port.
 * @copyright Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
 * @license The MIT License (MIT)
 * @author [qsjhyy](yihuan.huang@dfrobot.com)
 * @version  V1.0
 * @date  2021-10-26
 * @url https://github.com/DFRobot/DFRobot_ENS160
 */
#include "DFRobot_ENS160.h"

DFRobot_ENS160::DFRobot_ENS160()
{
  misr = 0;   // Mirror of DATA_MISR (0 is hardware default)
}

int DFRobot_ENS160::begin(void)
{
  uint8_t idBuf[2];
  if(0 == readReg(ENS160_PART_ID_REG, idBuf, sizeof(idBuf)))   // Judge whether the data bus is successful
  {
    DBG("ERR_DATA_BUS");
    return ERR_DATA_BUS;
  }

  DBG("real sensor id=");DBG(ENS160_CONCAT_BYTES(idBuf[1], idBuf[0]));
  if(ENS160_PART_ID != ENS160_CONCAT_BYTES(idBuf[1], idBuf[0]))   // Judge whether the chip version matches
  {
    DBG("ERR_IC_VERSION");
    return ERR_IC_VERSION;
  }
  setPWRMode(ENS160_STANDARD_MODE);
  setINTMode(0x00);

  DBG("begin ok!");
  return NO_ERR;
}

/***************** Config function ******************************/

void DFRobot_ENS160::setPWRMode(uint8_t mode)
{
  writeReg(ENS160_OPMODE_REG, &mode, sizeof(mode));
  delay(20);   // Give it some time to switch mode
}

void DFRobot_ENS160::setINTMode(uint8_t mode)
{
  mode |= (eINTDataDrdyEN | eIntGprDrdyDIS);
  writeReg(ENS160_CONFIG_REG, &mode, sizeof(mode));
  delay(20);   // Give it some time to switch mode
}

void DFRobot_ENS160::setTempAndHum(float ambientTemp, float relativeHumidity)
{
  uint16_t temp = (ambientTemp + 273.15) * 64;
  uint16_t rh = relativeHumidity * 512;
  uint8_t buf[4];

  buf[0] = temp & 0xFF;
  buf[1] = (temp & 0xFF00) >> 8;
  buf[2] = rh & 0xFF;
  buf[3] = (rh & 0xFF00) >> 8;
  writeReg(ENS160_TEMP_IN_REG, buf, sizeof(buf));
}

/***************** Performance function ******************************/
uint8_t DFRobot_ENS160::getENS160Status(void)
{
  readReg(ENS160_DATA_STATUS_REG, &ENS160Status, sizeof(ENS160Status));
  return ENS160Status.validityFlag;
}

uint8_t DFRobot_ENS160::getAQI(void)
{
  uint8_t data = 0;
  readReg(ENS160_DATA_AQI_REG, &data, sizeof(data));
  return data;
}

uint16_t DFRobot_ENS160::getTVOC(void)
{
  uint8_t buf[2];
  readReg(ENS160_DATA_TVOC_REG, buf, sizeof(buf));
  return ENS160_CONCAT_BYTES(buf[1], buf[0]);
}

uint16_t DFRobot_ENS160::getECO2(void)
{
  uint8_t buf[2];
  readReg(ENS160_DATA_ECO2_REG, buf, sizeof(buf));
  return ENS160_CONCAT_BYTES(buf[1], buf[0]);
}

/************************** crc check calculation function ******************************/
uint8_t DFRobot_ENS160::getMISR(void)
{
  uint8_t crc = 0;
  readReg(ENS160_DATA_MISR_REG, &crc, sizeof(crc));
  return crc;
}

uint8_t DFRobot_ENS160::calcMISR(uint8_t data)
{
  uint8_t misr_xor= ( (misr<<1) ^ data ) & 0xFF;
  if( (misr & 0x80) == 0 )
    misr = misr_xor;
  else
    misr = misr_xor ^ POLY;

  return misr;
}

/***************** Init and read/write of I2C and SPI interfaces ******************************/

DFRobot_ENS160_I2C::DFRobot_ENS160_I2C(TwoWire *pWire, uint8_t i2cAddr)
{
  _deviceAddr = i2cAddr;
  _pWire = pWire;
}

int DFRobot_ENS160_I2C::begin(void)
{
  _pWire->begin();   // Wire.h(I2C)library function initialize wire library
  return DFRobot_ENS160::begin();   // Use the initialization function of the parent class
}

void DFRobot_ENS160_I2C::writeReg(uint8_t reg, const void* pBuf, size_t size)
{
  if(pBuf == NULL) {
    DBG("pBuf ERROR!! : null pointer");
  }
  uint8_t * _pBuf = (uint8_t *)pBuf;

  _pWire->beginTransmission(_deviceAddr);
  _pWire->write(reg);

  for(size_t i = 0; i < size; i++) {
    _pWire->write(_pBuf[i]);
  }
  _pWire->endTransmission();
}

size_t DFRobot_ENS160_I2C::readReg(uint8_t reg, void* pBuf, size_t size)
{
  size_t count = 0;
  if(NULL == pBuf) {
    DBG("pBuf ERROR!! : null pointer");
  }
  uint8_t * _pBuf = (uint8_t*)pBuf;

  _pWire->beginTransmission(_deviceAddr);
  _pWire -> write(reg);
  if(0 != _pWire->endTransmission()) {   // Used Wire.endTransmission() to end a slave transmission started by beginTransmission() and arranged by write().
    DBG("endTransmission ERROR!!");
  } else {
    _pWire->requestFrom(_deviceAddr, (uint8_t)size);   // Master device requests size bytes from slave device, which can be accepted by master device with read() or available()
    
    while (_pWire->available()) {
      _pBuf[count++] = _pWire->read();   // Use read() to receive and put into buf
    }
    // _pWire->endTransmission();
  }
  return count;
}

DFRobot_ENS160_SPI::DFRobot_ENS160_SPI(SPIClass *pSpi, uint8_t csPin)
{
  _pSpi = pSpi;
  _csPin = csPin;
}

int DFRobot_ENS160_SPI::begin(void)
{
  pinMode(_csPin, OUTPUT);
  digitalWrite(_csPin,HIGH);
  _pSpi->begin();
  return DFRobot_ENS160::begin();
}

void DFRobot_ENS160_SPI::writeReg(uint8_t reg, const void* pBuf, size_t size)
{
  if(NULL == pBuf) {
    DBG("pBuf ERROR!! : null pointer");
  }
  uint8_t * _pBuf = (uint8_t *)pBuf;

  _pSpi->beginTransaction(SPISettings(2000000, MSBFIRST, SPI_MODE0));
  digitalWrite(_csPin, LOW);
  _pSpi->transfer((reg << 1) & 0xFE);
  while(size--) {
    _pSpi->transfer(*_pBuf);
    _pBuf++;
  }
  digitalWrite(_csPin, HIGH);
  _pSpi->endTransaction();
}

size_t DFRobot_ENS160_SPI::readReg(uint8_t reg, void* pBuf, size_t size)
{
  if(NULL == pBuf) {
    DBG("pBuf ERROR!! : null pointer");
  }
  uint8_t * _pBuf = (uint8_t *)pBuf;

  size_t count = 0;
  _pSpi->beginTransaction(SPISettings(2000000, MSBFIRST, SPI_MODE0));
  digitalWrite(_csPin, LOW);
  _pSpi->transfer((reg << 1) | 0x01);
  // _pSpi->transfer(0x00);
  while(size--) {
    *_pBuf = _pSpi->transfer(0x00);
    _pBuf++;
    count++;
  }
  _pSpi->endTransaction();
  digitalWrite(_csPin, HIGH);

  return count;
}
