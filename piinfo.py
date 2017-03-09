#!/usr/bin/python
'''
piinfo.py -- print information available to the Pi to standard output

changing the use of this a bit
purposes:
 - send CPU, GPU and SenseHat measurements
 - send system information
 - print system information
 - save system information to special place in boot folder
   - this could just be a redirection of the print function
   - archive of past information could be a shell routine
     - change the name to name.date
'''
#
### IMPORTS ###
#
import sys
import os
import getopt
import subprocess
import re
import socket
from sense_hat import SenseHat
from RPi import GPIO
from parse import *
from string import split
from math import floor


#
### Constants ###
#
routerIPaddress = "192.168.2.1"


#
### GLOBALS ###
#
DEBUG = False
topic = False


#
### FUNCTIONS ###
#
def printCommandSummary():
  print "Usage: python piiinfo.py [-0] [-a] [-i] [-I] [-v] [-V] [-s] [-t] [--debug] [-h] [--help]"
  print "  -0 is to turn off all selections"
  print "  -a is to turn on all selections"
  print "  -i is to include all Pi identifiers"
  print "  -I is to include all system (Linux) identifiers"
  print "  -v is to include all Pi variables"
  print "  -s is to include sense hat weather measurements"
  print "  -t is to use MQTT topic formatting rather than human formatting"
  print "  --debug to print debug messages
  print "  -h or --help is to print this command summary"
  print "\n  default is to print system and Pi variables


def getHostname ():
  f = open( "/etc/hostname", "r")
  s = f.readline().strip()
  return s


def getSDcardnumber ():
  try:
    f = open( "/boot/sdcardnumber", "r")
    s = f.readline().strip()
  except:
    s = "Not set up"
  return s


def getDate ():
  s = subprocess.check_output(["/bin/date"])
  return s


def getGPUTemperature ():
  try:
    s = subprocess.check_output(["/opt/vc/bin/vcgencmd","measure_temp"])
    return s.split('=')[1][:-3]
  except:
    return "0"


def getCPUTemperature ():
  try:
    s = (open('/sys/class/thermal/thermal_zone0/temp').read())
    return  s[:2] + '.' + s[2]
  except:
    return "0" 


def getUpTime ():
  try:
    s = subprocess.check_output(["/usr/bin/uptime","-p"])
    return s.strip()
  except:
    return ""


def getUpSince ():
  try:
    s = subprocess.check_output(["/usr/bin/uptime","--since"])
    dt= parse ("{date:S} {time:S}",s)

    # convert the local time to a datetime string with daylight savings as appriate for current time zone
    s =  subprocess.check_output(["/bin/date","+%FT%T%z","--date=" + dt['date'] + ' ' + dt['time'] ])
    dt = parse ("{:S}\n",s)
    return dt[0]
  except:
    return "0"


def getIPaddress():
  # returns the primary IP address for this node
  s = subprocess.check_output(["/sbin/ip", "route", "get", routerIPaddress])
  s = re.search ('.*src ([0-9.]*).*', s)
  if s is not None:
    s = s.group(1)
  else:
    s = "Unknown"
  return s


def getLoads ():
  '''
    parses the output of 'uptime':
       09:50:09 up 25 days, 18:55,  2 users,  load average: 0.02, 0.01, 0.00
       16:00:51 up 26 days,  1:06,  2 users,  load average: 0.00, 0.00, 0.00
    into the load over the last 1, 5 and 15 minutes
  '''
  try:
    s = subprocess.check_output(["/usr/bin/uptime"])
    loads = parse("{}load average: {load1min:f}, {load5min:f}, {load15min:f}", s)
    return {'load1min':loads['load1min'], 'load5min':loads['load5min'], 'load15min':loads['load15min']}
  except:
    return {'load1min':0, 'load5min':0, 'load15min':0}


def getSerial ():
  # get the serial number from the Pi
  s = subprocess.check_output(["/bin/cat", "/proc/cpuinfo"])
  serial = parse("{}Serial{:s}:{:s}{:S}", s)[-1] # extract the serial number from last field
  return serial


