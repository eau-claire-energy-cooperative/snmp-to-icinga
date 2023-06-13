"""
Set this script up as an snmp trap handler to log any incoming traps to a log file. Useful for determing the payload of individual traps.

Example trap handler:
traphandle default /usr/bin/python3 /path/to/snmplog.py
"""
import os
import os.path
import re
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
LOG_DIR = os.path.join(SCRIPT_DIR, 'tmp')

# create the log directory
if(not os.path.exists(LOG_DIR)):
    os.mkdir(LOG_DIR)

# read in the full trap from snmptrapd
trap = sys.stdin.readlines()

# network info is index 1 and payload is at the end
network_info = str(trap[1]).strip()
payload = str(trap[len(trap) - 1]).strip()

# get the sender's IP (first match)
sender = re.search('((\d+)\.){3}(\d+)', network_info).group()

# find the oid
oid = re.search('iso(\.([\d]{0,}))+', payload).group()
payload = payload[len(oid) + 1:]

# write to the log file - format is DATE [IP] OID: PAYLOAD
now = datetime.now()
with open(os.path.join(LOG_DIR, 'snmp.log'), 'a') as log_file:
  log_file.write(f"{now.strftime('%m-%d-%Y %H:%M:%S')} [{sender}] OID {oid}: {payload}\n")
