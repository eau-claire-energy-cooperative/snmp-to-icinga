import argparse
import os.path
import requests
import sys
import yaml
import utils as utils
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

        if(r.ok):
            results = r.json()
            print(results['results'][0]['status'])
        else:
            print("error with http")
    except:
        print("error with request")

def parse_payload(payload, type='value'):
    return payload

def find_trap_definition(trap_info, traps):
    # go through all the traps until we find a match
    for t in traps:
        if(t['snmp']['host'] == trap_info['sender_ip'] and t['snmp']['oid'] == trap_info['oid']):
            return t

    return None

parser = argparse.ArgumentParser(description='SNMP to Icinga')
parser.add_argument('-c', '--config', default="config.yaml",
                    help='Path to YAML config file')
args = parser.parse_args()

# load the yaml config file
with open(os.path.join(utils.CONFIG_DIR, args.config), 'r') as file:
    config = yaml.safe_load(file)

# parse the trap
trap_snmp = utils.parse_snmp(sys.stdin.readlines())

# check if we have a match
trap_config = find_trap_definition(trap_snmp, config['traps'])

# confirm we have a match for this trap
if(trap_config is not None):
    # convert the trap payload based on the type
    parsed_payload = parse_payload(trap_snmp['payload'], trap_config['snmp']['payload_type'])

    if(parsed_payload == trap_config['icinga']['ok_value']):
        trap_snmp['return_value'] = 0
    elif(parsed_payload == trap_config['icinga']['warning_value']):
        trap_snmp['return_value'] = 1
    elif(parsed_payload == trap_config['icinga']['critical_value']):
        trap_snmp['return_value'] = 2
    else:
        trap_snmp['return_value'] = 3

    # send to icinga
    send_to_icinga(trap_config['icinga']['host'], trap_config['icinga']['service'], trap_snmp)
else:
    print(f"No match for host {trap_snmp['sender_ip']} and OID {trap_snmp['oid']}")
