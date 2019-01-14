#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interface with a StorkAir WHR930 on Domoticz
Version 0.8 by albert[@]hakvoort[.]co

code based on code from Mosibi

Publish every 10 seconds the status on a MQTT Domoticz/in topic
Listen on MQTT topic for commands to set the ventilation level

todo :

- set bypass temperature
- check on faulty messages
- serial check

"""

import paho.mqtt.client as mqtt
import time
import serial
import json

IDXOutsideAirTemp=20		# temperature
IDXSupplyAirTemp=21		# temperature
IDXReturnAirTemp=22		# temperature
IDXExhaustAirTemp=23		# temperature
IDXIntakeFanSpeed=329		# text
IDXExhaustFanSpeed=330		# text
IDXIntakeFanRPM=331		# text
IDXExhaustFanRPM=332		# text
IDXStrIntakeFanActive=333	# text
IDXFanLevel=334			# text
IDXFilter=335			# text
IDXSelector=125			# selector 0=auto 10=away 20=low 30=middle 40=high

print("************************")
print("* WHR930 MQTT Domoticz *")
print("************************")
print("")

fan_level=0

def debug_msg(message):
    if debug is True:
        print('{0} DEBUG: {1}'.format(time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()), message))

def warning_msg(message):
    print('{0} WARNING: {1}'.format(time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()), message))

def info_msg(message):
    print('{0} INFO: {1}'.format(time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()), message))

def debug_data(serial_data):
    print('Ack           : {0} {1}'.format(serial_data[0], serial_data[1]))
    print('Start         : {0} {1}'.format(serial_data[2], serial_data[3]))
    print('Command       : {0} {1}'.format(serial_data[4], serial_data[5]))
    print('Nr data bytes : {0} (integer {1})'.format(serial_data[6], int(serial_data[6], 16)))

    n = 1
    while n <= int(serial_data[6], 16):
        print('Data byte {0}   : Hex: {1}, Int: {2}, Array #: {3}'.format(n, serial_data[n+6], int(serial_data[n + 6], 16), n + 6))

        n += 1
    
    print('Checksum      : {0}'.format(serial_data[-2]))
    print('End           : {0} {1}'.format(serial_data[-1], serial_data[-0]))


def on_message(client, userdata, message):
	#print("message check")
	msg_data = str(message.payload.decode("utf-8"))
	json_data = json.loads(msg_data)
	status = json_data['idx']
	if status == IDXSelector:
		print ("IDX Selector found on MQTT broker Domoticz")
		fan_level=99
		selector = int(json_data['svalue1'])
		if 0 == selector: 
			print("s1 is 0")
			fan_level=1
		elif 10 == selector: 
			print("s1 is 10")
			fan_level=1
		elif 20 == selector:
			print("s1 is 20")
			fan_level=2
		elif 30 == selector:
			print("s1 is 30")
			fan_level=3
		elif 40 == selector:
			print("s1 is 40")
			fan_level=4
		if fan_level >= 0 and fan_level <= 4:
            		set_ventilation_level(fan_level)


def publish_message(msg, mqtt_path):                                                                      
    mqttc.publish(mqtt_path, payload=msg, qos=0, retain=True)
    time.sleep(0.1)
    debug_msg('published message {0} on topic {1} at {2}'.format(msg, mqtt_path, time.asctime(time.localtime(time.time()))))

def serial_command(cmd):
    data = []
    ser.write(cmd)
    time.sleep(2)

    while ser.inWaiting() > 0:
        data.append(ser.read(1).hex())

    if len(data) > 0:
        return data
    else:
        return None

def set_ventilation_level(nr):
    if nr == 0:
        data = serial_command(b'\x07\xF0\x00\x99\x01\x01\x48\x07\x0F')
    elif nr == 1:
        data = serial_command(b'\x07\xF0\x00\x99\x01\x02\x49\x07\x0F')
    elif nr == 2:
        data = serial_command(b'\x07\xF0\x00\x99\x01\x03\x4A\x07\x0F')
    elif nr == 3:
        data = serial_command(b'\x07\xF0\x00\x99\x01\x04\x4B\x07\x0F')
    elif nr == 4:
        data = serial_command(b'\x07\xF0\x00\x99\x01\x00\x47\x07\x0F')

    if data:
        if ( data[0] == '07' and data[1] == 'f3' ):
            info_msg('Changed the ventilation to {0}'.format(nr))
        else:
            warning_msg('Changing the ventilation to {0} went wrong, did not receive an ACK after the set command'.format(nr))
    else:
        warning_msg('Changing the ventilation to {0} went wrong, did not receive an ACK after the set command'.format(nr))

def get_temp():
    data = serial_command(b'\x07\xF0\x00\x0F\x00\xBC\x07\x0F')

    if data == None:
        warning_msg('get_temp function could not get serial data')
    else:
        OutsideAirTemp = int(data[7], 16) / 2.0 - 20
        SupplyAirTemp = int(data[8], 16) / 2.0 - 20
        ReturnAirTemp = int(data[9], 16) / 2.0 - 20
        ExhaustAirTemp = int(data[10], 16) / 2.0 - 20

        publish_message(msg='{ "idx" : ' +str(IDXOutsideAirTemp) +str(', "nvalue" : 0, "svalue" :"') +str(OutsideAirTemp) +str('"}'), mqtt_path='domoticz/in')
        publish_message(msg='{ "idx" : ' +str(IDXSupplyAirTemp) +str(', "nvalue" : 0, "svalue" :"') +str(SupplyAirTemp) +str('"}'), mqtt_path='domoticz/in')
        publish_message(msg='{ "idx" : ' +str(IDXReturnAirTemp) +str(', "nvalue" : 0, "svalue" :"') +str(ExhaustAirTemp) +str('"}'), mqtt_path='domoticz/in')    
        publish_message(msg='{ "idx" : ' +str(IDXExhaustAirTemp) +str(', "nvalue" : 0, "svalue" :"') +str(ReturnAirTemp) +str('"}'), mqtt_path='domoticz/in')
     
        debug_msg('OutsideAirTemp: {0}, SupplyAirTemp: {1}, ReturnAirTemp: {2}, ExhaustAirTemp: {3}'.format(OutsideAirTemp, SupplyAirTemp, ReturnAirTemp, ExhaustAirTemp))

def get_ventilation_status():
    data = serial_command(b'\x07\xF0\x00\xCD\x00\x7A\x07\x0F')

    if data == None:
        warning_msg('get_ventilation_status function could not get serial data')
    else:
        ReturnAirLevel = int(data[13], 16)
        SupplyAirLevel = int(data[14], 16)
        FanLevel = int(data[15], 16) - 1
        IntakeFanActive = int(data[16], 16)

        if IntakeFanActive == 1:
            StrIntakeFanActive = 'Yes'
        elif IntakeFanActive == 0:
            StrIntakeFanActive = 'No'
        else:
            StrIntakeFanActive = 'Unknown'
            
        publish_message(msg='{ "idx" : ' +str(IDXFanLevel) +str(', "nvalue" : 0, "svalue" :"') +str(FanLevel) +str('"}'), mqtt_path='domoticz/in')
        publish_message(msg='{ "idx" : ' +str(IDXStrIntakeFanActive) +str(', "nvalue" : 0, "svalue" :"') +str(StrIntakeFanActive) +str('"}'), mqtt_path='domoticz/in')

        debug_msg('ReturnAirLevel: {}, SupplyAirLevel: {}, FanLevel: {}, IntakeFanActive: {}'.format(ReturnAirLevel, SupplyAirLevel, FanLevel, StrIntakeFanActive))

def get_fan_status():
    # 0x07 0xF0 0x00 0x0B 0x00 0xB8 0x07 0x0F 
    # Checksum: 0xB8 (0x00 0x0B) = 0 + 11 + 0 + 173 = 184
    # End: 0x07 0x0F

    data = serial_command(b'\x07\xF0\x00\x0B\x00\xB8\x07\x0F')

    if data == None:
        warning_msg('function get_fan_status could not get serial data')
    else:
        IntakeFanSpeed = int(data[7], 16)
        ExhaustFanSpeed = int(data[8], 16)  
        IntakeFanRPM = int(1875000 / int(''.join([str(int(data[9], 16)), str(int(data[10], 16))])))
        ExhaustFanRPM = int(1875000 / int(''.join([str(int(data[11], 16)), str(int(data[12], 16))])))

        publish_message(msg='{ "idx" : ' +str(IDXIntakeFanSpeed) +str(', "nvalue" : 0, "svalue" :"') +str(IntakeFanSpeed) +str('"}'), mqtt_path='domoticz/in')
        publish_message(msg='{ "idx" : ' +str(IDXExhaustFanSpeed) +str(', "nvalue" : 0, "svalue" :"') +str(ExhaustFanSpeed) +str('"}'), mqtt_path='domoticz/in')
        publish_message(msg='{ "idx" : ' +str(IDXIntakeFanRPM) +str(', "nvalue" : 0, "svalue" :"') +str(IntakeFanRPM) +str('"}'), mqtt_path='domoticz/in')
        publish_message(msg='{ "idx" : ' +str(IDXExhaustFanRPM) +str(', "nvalue" : 0, "svalue" :"') +str(ExhaustFanRPM) +str('"}'), mqtt_path='domoticz/in')

        debug_msg('IntakeFanSpeed {0}%, ExhaustFanSpeed {1}%, IntakeAirRPM {2}, ExhaustAirRPM {3}'.format(IntakeFanSpeed,ExhaustFanSpeed,IntakeFanRPM,ExhaustFanRPM))
    
def get_filter_status():
    # 0x07 0xF0 0x00 0xD9 0x00 0x86 0x07 0x0F 
    # Start: 0x07 0xF0
    # Command: 0x00 0xD9
    # Number data bytes: 0x00
    # Checksum: 0x86 (0x00 0xD9) = 0 + 217 + 0 + 173 = 390
    # End: 0x07 0x0F

    data = serial_command(b'\x07\xF0\x00\xD9\x00\x86\x07\x0F')

    if data == None:
        warning_msg('get_filter_status function could not get serial data')
    else:
        if int(data[18], 16) == 0:
            FilterStatus = 'Ok'
        elif int(data[18], 16) == 1:
            FilterStatus = 'Full'
        else:
            FilterStatus = 'Unknown'
        
        publish_message(msg='{ "idx" : ' +str(IDXFilter) +str(', "nvalue" : 0, "svalue" :"') +str(FilterStatus) +str('"}'), mqtt_path='domoticz/in')
        debug_msg('FilterStatus: {0}'.format(FilterStatus))
    
def recon():
    try:
        mqttc.reconnect()
        info_msg('Successfull reconnected to the MQTT server')
        topic_subscribe()
    except:
        warning_msg('Could not reconnect to the MQTT server. Trying again in 10 seconds')
        time.sleep(10)
        recon()
        
def topic_subscribe():
    try:
        mqttc.subscribe("domoticz/out", 0)
        info_msg('Successfull subscribed to the MQTT topics')
    except:
        warning_msg('There was an error while subscribing to the MQTT topic(s), trying again in 10 seconds')
        time.sleep(10)
        topic_subscribe()

def on_connect(client, userdata, flags, rc):
    topic_subscribe()
    
def on_disconnect(client, userdata, rc):
    if rc != 0:
        warning_msg('Unexpected disconnection from MQTT, trying to reconnect')
        recon()

### 
# Main
###
debug = False

# Connect to the MQTT broker
mqttc = mqtt.Client('whr930')
mqttc.username_pw_set(username="myuser",password="mypass")

# Define the mqtt callbacks
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.on_disconnect = on_disconnect

# Connect to the MQTT server
mqttc.connect('127.0.0.1', port=1883, keepalive=45)

# Open the serial port
ser = serial.Serial(port = '/dev/YPort', baudrate = 9600, bytesize = serial.EIGHTBITS, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE)

mqttc.loop_start()
while True:
    try:
        get_temp()
        get_ventilation_status()
        get_filter_status()
        get_fan_status()

        time.sleep(10)
        pass
    except KeyboardInterrupt:
        mqttc.loop_stop()
        ser.close()
        break
    
# End of program

