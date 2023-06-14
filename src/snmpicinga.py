import argparse
import jinja2
import json
import os.path
import requests
import sys
import yaml
import utils as utils
from cerberus import Validator
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning,InsecurePlatformWarning,SNIMissingWarning

config = None  # yaml config file

#disable insecure request warnings
requests.packages.urllib3.disable_warnings((InsecureRequestWarning,InsecurePlatformWarning,SNIMissingWarning))

def send_to_icinga(host, service, trap):
    # setup the url and basic http auth
    url = f"https://{config['icinga']['ip']}:5665/v1/actions/process-check-result"
    basic = HTTPBasicAuth(config['icinga']['username'], config['icinga']['password'])

    # data payload
    data = {"type": "Service", "filter": f"host.name==\"{host}\" && service.name==\"{service}\"",
            "exit_status": trap['return_value'], "plugin_output": trap['payload'],
            "check_source": "spiderman", "pretty": True }

    try:
        r = requests.post(url, headers={"Accept":"application/json"}, auth=basic, json=data, verify=False)

        # get the results as a dict
        if(r.ok):
            results = r.json()
            print(results['results'][0]['status'])
        else:
            print("error with http")
    except:
        print("error with request")

def parse_payload(payload, type='value'):
    result = payload  # for value types just return payload

    if(type == 'csv'):
        # break on commas into an array
        result = payload.split(',')

        # do a little cleanup on the values
        result = list(map(lambda v: v.strip().replace('"',''), result))

    elif(type == 'json'):
        result = json.loads(payload)

    return result

def find_trap_definition(trap_info, traps):
    # go through all the traps until we find a match
    for t in traps:
        if(t['snmp']['host'] == trap_info['sender_ip'] and t['snmp']['oid'] == trap_info['oid']):
            return t

    return None

def render_template(jinja_env, template_string, payload, return_bool=True):
    # evaulate the template and return the result
    template = jinja_env.from_string(template_string)
    result = template.render(payload=parsed_payload)

    if(return_bool):
        # jinja returns True/False string
        return result.lower() == 'true'
    else:
        return result

def validate_schema():
    with open(os.path.join(utils.CONFIG_DIR, 'schema.yaml'), 'r') as file:
        schema = yaml.safe_load(file)

    v = Validator(schema)
    if(not v.validate(config, schema)):
        print("Error - configuration file syntax is invalid")
        print(str(v.errors))
        sys.exit(2)

parser = argparse.ArgumentParser(description='SNMP to Icinga')
parser.add_argument('-c', '--config', default="config.yaml",
                    help='Path to YAML config file')
parser.add_argument('-t', "--test", action='store_true',
                    help="Validate the config file and exit")
args = parser.parse_args()

# load the yaml config file
with open(os.path.join(utils.CONFIG_DIR, args.config), 'r') as file:
    config = yaml.safe_load(file)

# validate the config file
validate_schema()

if(args.test):
    # exit after this
    print("Configuration file is valid")
    sys.exit(0)

# parse the trap
trap_snmp = utils.parse_snmp(sys.stdin.readlines())

# check if we have a match
trap_config = find_trap_definition(trap_snmp, config['traps'])

# confirm we have a match for this trap
if(trap_config is not None):
    # convert the trap payload based on the type
    parsed_payload = parse_payload(trap_snmp['payload'], trap_config['snmp']['payload_type'])

    return_codes = trap_config['icinga']['return_code']
    jinja_env = jinja2.Environment()

    # render return code starting with ok
    if(render_template(jinja_env, return_codes['ok'], parsed_payload)):
        trap_snmp['return_value'] = 0
    elif(render_template(jinja_env, return_codes['warning'], parsed_payload)):
        trap_snmp['return_value'] = 1
    elif(render_template(jinja_env, return_codes['critical'], parsed_payload)):
        trap_snmp['return_value'] = 2
    else:
        trap_snmp['return_value'] = 3

    # send to icinga
    send_to_icinga(trap_config['icinga']['host'], trap_config['icinga']['service'], trap_snmp)
else:
    print(f"No match for host {trap_snmp['sender_ip']} and OID {trap_snmp['oid']}")
