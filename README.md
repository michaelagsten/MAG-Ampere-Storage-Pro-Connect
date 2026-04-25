[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

# Ampere Storage Pro Modbus (Enhanced)

Home Assistant custom component for locally reading data from  
Ampere Storage Pro (Energiekonzepte Deutschland / SAJ HS2) inverters via Modbus TCP.

This repository is a hardened and extended branch of the original project:  
[https://github.com/dboeni/home-assistant-ampere-storage-pro-modbus](https://github.com/dboeni/home-assistant-ampere-storage-pro-modbus)

---

## Overview

This version focuses on stability, robustness and extended functionality,  
especially for parallel Modbus operation, for example together with KiwiGrid HEMS.

Release 1.3 further hardens the integration lifecycle, Modbus communication handling, sensor setup and binary sensor state handling.

---

## Key Improvements (Release 1.3)

### 1. Hardened Modbus Communication

- Reduced Modbus read chunk size from 60 to 30 registers
- Added pacing between Modbus requests
- Enforced one active Modbus transaction at a time
- Improved handling of invalid Modbus responses
- Hard reconnect after:
  - Modbus I/O errors
  - timeouts
  - cancelled requests
  - disconnected client states
- Reduced risk of mixed or stale Modbus transactions

### 2. Partial Update Handling

The integration no longer fails the complete update cycle when only one read block fails.

Instead:

- valid read blocks are still processed
- cached values remain available
- temporary failures are logged without invalidating all entities
- Home Assistant entities remain more stable during short inverter communication faults

This is especially relevant when the inverter is accessed by multiple clients, such as Home Assistant and a HEMS system.

### 3. Improved Connection Lifecycle

- Explicit connection creation and teardown
- Clean socket reset after protocol or transport errors
- Safer shutdown behavior during Home Assistant reloads and restarts
- Added `async_shutdown()` support in the hub
- Prevents dangling Modbus tasks during unload or shutdown

### 4. Hardened Config Entry Lifecycle

- Hub data is now stored by `entry.entry_id` instead of the user-visible entry name
- Prevents lookup failures after entry renames
- Avoids collisions between entries with identical names
- Initial Modbus refresh failures are handled as `ConfigEntryNotReady`
- Home Assistant can retry setup cleanly after temporary inverter unavailability
- Failed setup attempts now clean up hub state properly
- Platform setup failures trigger a clean rollback

### 5. Hardened Sensor Platform

- Sensors now resolve the hub by config entry ID
- Stable device identifiers based on config entry ID
- Stable unique IDs based on domain, entry ID and sensor key
- Defensive setup handling if hub data is missing
- Invalid values such as `unknown`, `unavailable` or empty strings are suppressed
- Numeric sensors remain numeric
- Invalid non-numeric values for numeric sensors are returned as `None`
- Improved availability handling based on coordinator state

### 6. Hardened Binary Sensor Platform

- Binary sensors now resolve the hub by config entry ID
- Stable device identifiers based on config entry ID
- Stable unique IDs based on domain, entry ID and binary sensor key
- Defensive handling of missing coordinator data
- Explicit boolean values are preferred where available
- `devicestatus_raw` is used as compatibility fallback
- Invalid, missing or non-integer device status values return `None`

### 7. Reduced Log Noise

- Repeated polling suspension countdown messages are now logged at debug level
- Temporary block failures are handled more gracefully
- Error logs are now more focused on actionable Modbus failures

---

## Key Improvements (Release 1.2)

### 1. Modbus Stability & Anti-Freeze

- Strict connection lifecycle with explicit connect and close
- No uncontrolled reconnect loops
- Automatic reconnect on failures
- Suspend window after repeated errors to prevent overload loops
- Stable long-term operation without manual restarts

### 2. Safe Modbus Communication

- Automatic register chunking
- Fully compliant with Modbus limits of max. 125 registers per request
- Eliminates read errors for large register blocks
- Controlled timing between requests

### 3. Parallel Operation (KiwiGrid HEMS)

- Optimized polling behavior to reduce bus contention
- Prevents Modbus freezes under multiple clients
- Stable operation with Home Assistant and KiwiGrid HEMS in parallel

### 4. Extended Energy Metrics

Added full grid energy statistics:

- Grid Import (FeedIn):
  - Daily
  - Monthly
  - Yearly
  - Total
- Grid Export (Sell):
  - Daily
  - Monthly
  - Yearly
  - Total

Registers: `0x4167` – `0x4175`  
Data type: `UInt32`  
Scale: `0.01 kWh`

### 5. AC Grid Measurements

- Voltage L1 / L2 / L3
- Grid frequency

Additional logic:

- Plausibility checks using valid grid ranges
- Automatic fallback to last valid values
- Prevents corrupted Home Assistant statistics from short invalid inverter readings

### 6. Operation Mode Detection

- Raw device status: `devicestatus_raw`
- Binary sensors:
  - Island Mode / off-grid
  - Grid Mode / grid-connected

Mapping:

- `0x4004 == 3` → Island Mode
- `0x4004 == 4` → Grid Mode

### 7. Improved Error Handling

- Strict response validation
- Retry with backoff
- Clean connection reset on failure
- Detailed diagnostic logging

---

## Features

- Setup via Home Assistant UI
- Configurable:
  - Host
  - Port
  - Slave ID / Unit ID
  - Scan interval
- Efficient block-based register reading
- Conservative Modbus chunking for improved inverter compatibility
- Binary sensors for system state:
  - Grid Mode
  - Island Mode
- Extended energy statistics:
  - PV generation
  - Battery charge / discharge
  - Grid import / export
- AC grid measurements:
  - L1 / L2 / L3 voltage
  - Grid frequency
- Cached last-good values for selected measurements
- Partial update tolerance during temporary Modbus faults
- Stable long-term operation with parallel Modbus clients

---

## Installation

This custom component can be installed in two ways.

### 1. Installation via HACS

- Install HACS: [https://hacs.xyz/docs/setup/download/](https://hacs.xyz/docs/setup/download/)
- Add this repository as a custom integration:
  1. Open HACS → Integrations
  2. Click the 3-dot menu → Custom repositories
  3. Add this repository URL
  4. Select Integration
- Install the integration via HACS
- Restart Home Assistant
- Go to Settings → Devices & Services
- Click Add Integration
- Search for Ampere Storage Pro Modbus

### 2. Manual Installation

Copy the folder:

```text
custom_components/ampere_modbus
```

into:

```text
<config_dir>/custom_components/ampere_modbus/
```

Then:

- Restart Home Assistant
- Add integration via UI:
  - Settings → Devices & Services → Add Integration
  - Search for Ampere Storage Pro Modbus

---

## Upgrade Notes for Release 1.3

Release 1.3 changes how entities and devices are internally identified.

The integration now uses the Home Assistant config entry ID instead of the user-visible integration name for:

- hub lookup
- device identifiers
- sensor unique IDs
- binary sensor unique IDs

This is technically more robust, but existing entities may be recreated after the update.

If duplicate entities appear:

- verify that the new entities receive valid data
- remove old disabled or orphaned entities from the Home Assistant entity registry
- update dashboards, automations or statistics references if entity IDs changed

Recommended after upgrade:

- restart Home Assistant once
- check the integration under Settings → Devices & Services
- monitor logs for recurring Modbus read failures
- verify energy sensors in the Energy Dashboard

---

## Notes

- Optimized for SAJ HS2 / Ampere Storage Pro systems
- Parallel Modbus operation, for example with KiwiGrid HEMS, is explicitly considered
- Short invalid grid readings from the inverter are filtered automatically
- The integration is more tolerant of temporary Modbus failures, but persistent failures still indicate an underlying network, inverter, gateway or competing-client issue

---

## Troubleshooting

### Temporary Modbus read failures

Occasional messages such as `Modbus read block failed` can occur if the inverter is temporarily busy or another client is polling at the same time.

Release 1.3 keeps cached values and continues processing other valid read blocks.

### Repeated connection failures

If connection failures persist, check:

- inverter IP address
- Modbus TCP port
- Unit ID / Slave ID
- network stability
- Wi-Fi signal quality, if applicable
- whether another system is polling the inverter too aggressively

Possible mitigation:

- increase the scan interval
- reduce Modbus traffic from other clients
- ensure that the inverter has a stable LAN connection

### Duplicate entities after upgrade

Release 1.3 uses more stable unique IDs. Home Assistant may therefore create new entities.

Remove old orphaned entities only after confirming that the new entities work correctly.

---

## Future Improvements

- HACS default repository integration
- Writable control parameters, for example power limits
- Battery diagnostics and battery health metrics
- Battery control and load shifting support
- Extended diagnostics and monitoring
- Optional configuration for Modbus chunk size and request pacing

---

## Disclaimer

This is a custom integration and not officially supported by Home Assistant.  
Use at your own risk in production environments.

---

