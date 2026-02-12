#!/usr/bin/python3
import spidev
import serial
import RPi.GPIO as GPIO
from datetime import datetime
import pickle

#constants
def cSINGLEEVENTFILE():
	return 'single_events.txt'

def cAVERAGEDATAFILE():
	return 'pm_hourly_avg.txt'

def cAVERAGEDATABASEFILE():
	return 'pm_hourly_avg_db.txt'

def cR1():
	return 11.2

def cR2():
	return 2.2

def cUF_diode():
	return 0.85

def cUlow_pbAcidBatt():
	return 11.1

def cUlow_liFePO4Batt():
	return 12.4

def cSDS011_POW_ON_OFF_PIN():
	return 31

def cSCI_RCV_TIMEOUT_SECS():
	return 25

def cSCRIPT_VERSION():
	return 20260208

#variables
idx = 0
noOfVals = 0
avgPM2_5val = 0
avgPM10_val = 0
currPM2_5val = 0
currPM10_val = 0
currSupplyVoltage_val = 0
dateString = ""
fSupplyVoltageLastCall = 12

#use pin numbers not GPIO-numbers
GPIO.setmode(GPIO.BOARD)
#pin31 = GPIO22 = bcm-pin6 = SDS011-power-on/off
GPIO.setup(cSDS011_POW_ON_OFF_PIN(), GPIO.OUT)
#switch SDS011-power-on
GPIO.output(cSDS011_POW_ON_OFF_PIN(), GPIO.HIGH)

spi = spidev.SpiDev()
spi.open(0,1)
spi.max_speed_hz = 500000
spi.mode = 0
spi.bits_per_word = 8

sci = serial.Serial("/dev/serial0")
sci.baudrate = 9600
sci.bytesize = serial.EIGHTBITS
sci.parity = serial.PARITY_NONE
#sci.stopbits = STOPBITS_ONE
sci.timeout = cSCI_RCV_TIMEOUT_SECS()

sci.flushInput()

def analog_read(channel):
	r = spi.xfer([0x01, 0x80, 0x00])
	if 0 <= r[1] <= 3:
		adc_out = ((r[1] * 256) + r[2])
	else:
		adc_out = 0
	return adc_out

def supply_voltage_read():
	adc_raw_val = analog_read(0)
	adc_volt_val = adc_raw_val * 3.3 / 1024
	scaled_volt_val = (adc_volt_val / (cR2() / (cR1() + cR2())) + cUF_diode())
	return scaled_volt_val

def sds011_read():
	crc = 0
	exitCond = False
	pm2_5val = 0
	pm10val = 0
	tsStartTime = datetime.now()
	tsEndTime = tsStartTime
	tsDiffTime = tsEndTime - tsStartTime
	fDiffTimeInSeconds = tsDiffTime.total_seconds()
	#while within 10s after call or exit condition false
	while ((fDiffTimeInSeconds < cSCI_RCV_TIMEOUT_SECS()) and (exitCond == False)):
		incomingByte = ord(sci.read())
		if (incomingByte == 0xAA):
			buf = sci.read(9)
			if ((buf[0] == 0xC0) & (buf[8] == 0xAB)):
				for i in range(1, 7):
					crc = crc + buf[i]
					crc = crc & 0xFF
					#print("buf[" + str(i) + "]" + str(buf[i]))
				#print("crc:"+ str(crc))
				#print("buf[7]:" + str(buf[7]))
				if (crc == buf[7]):
					pm2_5val = ((256 * buf[2]) + buf[1])/10
					pm10val  = ((256 * buf[4]) + buf[3])/10
					exitCond = True
		tsEndTime = datetime.now()
		tsDiffTime = tsEndTime - tsStartTime
		fDiffTimeInSeconds = tsDiffTime.total_seconds()
	#print("incomingByte:" + str(incomingByte))
	return pm2_5val, pm10val

print("feinstaubpi.py-version:" + str(cSCRIPT_VERSION()))
tsCurrRunDate = datetime.now() #get timestamp of current script run
currSupplyVoltage_val = supply_voltage_read()
print("Supply Voltage=" + str(currSupplyVoltage_val))
currPM2_5val, currPM10_val = sds011_read()
print("PM2.5-value=" + str(currPM2_5val) + " | PM10-value=" + str(currPM10_val))