def getDistribution ():
  # get the distribution version identification
  s = subprocess.check_output(["/usr/bin/lsb_release", "-d"])
  s = parse("Description:\t{}\n", s)[0] # extract the description field without label
  return s


def getKernal ():
  # get the kernal version identification
  s = subprocess.check_output(["/bin/uname", "-a"])
  s = parse("{}\n", s)[0] # remove new line
  return s


def getSessions ():
  # return the number of sessions
  s = subprocess.check_output(["/usr/bin/who", "--count"])
  # returns line with names, line with users=x
  s = split( s, "\n")
  s = split( s[1], "=")
  s = s[1]
  return s


def getIPaddresses( ):
  # get the IP addresses for each interface used

  res = []
  s = subprocess.check_output(["/sbin/ifconfig"])
  s = split( s, "\n\n") # one string per interface
  for line in s:
    item = parse("{:S}{}inet addr:{:S}{}", line) # test for line with media access (MAC) address
    if item is not None:
      res.append ((item[0], item[2]))
  return res


def getMACaddresses( ):
  # get the ethernet hardware media access (MAC) addresses for each interface used

  res = []
  output = subprocess.check_output(["/sbin/ifconfig"])
  output = split( output, "\n")
  for line in output:
    line = parse("{:S}{:s}Link encap:{}HWaddr{}{:S}{}", line) # test for line with media access (MAC) address
    if line is not None:
      res.append ((line[0], line[4]))
  return res

def getMemory ():
  '''
    parses the output of 'free -h':
             total       used       free     shared    buffers     cached
Mem:          862M       415M       446M        48M        83M       232M
-/+ buffers/cache:        99M       762M
Swap:          99M         0B        99M
  '''
  try:
    s = subprocess.check_output(["/usr/bin/free","-h"])
    memory = parse("{}Mem:{:s}{total:S}{:s}{used:S}{:s}{free:S}{}Swap:{:s}{swapTotal:S}{:s}{swapUsed:S}{:s}{swapFree:S}{}", s)
    return {'total':memory['total'],
            'used':memory['used'],
            'free':memory['free'],
            'swapTotal':memory['swapTotal'],
            'swapUsed':memory['swapUsed'],
            'swapFree':memory['swapFree']}
  except:
    return {'total':0, 'used':0, 'free':0, 'swapTotal':0, 'swapUsed':0, 'swapFree':0}



def getDiskUsed (dir):
  '''
    parses the output of 'df <dir>':
Filesystem     1K-blocks    Used Available Use% Mounted on
/dev/root        7512304 4738988   2413368  67% /
  '''
  try:
    s = subprocess.check_output(["/bin/df",dir])
    diskUsed = parse("{}Use%{}{:S}%{}", s)[2]
    return diskUsed
  except:
    return 0


def getUSBdevices():
  s = subprocess.check_output(["/usr/bin/lsusb"])
  # output looks like:
  #   Bus 001 Device 002: ID 0424:9512 Standard Microsystems Corp. 
  #   Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
  #   Bus 001 Device 003: ID 0424:ec00 Standard Microsystems Corp. 
  #   Bus 001 Device 004: ID 06cd:0121 Keyspan USA-19hs serial adapter
  s = split( s, "\n")

  pattern = re.compile ('Bus ([0-9]*) Device ([0-9]*): ID ([0-9a-fA-F:]*)(.*)')
  result = []
  for line in s:
    if line is not "":
      fields = pattern.match( line)
      if fields is None:
        result.append ({'bus':"?", 'device':"?", 'id':"?", 'description':"?"})
      else:
        result.append ({'bus':fields.group(1),
                        'device':fields.group(2),
                        'id':fields.group(3),
                        'description':fields.group(4).strip()})
  return result


def getHttpdVersion():
  path = "/usr/bin/httpd"
  if os.path.isfile(path): # apache is installed
    s = subprocess.check_output([path, "-v", "2>/dev/null"])
    # outputs something like:
    #  Server version: Apache/2.4.18 (Unix)
    #  Server built:   Feb 20 2016 20:03:19
    s  = parse( "{}version: {:S}{}", s)[1]
  else:
    s = "Not installed"
  return s

