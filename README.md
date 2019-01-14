Interface with a StorkAir WHR930 on Domoticz

Publish every 10 seconds the status on a MQTT Domoticz/in topic
Listen on MQTT topic for commands to set the ventilation level

Version 0.8 by albert[@]hakvoort[.]co

[based on code from Mosibi]



todo :
- set bypass temperature
- check on faulty messages
- serial check


The following packages are needed:

- sudo apt-get install python3-serial python3-pip python3-yaml

- sudo pip3 install paho-mqtt


Add the following dummy Devices in Domoticz :

- OutsideAirTemp		# temperature

- SupplyAirTemp	  	# temperature

- ReturnAirTemp		# temperature

- ExhaustAirTemp		# temperature

- IntakeFanSpeed		# text

- ExhaustFanSpeed		# text

- IntakeFanRPM		# text

- ExhaustFanRPM		# text

- IntakeFanActive		# text

- FanLevel			# text

- Filter				# text

- Selector			# selector 0=auto 10=away 20=low 30=middle 40=high !! Depends on model/CO2 sensor etc !!


After installing the dependencies, clone this repository and modify the settings in src/whr930.py and run sudo make install.

$ git clone https://github.com/AlbertHakvoort/StorkAir-Zehnder-WHR-930-Domoticz-MQTT.git
$ vi src/whr930.py
$ sudo make install

edit the whr930.py and fill the IDX's, serialport and MQTTserver address.

- SerialPort='/dev/YPort'		# Serial port WHR930
- MQTTServer='127.0.0.1'		# IP MQTT broker

To test if everything is working fine :

python3 /usr/local/bin/whr930.py

To start the whr930 as service :

$ sudo systemctl start whr930.service
