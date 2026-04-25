[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

Ampere Storage Pro Modbus (Enhanced)

Home Assistant custom component for locally reading data from
Ampere Storage Pro (Energiekonzepte Deutschland / SAJ HS2 / SAJ H2) inverters via Modbus TCP.

This repository is a hardened and extended branch of the original project:
https://github.com/dboeni/home-assistant-ampere-storage-pro-modbus￼

⸻

Overview

This version focuses on stability, robustness and extended functionality,
especially for parallel Modbus operation, for example together with KiwiGrid HEMS.

Release 1.6 adds the finalized first-stage BMS battery stack readout, improves realtime register polling stability and extends the integration lifecycle handling in __init__.py so stale Home Assistant devices can be removed from the device registry.

⸻

Key Improvements (Release 1.6)

1. Finalized BMS Battery Stack Readout

Release 1.6 adds first-stage BMS health monitoring for SAJ H2 / HS2 based storage systems.

The integration now reads the SAJ BMS peripheral register block for the reported battery stack:

0xA000–0xA011

This range includes:

* battery module / stack count
* battery capacity in Ah
* available battery capacity
* battery online mask
* battery stack SOC
* battery stack SOH
* battery stack voltage
* battery stack current
* battery stack temperature
* battery stack cycle count

The tested SAJ/BMS setup reports the connected storage as one battery stack.
Therefore, Release 1.6 intentionally exposes one consolidated battery stack instead of separate Battery 2–4 entities.

2. Battery Health Sensors

Added Home Assistant sensor entities for the reported battery stack:

* Battery Module Count
* Battery Capacity Ah
* Battery Available Capacity
* Battery Online Mask
* Battery Stack SOC
* Battery Stack SOH
* Battery Stack Voltage
* Battery Stack Current
* Battery Stack Temperature
* Battery Stack Cycles

The raw coordinator keys are:

battery_module_count
battery_capacity_ah
battery_available_capacity
battery_online_mask
battery_1_soc
battery_1_soh
battery_1_voltage
battery_1_current
battery_1_temperature
battery_1_cycles

Battery Stack values keep the internal battery_1_* keys for compatibility with the first BMS implementation.

3. Removed Battery 2–4 Sensor Definitions

Earlier development versions exposed Battery 2–4 sensor definitions.

Release 1.6 removes these definitions because the tested inverter/BMS combination exposes the connected storage as one reported battery stack.

Removed sensor groups:

* Battery 2 SOC / SOH / voltage / current / temperature / cycles
* Battery 3 SOC / SOH / voltage / current / temperature / cycles
* Battery 4 SOC / SOH / voltage / current / temperature / cycles

This avoids unavailable, misleading or stale entities on systems that expose only one battery stack.

4. Invalid BMS Register Handling

Invalid raw BMS register values are filtered safely.

The following values are treated as unavailable:

0xFFFF
0x7FFF
None

This prevents invalid BMS values from being exposed as numeric Home Assistant sensor states.

5. Reduced BMS Modbus Read Size

The BMS readout was reduced from the earlier multi-module range:

0xA000–0xA023

to the single reported stack range:

0xA000–0xA011

This reduces Modbus traffic and avoids reading unused module registers.

6. Realtime Register Polling Split

The realtime polling was split into smaller stable blocks.

Previous behavior:

Read one large block from 0x4069 with count 60

With conservative chunking, this produced a second read around:

0x4087

Some SAJ H2 devices can return invalid Modbus responses when reading across model-dependent reserved register areas.

Release 1.6 now reads two smaller blocks:

0x4069–0x4079
0x4095–0x40A7

This keeps the existing sensor keys unchanged while avoiding unstable reads across reserved or model-dependent register gaps.

7. Device Registry Cleanup Support

Release 1.6 extends __init__.py with Home Assistant device removal support.

The integration now implements:

async_remove_config_entry_device()

This allows Home Assistant to remove stale devices from the device registry after earlier device_info mappings or sensor layout changes.

This is relevant when old devices remain visible under:

Settings → Devices & Services → Integration → Devices

For example, after consolidating the BMS readout to one reported battery stack.

Without this hook, Home Assistant may still show old integration devices but not offer a working remove option in the UI.

8. Config Entry Removal Cleanup

The integration now includes explicit config entry removal cleanup.

When a config entry is removed, the integration:

* shuts down the Modbus hub
* closes the Modbus connection
* removes runtime data from hass.data
* cleans up the domain data container when no entries remain

This improves lifecycle behavior during removal, reloads and stale config entry cleanup.

9. Fixes

* Fixed an indentation issue in the BMS health readout method
* Fixed stale runtime cleanup paths during setup failures
* Added cleaner removal handling for obsolete devices
* Added async_remove_config_entry_device() in __init__.py so stale devices can be removed from the Home Assistant UI

⸻

Key Improvements (Release 1.3)

1. Hardened Modbus Communication

* Reduced Modbus read chunk size from 60 to 30 registers
* Added pacing between Modbus requests
* Enforced one active Modbus transaction at a time
* Improved handling of invalid Modbus responses
* Hard reconnect after:
    * Modbus I/O errors
    * timeouts
    * cancelled requests
    * disconnected client states
* Reduced risk of mixed or stale Modbus transactions

2. Partial Update Handling

The integration no longer fails the complete update cycle when only one read block fails.

Instead:

* valid read blocks are still processed
* cached values remain available
* temporary failures are logged without invalidating all entities
* Home Assistant entities remain more stable during short inverter communication faults

This is especially relevant when the inverter is accessed by multiple clients, such as Home Assistant and a HEMS system.

3. Improved Connection Lifecycle

* Explicit connection creation and teardown
* Clean socket reset after protocol or transport errors
* Safer shutdown behavior during Home Assistant reloads and restarts
* Added async_shutdown() support in the hub
* Prevents dangling Modbus tasks during unload or shutdown

4. Hardened Config Entry Lifecycle

* Hub data is now stored by entry.entry_id instead of the user-visible entry name
* Prevents lookup failures after entry renames
* Avoids collisions between entries with identical names
* Initial Modbus refresh failures are handled as ConfigEntryNotReady
* Home Assistant can retry setup cleanly after temporary inverter unavailability
* Failed setup attempts now clean up hub state properly
* Platform setup failures trigger a clean rollback

5. Hardened Sensor Platform

* Sensors now resolve the hub by config entry ID
* Stable device identifiers based on config entry ID
* Stable unique IDs based on domain, entry ID and sensor key
* Defensive setup handling if hub data is missing
* Invalid values such as unknown, unavailable or empty strings are suppressed
* Numeric sensors remain numeric
* Invalid non-numeric values for numeric sensors are returned as None
* Improved availability handling based on coordinator state

6. Hardened Binary Sensor Platform

* Binary sensors now resolve the hub by config entry ID
* Stable device identifiers based on config entry ID
* Stable unique IDs based on domain, entry ID and binary sensor key
* Defensive handling of missing coordinator data
* Explicit boolean values are preferred where available
* devicestatus_raw is used as compatibility fallback
* Invalid, missing or non-integer device status values return None

7. Reduced Log Noise

* Repeated polling suspension countdown messages are now logged at debug level
* Temporary block failures are handled more gracefully
* Error logs are now more focused on actionable Modbus failures

⸻

Key Improvements (Release 1.2)

1. Modbus Stability & Anti-Freeze

* Strict connection lifecycle with explicit connect and close
* No uncontrolled reconnect loops
* Automatic reconnect on failures
* Suspend window after repeated errors to prevent overload loops
* Stable long-term operation without manual restarts

2. Safe Modbus Communication

* Automatic register chunking
* Fully compliant with Modbus limits of max. 125 registers per request
* Eliminates read errors for large register blocks
* Controlled timing between requests

3. Parallel Operation (KiwiGrid HEMS)

* Optimized polling behavior to reduce bus contention
* Prevents Modbus freezes under multiple clients
* Stable operation with Home Assistant and KiwiGrid HEMS in parallel

4. Extended Energy Metrics

Added full grid energy statistics:

* Grid Import (FeedIn):
    * Daily
    * Monthly
    * Yearly
    * Total
* Grid Export (Sell):
    * Daily
    * Monthly
    * Yearly
    * Total

Registers: 0x4167 – 0x4175
Data type: UInt32
Scale: 0.01 kWh

5. AC Grid Measurements

* Voltage L1 / L2 / L3
* Grid frequency

Additional logic:

* Plausibility checks using valid grid ranges
* Automatic fallback to last valid values
* Prevents corrupted Home Assistant statistics from short invalid inverter readings

6. Operation Mode Detection

* Raw device status: devicestatus_raw
* Binary sensors:
    * Island Mode / off-grid
    * Grid Mode / grid-connected

Mapping:

* 0x4004 == 3 → Island Mode
* 0x4004 == 4 → Grid Mode

7. Improved Error Handling

* Strict response validation
* Retry with backoff
* Clean connection reset on failure
* Detailed diagnostic logging

⸻

Features

* Setup via Home Assistant UI
* Configurable:
    * Host
    * Port
    * Slave ID / Unit ID
    * Scan interval
* Efficient block-based register reading
* Conservative Modbus chunking for improved inverter compatibility
* Binary sensors for system state:
    * Grid Mode
    * Island Mode
* Extended energy statistics:
    * PV generation
    * Battery charge / discharge
    * Grid import / export
* AC grid measurements:
    * L1 / L2 / L3 voltage
    * Grid frequency
* BMS battery stack diagnostics:
    * battery module / stack count
    * battery capacity in Ah
    * available battery capacity
    * battery online mask
    * battery stack SOC
    * battery stack SOH
    * battery stack voltage
    * battery stack current
    * battery stack temperature
    * battery stack cycle count
* Cached last-good values for selected measurements
* Partial update tolerance during temporary Modbus faults
* Stable long-term operation with parallel Modbus clients
* Stale device removal support through Home Assistant device registry handling

⸻

Installation

This custom component can be installed in two ways.

1. Installation via HACS

* Install HACS: https://hacs.xyz/docs/setup/download/￼
* Add this repository as a custom integration:
    1. Open HACS → Integrations
    2. Click the 3-dot menu → Custom repositories
    3. Add this repository URL
    4. Select Integration
* Install the integration via HACS
* Restart Home Assistant
* Go to Settings → Devices & Services
* Click Add Integration
* Search for Ampere Storage Pro Modbus

2. Manual Installation

Copy the folder:

custom_components/ampere_modbus

into:

<config_dir>/custom_components/ampere_modbus/

Then:

* Restart Home Assistant
* Add integration via UI:
    * Settings → Devices & Services → Add Integration
    * Search for Ampere Storage Pro Modbus

⸻

Upgrade Notes for Release 1.6

Release 1.6 changes the BMS battery sensor layout.

Earlier development versions may have created Battery 2–4 entities.
Release 1.6 removes Battery 2–4 sensor definitions and exposes only the reported battery stack.

After upgrade, old Battery 2–4 entities may remain in Home Assistant’s entity registry as stale or unavailable entities.

Release 1.6 also updates the integration lifecycle handling in __init__.py.

The integration now explicitly supports stale device removal through Home Assistant’s device registry API. This helps remove old devices that were created by previous device_info mappings and are no longer used by the current sensor layout.

Recommended after upgrade:

* restart Home Assistant once
* check the integration under Settings → Devices & Services
* verify that the new Battery Stack sensors report valid values
* remove old unavailable Battery 2–4 entities from the entity registry
* remove old stale devices from the device registry if Home Assistant still shows them
* monitor logs for recurring Modbus read failures

Relevant old entity names may include:

Battery 2 SOC
Battery 2 SOH
Battery 2 Voltage
Battery 2 Current
Battery 2 Temperature
Battery 2 Cycles
Battery 3 SOC
Battery 3 SOH
Battery 3 Voltage
Battery 3 Current
Battery 3 Temperature
Battery 3 Cycles
Battery 4 SOC
Battery 4 SOH
Battery 4 Voltage
Battery 4 Current
Battery 4 Temperature
Battery 4 Cycles

If a stale device remains visible under the integration page, open the device and use the device menu to remove it. Release 1.6 explicitly allows stale device removal through Home Assistant’s device registry handling.

If removal is still not offered, first remove or disable stale entities assigned to that device and restart Home Assistant.

⸻

Upgrade Notes for Release 1.3

Release 1.3 changes how entities and devices are internally identified.

The integration now uses the Home Assistant config entry ID instead of the user-visible integration name for:

* hub lookup
* device identifiers
* sensor unique IDs
* binary sensor unique IDs

This is technically more robust, but existing entities may be recreated after the update.

If duplicate entities appear:

* verify that the new entities receive valid data
* remove old disabled or orphaned entities from the Home Assistant entity registry
* update dashboards, automations or statistics references if entity IDs changed

Recommended after upgrade:

* restart Home Assistant once
* check the integration under Settings → Devices & Services
* monitor logs for recurring Modbus read failures
* verify energy sensors in the Energy Dashboard

⸻

Notes

* Optimized for SAJ HS2 / SAJ H2 / Ampere Storage Pro systems
* Parallel Modbus operation, for example with KiwiGrid HEMS, is explicitly considered
* Short invalid grid readings from the inverter are filtered automatically
* The BMS readout currently exposes raw battery stack values only
* Derived battery diagnostics such as aggregated health status, SOH trend, SOC spread, voltage spread and temperature spread are not included yet
* The integration is more tolerant of temporary Modbus failures, but persistent failures still indicate an underlying network, inverter, gateway or competing-client issue

⸻

Troubleshooting

Temporary Modbus read failures

Occasional messages such as Modbus read block failed can occur if the inverter is temporarily busy or another client is polling at the same time.

Release 1.6 keeps cached values and continues processing other valid read blocks.

Invalid realtime read around 0x4087

Older versions could produce errors similar to:

Invalid Modbus response from address 0x4087

Release 1.6 avoids this by splitting realtime polling into smaller stable blocks and avoiding reads across reserved or model-dependent register gaps.

Missing Battery 2–4 sensors

This is expected in Release 1.6.

The tested SAJ/BMS setup reports the connected storage as one battery stack.
Therefore, the integration exposes Battery Stack values instead of Battery 2–4 module values.

Check these sensors instead:

Battery Module Count
Battery Online Mask
Battery Stack SOC
Battery Stack SOH
Battery Stack Voltage
Battery Stack Current
Battery Stack Temperature
Battery Stack Cycles

Stale Battery 2–4 entities after upgrade

Home Assistant may keep old entities in the entity registry even if the integration no longer creates them.

Remove them manually under:

Settings → Devices & Services → Entities

Search for:

Battery 2
Battery 3
Battery 4
battery_2
battery_3
battery_4

Then remove stale, unavailable or disabled entities after confirming that the new Battery Stack sensors work correctly.

Stale device remains visible

If an old device remains visible under the integration page, open the device and use the device menu to remove it.

Release 1.6 extends __init__.py with explicit device removal support by implementing:

async_remove_config_entry_device()

This allows Home Assistant to remove stale devices from the device registry when they are no longer created by the current integration code.

If the device still cannot be removed, first remove all stale entities assigned to that device, then restart Home Assistant and try again.

Repeated connection failures

If connection failures persist, check:

* inverter IP address
* Modbus TCP port
* Unit ID / Slave ID
* network stability
* Wi-Fi signal quality, if applicable
* whether another system is polling the inverter too aggressively

Possible mitigation:

* increase the scan interval
* reduce Modbus traffic from other clients
* ensure that the inverter has a stable LAN connection

Duplicate entities after upgrade

Release 1.3 introduced more stable unique IDs.
Release 1.6 changes the BMS sensor layout.

Home Assistant may therefore retain old entities.

Remove old orphaned entities only after confirming that the new entities work correctly.

⸻

Future Improvements

* HACS default repository integration
* Writable control parameters, for example power limits
* Battery diagnostics and battery health metrics
* Derived BMS health indicators:
    * SOH trend
    * SOC spread
    * voltage spread
    * temperature spread
    * aggregated battery health status
* Battery control and load shifting support
* Extended diagnostics and monitoring
* Optional configuration for Modbus chunk size and request pacing
* Optional support for installations that expose multiple BMS modules separately

⸻

Disclaimer

This is a custom integration and not officially supported by Home Assistant.
Use at your own risk in production environments.

⸻
