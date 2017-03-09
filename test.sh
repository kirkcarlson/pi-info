#!/bin/bash
# shell program to test various argument variations of sysinfo
# the output of the program should be further examined for errors


# help text tests
python sysinfo.py
 if [ $? -ne 0 ]; then echo "Failed Test 1"; exit; fi
python sysinfo.py -b
 if [ $? -ne 2 ]; then echo "Failed Test 1.1"; exit; fi
python sysinfo.py --BAD
 if [ $? -ne 2 ]; then echo "Failed Test 1.2"; exit; fi
python sysinfo.py -h
 if [ $? -ne 2 ]; then echo "Failed Test 2"; exit; fi
python sysinfo.py --help
 if [ $? -ne 2 ]; then echo "Failed Test 3"; exit; fi

# MQTT parameter tests
python sysinfo.py --qos=1 --retain -t topic
 if [ $? -ne 0 ]; then echo "Failed Test 4"; exit; fi
python sysinfo.py -m localhost
 if [ $? -ne 0 ]; then echo "Failed Test 5"; exit; fi
python sysinfo.py --mqtt=localhost --qos=1
 if [ $? -ne 0 ]; then echo "Failed Test 6"; exit; fi
python sysinfo.py --mqtt=localhost --qos=1 --retain
 if [ $? -ne 0 ]; then echo "Failed Test 7"; exit; fi
python sysinfo.py --mqtt=localhost --qos=1 --retain --topic=topic
 if [ $? -ne 0 ]; then echo "Failed Test 8"; exit; fi
python sysinfo.py -m localhost -q 1 -k -t topic
 if [ $? -ne 0 ]; then echo "Failed Test 9"; exit; fi

# printing tests
sudo python sysinfo.py -s
 if [ $? -ne 0 ]; then echo "Failed Test 10"; exit; fi
python sysinfo.py -i
 if [ $? -ne 0 ]; then echo "Failed Test 11"; exit; fi
python sysinfo.py -I
 if [ $? -ne 0 ]; then echo "Failed Test 12"; exit; fi
sudo python sysinfo.py -a
 if [ $? -ne 0 ]; then echo "Failed Test 13"; exit; fi
sudo python sysinfo.py -v
 if [ $? -ne 0 ]; then echo "Failed Test 14"; exit; fi

# MQTT tests
sudo python sysinfo.py -s -m localhost
 if [ $? -ne 0 ]; then echo "Failed Test 15"; exit; fi
python sysinfo.py -i -m localhost
 if [ $? -ne 0 ]; then echo "Failed Test 16"; exit; fi
python sysinfo.py -I -m localhost
 if [ $? -ne 0 ]; then echo "Failed Test 17"; exit; fi
sudo python sysinfo.py -a -m localhost
 if [ $? -ne 0 ]; then echo "Failed Test 18"; exit; fi
sudo python sysinfo.py -v -m localhost
 if [ $? -ne 0 ]; then echo "Failed Test 19"; exit; fi
