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
from requests.packages.urllib3.exceptions import InsecureRequestWarning, InsecurePlatformWarning, SNIMissingWarning

config = None  # yaml config file

# disable insecure request warnings
requests.packages.urllib3.disable_warnings((InsecureRequestWarning, InsecurePlatformWarning, SNIMissingWarning))


def send_to_icinga(host, service, trap):
    # setup the url and basic http auth
    url = f"https://{config['icinga']['ip']}:5665/v1/actions/process-check-result"
    basic = HTTPBasicAuth(config['icinga']['username'], config['icinga']['password'])

    # data payload - https://icinga.com/docs/icinga-2/latest/doc/12-icinga2-api/#process-check-result
    data = {"type": "Service", "filter": f"host.name==\"{host}\" && service.name==\"{service}\"",
            "exit_status": trap['return_value'], "plugin_output": trap['plugin_output'],
            'performance_data': trap['performance_data'], "check_source": config['icinga']['check_source'],
            "pretty": False}

    try:
        r = requests.post(url, headers={"Accept": "application/json"}, auth=basic, json=data, verify=False)

        # get the results as a dict
        if(r.ok):
            results = r.json()
            print(results['results'][0]['status'])
        else:
            print("error with http")
    except Exception:
        print("error with request")


def parse_payload(payload, type='value'):
    result = payload  # for value types just return payload

    if(type == 'csv'):
        # break on commas into an array
        result = payload.split(',')

        # do a little cleanup on the values
        result = list(map(lambda v: v.strip().replace('"', ''), result))

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


def load_config_file(config_file):
    with open(os.path.join(utils.CONFIG_DIR, 'schema.yaml'), 'r') as file:
        schema = yaml.safe_load(file)

    # load the yaml config file
    with open(os.path.join(utils.CONFIG_DIR, config_file), 'r') as file:
        c = yaml.safe_load(file)

    v = Validator(schema)
    if(not v.validate(c, schema)):
        print("Error - configuration file syntax is invalid")
        print(str(v.errors))
        sys.exit(2)

    return v.normalized(c)


# parse CLI arguments
parser = argparse.ArgumentParser(description='SNMP to Icinga')
parser.add_argument('-c', '--config', default="config.yaml",
                    help='Path to YAML config file')
parser.add_argument('-t', '--test', action="store_true",
                    help="In test mode results are not sent to Icinga, printed to screen instead")
parser.add_argument('-V', "--validate", action='store_true',
                    help="Validate the config file and exit")
args = parser.parse_args()

# load and validate the config file
config = load_config_file(args.config)

if(args.validate):
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
    jinja_env.globals = {"trap": {"host": trap_snmp['sender_ip'], "oid": trap_snmp['oid']}}

    # render return code starting with ok
    if(render_template(jinja_env, return_codes['ok'], parsed_payload)):
        trap_snmp['return_value'] = utils.RETURN_CODES['OK']
    elif(render_template(jinja_env, return_codes['warning'], parsed_payload)):
        trap_snmp['return_value'] = utils.RETURN_CODES['WARNING']
    elif(render_template(jinja_env, return_codes['critical'], parsed_payload)):
        trap_snmp['return_value'] = utils.RETURN_CODES['CRITICAL']
    else:
        trap_snmp['return_value'] = utils.RETURN_CODES['UNKNOWN']

    # set the plugin output from template, if given, otherwise raw payload
    if('plugin_output' in trap_config['icinga']):
        trap_snmp['plugin_output'] = render_template(jinja_env, trap_config['icinga']['plugin_output'], parsed_payload, return_bool=False)
    else:
        trap_snmp['plugin_output'] = trap_snmp['payload']

    # finally evaluate the performance data
    if('performance_data' in trap_config['icinga']):
        trap_snmp['performance_data'] = render_template(jinja_env, trap_config['icinga']['performance_data'], parsed_payload, return_bool=False)
    else:
        trap_snmp['performance_data'] = ""

    # send to icinga if not in test mode
    if(not args.test):
        send_to_icinga(trap_config['icinga']['host'], trap_config['icinga']['service'], trap_snmp)
    else:
        print(f"Matched: {trap_config['name']}")
        print(f"Exit Status: {trap_snmp['return_value']}, Plugin Output: {trap_snmp['plugin_output']}")
else:
    print(f"No match for host {trap_snmp['sender_ip']} and OID {trap_snmp['oid']}")
