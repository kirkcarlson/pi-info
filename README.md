# pi-info -- Retrieve Infomation about the Raspberry Pi
A python program to return Raspberry Pi system information to the standard output. It has
options for controlling the output.

The intended uses of this program are to retreive system information that can be saved
to track a fleet of Raspberry Pis and to get internal operating parameters to be collected using MQTT with the companion project text-to-MQTT.

Usage from command line:
```
python piiinfo.py [-0] [-a] [-i] [-I] [-v] [-V] [-s] [-t] [--debug] [-h] [--help]
```
where:

-0 is to turn off all selections

-a is to turn on all selections

-i is to include all Pi identifiers

-I is to include all system (Linux) identifiers

-v is to include all Pi variables

-s is to include Sense Hat weather measurements

-t is to use MQTT topic formatting rather than human formatting

--debug to print debug message

-h or --help is to print this command summary


default is to print system and Pi variables

Note program must be run with superuser privleges if the Sense Hat measurements are to be accessed.
```
  
Usage for the periodic sending of MQTT messages, do something like:
```
  sudo crontab -e
  # and add the following to the end of the file:
  */5 * * * * /usr/bin/python /home/pi/bin/piinfo.py -s -i | /usr/python/bin/txt2mqtt.py
```
  
Usage for logging startups to the /boot directory do something like:
```
  /usr/bin/python /home/pi/bin/piinfo -i)>> /boot/machine
  ... this is a bit more complex... it should be an init.d process... to kick out the above message when starting and
  and to note graceful shutdowns as well.
```
  
The test.sh file is used to test the parameter processing of the program. Add new tests as necessary.