#switch SDS011-power-off
GPIO.output(cSDS011_POW_ON_OFF_PIN(), GPIO.LOW)

GPIO.cleanup()
spi.close()
sci.close()

#open last processed single event data file or create if not existing
try:
	fRd = open(cSINGLEEVENTFILE(), 'rb')
except IOError:
	#there is no single event file existing
	nOfVals = 0 #no data stored already
	tsPrevRunDate = tsCurrRunDate #there is no previous run time so use the current one
	uiDataStoredThisHour = 0 #indicator that the average result file was already written when 1
else:
	#single event file exists and could be opened
	dataToRead = pickle.load(fRd) #read in the file content into a pickled list
	fRd.close() #close the file that was opened for reading
	noOfVals = dataToRead[0]
	tsPrevRunDate = datetime.strptime(dataToRead[1], '%Y-%m-%d %H:%M:%S.%f') #convert the read date string into a timestamp
	avgPM2_5val = dataToRead[2]
	avgPM10_val = dataToRead[3]
	uiDataStoredThisHour = dataToRead[4]
	fSupplyVoltageLastCall = dataToRead[5]

#check the current supply voltage
if ( (fSupplyVoltageLastCall < cUlow_liFePO4Batt()) & (currSupplyVoltage_val < cUlow_liFePO4Batt()) ):
	uiTooLowSupplyVoltage = 1
else:
	uiTooLowSupplyVoltage = 0

#check if previous stored call and current call are in the same hour
prevHr = "{:%H}".format(tsPrevRunDate)
currHr = "{:%H}".format(tsCurrRunDate)
currMin = "{:%M}".format(tsCurrRunDate)
if (tsPrevRunDate == tsCurrRunDate):
	#this happens only if no previous data are stored	
	avgPM2_5val = ((noOfVals * avgPM2_5val) + currPM2_5val)/(noOfVals + 1)
	avgPM10_val = ((noOfVals * avgPM10_val) + currPM10_val)/(noOfVals + 1)
	noOfVals = 1
elif (prevHr == currHr):
	#when the calls are within the same hour average the values
	avgPM2_5val = ((noOfVals * avgPM2_5val) + currPM2_5val)/(noOfVals + 1)
	avgPM10_val = ((noOfVals * avgPM10_val) + currPM10_val)/(noOfVals + 1)
	noOfVals = noOfVals + 1
else:
	#when the calls are in different hours start the averaging again
	noOfVals = 0 #reset the number of values used for averaging
	uiDataStoredThisHour = 0 #reset the indicator that data of the current hour were written already
	avgPM2_5val = ((noOfVals * avgPM2_5val) + currPM2_5val)/(noOfVals + 1)
	avgPM10_val = ((noOfVals * avgPM10_val) + currPM10_val)/(noOfVals + 1)
#prepare data to be written to result file
dateString = "{:%Y-%m-%d %H:%M:%S.%f}".format(tsCurrRunDate)
if ((int(currMin) >= 48) & (uiDataStoredThisHour == 0)):
	uiDataStoredThisHour = 1
	#prepare data to be written to result file
	avgDataToWrite = [dateString, avgPM2_5val, avgPM10_val, currSupplyVoltage_val, uiTooLowSupplyVoltage]
	#write final result file
	fWr = open(cAVERAGEDATAFILE(), 'wb') #open the hourly average data file for writing
	pickle.dump(avgDataToWrite, fWr, protocol=0)  #write the pickled list to the file
	fWr.close() #close the write file
	fWr = open(cAVERAGEDATABASEFILE(), 'a') #open the hourly average database file for appending
	writeBuffer = "%s;%.1f;%.1f;%.2f;%d\n" % (dateString, round(avgPM2_5val, 1), round(avgPM10_val, 1), round(currSupplyVoltage_val, 2), uiTooLowSupplyVoltage)
	fWr.write(writeBuffer) #write the data to the file
	fWr.close() #close the write file
#prepare data to be written to result file
dataToWrite = [noOfVals, dateString, avgPM2_5val, avgPM10_val, uiDataStoredThisHour, currSupplyVoltage_val]
print(dataToWrite)
#write data to result file
fWr = open(cSINGLEEVENTFILE(), 'wb') #open the single event file for writing
pickle.dump(dataToWrite, fWr)  #write the pickled list to the file
fWr.close() #close the write file
