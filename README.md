# SNMP To Icinga

This is a bridge to configure SNMP traps that should be updated in Icinga via a passive check. This is meant to be highly configurable and work multiple types of SNMP traps without writing custom handlers for them all.

## Install

This script is meant to work in conjunction with [snmptrapd](https://net-snmp.sourceforge.io/docs/man/snmptrapd.html). Having that up and running is a pre-requsite. There are numerous guides depending on your system to get this going.

```

sudo pip3 install .

```
## Usage

### SNMP Logging

If you just want to log SNMP traps to a file for review this can be done by setting up the `snmplog.py` file as a trap handler. Below is an example for the `snmptrapd.conf` file.

```

```

Once setup the script will take any traps forwarded and log the time, sender IP, OID, and trap value to a log file. This is useful for if you want to test if a trap is coming through and what the payload values actually are. This can help determine the rules for configuring the Icinga service. 
