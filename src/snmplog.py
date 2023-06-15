"""
Set this script up as an snmp trap handler to log any incoming traps to a log file. Useful for determing the payload of individual traps.

Example trap handler:
traphandle default /usr/bin/python3 /path/to/snmplog.py
"""
import os
import os.path
import sys
from datetime import datetime
import utils as utils

# create the log directory
if(not os.path.exists(utils.LOG_DIR)):
    os.mkdir(utils.LOG_DIR)

# parse the trap from snmptrapd
trap = utils.parse_snmp(sys.stdin.readlines())

# write to the log file - format is DATE [IP] OID: PAYLOAD
now = datetime.now()
with open(os.path.join(utils.LOG_DIR, 'snmp.log'), 'a') as log_file:
    log_file.write(f"{now.strftime('%m-%d-%Y %H:%M:%S')} [{trap['sender_ip']}] OID {trap['oid']}: {trap['payload']}\n")