def getPHPversion():
  # returns the version of PHP, if installed
  phpPath = '/usr/bin/php'
  if os.path.isfile(phpPath): # PHP is installed
    s = subprocess.check_output([phpPath, "-v", "2>/dev/null"])
    # returns something like: PHP 5.6.27-0+deb8u1 (cli) (built: Oct 24 2016 18:22:27) 
    s  = parse( "PHP {:S}{}", s)[0]
  else:
    s = "Not installed"
  return s


def getMySQLversion():
  # returns the version of mySQL, if installed
  mySQLpath = '/usr/bin/mysql'
  result = ("Not installed", "Not installed")
  if os.path.isfile(mySQLpath): # mySQL is installed
    s = subprocess.check_output([mySQLpath, "--version", "2>/dev/null"])
    # returns something like: mysql  Ver 14.14 Distrib 5.5.52, for debian-linux-gnu (armv7l) using readline 6.3
    s = re.search ('.*Ver ([0-9.A-Za-z-]*).*Distrib ([0-9.a-zA-Z-]*).*', s)
    if s is not None:
      result = ( s.group(1), s.group(2))
  return result


def getVoltage (type):
  try:
    s = subprocess.check_output(["/usr/bin/vcgencmd", "measure_volts", type])
    voltage  = parse("Volt={}V", s)[0]
    return voltage
  except:
    return 0


def pStat (humanDescriptor, topicDescriptor, value):
  if topic and topicDescriptor != "": 
     print topicDescriptor + ":", value
  else:
     print humanDescriptor + ":", value


