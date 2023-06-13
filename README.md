# SNMP To Icinga

This is a bridge to configure SNMP traps that should be updated in Icinga via a passive check. This is meant to be highly configurable and work multiple types of SNMP traps without writing custom handlers for them all.

## Install

This script is meant to work in conjunction with [snmptrapd](https://net-snmp.sourceforge.io/docs/man/snmptrapd.html). Having that up and running is a pre-requsite. There are numerous guides depending on your system to get this going.
