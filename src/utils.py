"""
constants and utility functions for the other scripts
"""
import os.path
import re

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
LOG_DIR = os.path.join(SCRIPT_DIR, 'tmp')


def parse_snmp(trap):
    """
    parse raw snmp trap data into a useable format

    :returns: dict containing the sender ip, oid, and payload
    """
    # network info is index 1 and payload is at the end
    network_info = str(trap[1]).strip()
    payload = str(trap[len(trap) - 1]).strip()

    # get the sender's IP (first match)
    sender = re.search('((\d+)\.){3}(\d+)', network_info).group()

    # find the oid
    oid = re.search('iso(\.([\d]{0,}))+', payload).group()
    payload = payload[len(oid) + 1:]

    return {"sender_ip": sender, "oid": oid, "payload": payload}