#
### MAIN ###
#
def main(argv):
   global topic

   # setup defaults
   includingSystemIdentifiers = False
   includingPiIdentifiers = False
   includingSystemVariables = True
   includingPiVariables = True
   includingSenseHatVariables = False
   topic = False

   if DEBUG:
     print "Arguments:", argv

   #process command line
   try:
      opts, args = getopt.getopt(argv,"0aIiVvsth",["help","debug"])
   except getopt.GetoptError:
      printCommandSummary()
      sys.exit(2)
   for opt, arg in opts:
      if opt == "-0":
        includingSystemIdentifiers = False
        includingPiIdentifiers = False
        includingSystemVariables = False
        includingPiVariables = False
        includingSenseHatVariables = False
      if opt == "-a":
        includingSystemIdentifiers = True
        includingPiIdentifiers = True
        includingSystemVariables = True
        includingPiVariables = True
        includingSenseHatVariables = True
      if opt == "-I":
        includingSystemIdentifers = True
      if opt == "-i":
        includingPiIdentifers = True
      elif opt == "-V":
        includingSystemVariables = True
      elif opt == "-v":
        includingPiVariables = True
      elif opt == "-s":
        includingSenseHatVariables = True
      elif opt == "-t":
        topic = True
      elif opt in ("--debug"):
        debug = True
      elif opt in ("--help", "-h"):
        printCommandSummary()
        sys.exit(2)

   if DEBUG:
     print 'Parameters are:'
     print '  includingSystemIdentifiers is', includingSystemIdentifiers
     print '  includingSystemVariables is', includingSystemVariables
     print '  includingPiIdentifiers is', includingPiIdentifiers
     print '  includingPiVariables is', includingPiVariables
     print '  includingSenseHatVariables is', includingPiVariables

   # want to to test presence of SenseHAT to skip 
   senseHatIsPresent = False
   SenseHAT = re.compile ('.*Sense HAT firmware version')
   for line in subprocess.check_output(["/bin/dmesg"]).split("\n"):
     if SenseHAT.match( line) != None:
       senseHatIsPresent = True
       sense = SenseHat()
       break

   if includingSystemIdentifiers:
     pStat( "Hostname",                   "hostname",         getHostname())
     pStat( "SD card number",             "SDcardNumber",     getSDcardnumber())
     pStat( "Run at",                     "pi/time",          getDate().strip())

     pStat( "P1revision",                 "pi/p1rev",         GPIO.RPI_INFO['P1_REVISION'])
     pStat( "revision",                   "pi/rev",           GPIO.RPI_INFO['REVISION'])
     pStat( "Distribution",               "pi/distribution",  getDistribution())
     pStat( "Kernal",                     "pi/kernal",        getKernal())
     pStat( "Pi RAM",                     "pi/ram",           GPIO.RPI_INFO['RAM'])
     pStat( "Pi Type",                    "pi/type",          GPIO.RPI_INFO['TYPE'])
     pStat( "Processor",                  "pi/processor",     GPIO.RPI_INFO['PROCESSOR'])
     pStat( "Manufacturer",               "pi/manufacturer",  GPIO.RPI_INFO['MANUFACTURER'])
     pStat( "PHP version",                "phpVersion",       getPHPversion())
     pStat( "apache version",             "apacheVersion",    getHttpdVersion())
     pStat( "mySQL version",              "mySQLversion",     getMySQLversion()[0])
     pStat( "mySQL distribution",         "mySQLdistro",      getMySQLversion()[1])

   if includingPiIdentifiers:
     pStat( "Serial Number",              "pi/serial",        getSerial())
     pStat( "IP address",                 "IPaddr",           getIPaddress())
     for connection in getIPaddresses():
       pStat( connection[0] + " IP address", connection[0] + "/IPaddr", connection[1] )
     for connection in getMACaddresses():
       pStat( connection[0] + " MAC address", connection[0] + "/MACaddr", connection[1] )
     for device in getUSBdevices():
       pStat( "USB bus" + device['bus'] +
              " device" + device['device'] +
              " ID",
                                          "USB/bus" + device['bus'] +
                                          "/device" + device['device'] +
                                          "/ID",
                                                              device['id'])
       pStat( "USB bus" + device['bus'] +
              " device" + device['device'] +
              " description",
                                          "USB_bus" + device['bus'] +
                                          "/device" + device['device'] +
                                          "/description",
                                                              device['description'])
     # should include HATs

   if includingSystemVariables:
     pStat( "upTime",                     "",                 getUpTime())
     pStat( "upSince",                    "",                 getUpSince())

     pStat( "Sessions",                   "sessions",         getSessions())
     loads = getLoads()
     pStat( "Load 1 min",                 "load/1min",        loads['load1min'])
     pStat( "Load 5 min",                 "load/5min",        loads['load5min'])
     pStat( "Load 15 min",                "load/15min",       loads['load15min'])

     pStat( "root disk usage%",           "disk/usedPercent", getDiskUsed('/'))
     pStat( "boot disk usage%",           "boot/usedPercent", getDiskUsed('/boot'))

     memory = getMemory()
     pStat( "Memory Total",               "mem/total",        memory['total'])
     pStat( "Memory Used",                "mem/total",        memory['used'])
     pStat( "Memory Free",                "mem/free",         memory['free'])

     pStat( "Swap Total",                 "swap/total",       memory['swapTotal'])
     pStat( "Swap Used",                  "swap/used",        memory['swapUsed'])
     pStat( "Swap Free",                  "swap/free",        memory['swapFree'])

   if includingPiVariables:
     pStat( "Voltage in core",            "core/volt",        getVoltage( 'core'))
     pStat( "Voltage in sdram_c",         "SDRAMC/volt",      getVoltage( 'sdram_c'))
     pStat( "Voltage in sdram_i",         "SDRAMI/volt",      getVoltage( 'sdram_i'))
     pStat( "Voltage in sdram_p",         "SDRAMP/volt",      getVoltage( 'sdram_p'))
     pStat( "CPU Temperature",            "CPU/temp",         getGPUTemperature())
     pStat( "GPU Temperature",            "GPU/temp",         getCPUTemperature())

   if includingSenseHatVariables and senseHatIsPresent:
     pStat( "Temperature from humidity",  "humid/temp",       floor(sense.get_temperature_from_humidity()*10) /10)
     pStat( "Temperature from pressure",  "pressure/temp",    floor(sense.get_temperature_from_pressure()*10) /10)
     pStat( "Humidity",                   "humidity",         floor(sense.get_humidity()*10) /10)
     pStat( "Pressure",                   "pressure",         floor(sense.get_pressure()*10) /10)


if __name__ == "__main__":
  main(sys.argv[1:])
