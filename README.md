# SNMP To Icinga

This is a bridge to configure SNMP traps sent from [snmptrapd](https://net-snmp.sourceforge.io/docs/man/snmptrapd.html) so they can update [Icinga](https://icinga.com/) services via a passive check. This is meant to be highly configurable and work with multiple types of SNMP traps without writing custom handlers for them all.

## Table Of Contents

- [Background](#background)
- [Install](#install)
- [Usage](#usage)
  - [SNMP Logging](#snmp-logging)
  - [SNMP To Icinga](#snmp-to-icinga)
- [Config File](#config-file)
  - [Trap Parsing](#trap-parsing)
  - [Return Codes](#return-codes)
  - [Other Output](#other-output)
- [License](#license)

## Background

[Icinga](https://icinga.com/) is a monitoring tool, similar to Nagios, that can perform both active and passive checks on hosts and services. Active checks are initiated from the Icinga daemon and return a response code (OK, WARNING, CRTICIAL, or UNKNOWN). Passive checks send data to Icinga from an external script or trigger. For backwards compatibility Icinga uses the same return codes and outputs as Nagios so many of the same scripts are interchangeable.

One common method of getting information from a remote host is to use [SNMP](https://en.wikipedia.org/wiki/Simple_Network_Management_Protocol). SNMP can be queried via an active service check. It also has the ability, on some devices, to send notifications (SNMP Traps) to a remote host. Icinga cannot parse this trap information natively on it's own but it does have a web service capable of receiving passive check info in the proper format.

This script is an attempt to create a bridge, taking the SNMP Trap information and creating the payload Icinga needs for a service check. This is done by registering the script as a trap handler for __snmptrapd__ and intercepting the trap data. A config file is used to determine how to map the SNMP OID and it's payload to valid Icinga return code values. Multiple traps can be defined so one trap handler can handle multiple service checks.

## Install

This script is meant to work in conjunction with [snmptrapd](https://net-snmp.sourceforge.io/docs/man/snmptrapd.html) and Icinga. Having those up and running is a prerequisite. There are numerous guides depending on your system to get this going. In Icinga you must also create an [API user](https://icinga.com/docs/icinga-2/latest/doc/09-object-types/#apiuser) with permissions to process check results via the API.

Once you're ready, clone this repo somewhere local on the __same system as snmptrapd__.

```
git clone https://github.com/eau-claire-energy-cooperative/snmp-to-icinga.git
sudo pip3 install .

```

Once built you can setup one of the two scripts as a trap handler.

## Usage

### SNMP Logging

If you just want to log SNMP traps to a file for review this can be done by setting up the `snmplog.py` file as a trap handler. Below is an example for the `snmptrapd.conf` file.

```
traphandle default /usr/bin/python3 /home/user/Git/snmp-to-icinga/src/snmplog.py
```

Once setup the script will take any traps forwarded and log the time, sender IP, OID, and trap value to a log file located in `tmp/snmp.log`. This is useful for if you want to test if a trap is coming through and what the payload values actually are. This can help determine the rules for configuring the Icinga service.

### SNMP To Icinga

To setup the full SNMP trap to Icinga integration you will need to:

1. Setup the `snmpicinga.py` script as a trap handler. See the example below.
2. Generate a config file that contains the SNMP trap and Icinga information needed to parse the trap and return the service status.

```
traphandle default /usr/bin/python3 /home/user/Git/snmp-to-icinga/src/snmpicinga.py --config demo.yaml
```

Once configured the script will load the config file and match the sender and OID to one of the configured values. If one can't be found the script exits. The SNMP payload is parsed according to the directives so that an OK, WARNING, CRITICAL, or UNKNOWN status can be sent to Icinga.

## Config File

A YAML configuration file must be created that contains the Icinga and SNMP trap information. The script looks for config files in the `config` directory, specifying a different absolute path will not work. Multiple SNMP traps can be defined in the same file.

```
# your icinga service information, including the API user and check source.
icinga:
  ip: 127.0.0.1
  username: api_user
  password: api_pass
  check_source: source_name
# define each of the traps below
traps:
  - name: "Test SNMP"
    # the SNMP sender and OID information
    snmp:
      host: 192.168.1.100
      oid: iso.3.6.1.4.1.8072.2.3.2.1
      payload_type: value
    # how to convert the trap to an icinga service
    icinga:
      host: garage_rack_door_sensor
      service: check_rack_door
      # Icinga plugin output is optional
      plugin_output: "The payload is: {{ payload }}"
      return_code:
        ok: {{ payload | int == 1 }}
        warning: {{ payload | int == 2 }}
        critical: {{ payload | int == 3 }}
```

The configuration file will be validated at runtime to make sure it is valid. You can confirm this manually by adding the `--validate` flag.

```
python3 snmptoicinga.py --config config.yaml --validate
```

### Trap Parsing

The SNMP payload is just a text string by default. Trap parsing can help turn this into a more useful data structure via the `payload_type` attribute. Payloads are stored for use later in the `payload` variable (see [return codes](#return-codes)). Supported values are:

* __value__ - this passes through the raw SNMP trap value
* __csv__ - parses the value into an array, splitting on commas like a CSV. This turns `Value1, Value2, Value3` into an array `['Value1', 'Value2', 'Value3']`.
* __json__ - parses the payload as JSON. This would turn the string `{"value1": 4, "value2": [1,2,3]}` into a [Python dict](https://docs.python.org/3/tutorial/datastructures.html#dictionaries) you can access directly.

### Return Codes

Icinga expects a return code corresponding to either OK, WARNING, CRITICAL, or UNKNOWN. This is created by evaluating the SNMP payload. In the __return_codes__ section of the configuration file are specified the rules for evaluating each return type. These are processed in order from OK to CRITICAL. The OK type is required but WARNING and CRITICAL return types are optional. Using [Jinja syntax](https://jinja.palletsprojects.com/en/3.1.x/templates/) each statement must evaluate to a true/false value. Returning `True` means that this return value will be sent to Icinga. If no statement is found to be True, then an UNKNOWN return code is given.

The SNMP payload is available as a variable called `payload`. For CSV type payloads you can access each with array notation (`payload[0]`). For JSON type payloads you can use dict notation (`payload['key']`).

A few examples:

```
# simple condition evaluation
ok: "{{ payload == 'value' }}"

# comparing to an integer
ok: "{{ payload | int == 123 }}"

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

By default the raw SNMP payload data is also sent to Icinga as a string in the _plugin output_ information. You can format this output in a template as well by specifying a `plugin_output` value in the config file.

Similarly _performance data_ can also be sent by specifying a `performance_data` template. Keep in mind that performance data must conform to the [Nagios standard](https://nagios-plugins.org/doc/guidelines.html#PLUGOUTPUT) in order for it to work correctly in Icinga.

## License

[GPLv3](https://github.com/eau-claire-energy-cooperative/snmp-to-icinga.git)
