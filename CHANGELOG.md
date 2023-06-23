# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## Unreleased

### Changed

- `--test` flag is not `--validate` to better identify it's function

## Version 0.4

### Added

- added `check_source` as optional config value. This sends the source of the check to Icinga. Important when Icinga rules are based of check source. Defaults to `localhost` if not present

## Version 0.3

### Added

- can specify `plugin_output` and `performance_data` via templates to send to Icinga as well

### Fixed

- Python styling

## Version 0.2

### Added

- Added `snmpicinga.py` file to send results to Icinga
- utilized Jinja to template OK, Warning, and Critical states
- utilized Cerebrus to validate YAML schema

### Changed

- split utility functions into their own Python module

## Version 0.1

### Added

- started with simple `snmplog.py` file to log SNMP traffic
