# SNMP To Icinga

This is a bridge to configure SNMP traps that should be updated in Icinga via a passive check. This is meant to be highly configurable and work multiple types of SNMP traps without writing custom handlers for them all.

## Install

This script is meant to work in conjunction with [snmptrapd](https://net-snmp.sourceforge.io/docs/man/snmptrapd.html). Having that up and running is a pre-requsite. There are numerous guides depending on your system to get this going.

Once _snmptrapd_ is confirmed working, clone this repo somewhere local on the same system.

```
git clone https://github.com/eau-claire-energy-cooperative/snmp-to-icinga.git
sudo pip3 install .

```

Once built you can setup one of the two scripts as a trap handler.

## Usage

### SNMP Logging

If you just want to log SNMP traps to a file for review this can be done by setting up the `snmplog.py` file as a trap handler. Below is an example for the `snmptrapd.conf` file.

```

```

Once setup the script will take any traps forwarded and log the time, sender IP, OID, and trap value to a log file. This is useful for if you want to test if a trap is coming through and what the payload values actually are. This can help determine the rules for configuring the Icinga service.

### SNMP To Icinga

To setup the full SNMP trap to Icinga integration you will need to:

1. Setup the `snmpicinga.py` script as a trap handler. See the example below.
2. Generate a config file that contains the SNMP trap and Icinga information needed to parse the trap and return the service status.

```

```

Once configured the script will load the config file and match the sender and OID to one of the configured values. If one can't be found the script exists. The SNMP payload is parsed according to the directives so that an OK, WARNING, CRITICAL, or UNKNOWN status can be sent to Icinga.

## Config File

A YAML configuration file must be created that contains the Icinga and SNMP trap information. Multiple SNMP traps can be defined in the same file.

```

```

The configuration file will be validated at runtime to make sure it is valid. You can test this manually by adding the `--test` flag.

```
python3 snmptoicinga.py --config config.yaml --test
```

### Trap Parsing

Trap parsing can be done by specifying the `payload_type`. This can be either a single `value`, a `json` payload, or a `csv` payload. Normal values are returned as is. JSON values are parsed with `json.loads` and CSV values are converted to an array.

### Return Codes

Icinga expects a return code corresponding to either OK, WARNING, CRITICAL, or UNKNOWN. This is created by evaluating the SNMP payload. In the __return_codes__ section of the configuration file are specified the rules for evaluating each return type. These are processed in order from OK to CRITICAL. The OK type is required but WARNING and CRITICAL return types are optional. Using Jinja syntax each statement must evaluate to a true/false value. Returning `True` means that this return value will be sent to Icinga. If no statement is found to be True, then an UNKNOWN return code is given.

The SNMP payload is available as a variable called `payload`. For CSV type payloads you can access each with array notation (`payload[0]`). For JSON type payloads you can use JSON notation (`payload['key']`).

A few examples:

```
# simple condition evaluation
ok: "{{ payload == 'value' }}"

# more complicated CSV payload
ok: "{{ payload[1] == 'value' }}"

# advanced jinja evaluation using JSON payload
# here different values equal True based on the name of the sensor
ok: >-
  {% if payload['sensor'] == 'sensor 1' %}
    {{ payload['sensor_value'] == 'OK' }}
  {% elif payload['sensor'] == 'sensor 2' %}
    {{ payload['sensor_value'] == 'NOT OK' }}
  {% else %}
    False
  {% endif %}
```

### Other Output

By default the raw SNMP payload data is also sent to Icinga as a string as the _plugin output_ information. You can format this output in a template as well by specifying a `plugin_output` value in the config file.

Similarly _performance data_ can also be sent by specifying a `performance_data` template. Keep in mind that performance data must conform to the [Nagios standard](https://nagios-plugins.org/doc/guidelines.html#PLUGOUTPUT) in order for it to work correctly in Icinga. 
