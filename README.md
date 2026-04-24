[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

# Ampere Storage Pro Modbus (Enhanced)

Home Assistant custom component for locally reading data from  
Ampere Storage Pro (Energiekonzepte Deutschland / SAJ HS2) inverters via Modbus TCP.

This repository is a hardened and extended branch of the original project:  
https://github.com/dboeni/home-assistant-ampere-storage-pro-modbus

---

## Overview

This version focuses on stability, robustness and extended functionality,  
especially for parallel Modbus operation (e.g. together with KiwiGrid HEMS).

---

## Key Improvements (Release 1.2)

### 1. Modbus Stability & Anti-Freeze
- Strict connection lifecycle (explicit connect / close)
- No uncontrolled reconnect loops
- Automatic reconnect on failures
- Suspend window after repeated errors (prevents overload loops)
- Stable long-term operation without manual restarts

### 2. Safe Modbus Communication
- Automatic register chunking (60 registers per request)
- Fully compliant with Modbus limits (≤125 registers)
- Eliminates read errors for large register blocks
- Controlled timing between requests

### 3. Parallel Operation (KiwiGrid HEMS)
- Optimized polling behavior to avoid bus contention
- Prevents Modbus freezes under multiple masters
- Stable operation with Home Assistant and KiwiGrid HEMS in parallel

### 4. Extended Energy Metrics
Added full grid energy statistics:
- Grid Import (FeedIn):
  - Daily / Monthly / Yearly / Total
- Grid Export (Sell):
  - Daily / Monthly / Yearly / Total

Registers: 0x4167 – 0x4175 (UInt32, scale 0.01)

### 5. AC Grid Measurements
- Voltage L1 / L2 / L3
- Grid frequency

Additional logic:
- Plausibility checks (valid grid ranges)
- Automatic fallback to last valid values
- Prevents corrupted Home Assistant statistics

### 6. Operation Mode Detection
- Raw device status (devicestatus_raw)
- Binary sensors:
  - Island Mode (off-grid)
  - Grid Mode (grid-connected)

Mapping:
- 0x4004 == 3 → Island Mode
- 0x4004 == 4 → Grid Mode

### 7. Improved Error Handling
- Strict response validation
- Retry with exponential backoff
- Clean connection reset on failure
- Detailed logging for diagnostics

---

## Features

- Setup via Home Assistant UI
- Configurable:
  - Host / Port
  - Slave ID
  - Scan interval
- Efficient block-based register reading
- Binary sensors for system state (grid / island)
- Stable long-term operation

---

## Installation

This custom component can be installed in two ways:

### 1. Installation via HACS

- Install HACS (https://hacs.xyz/docs/setup/download/)
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

- Copy the folder:
  custom_components/ampere_modbus  
  into:
  <config_dir>/custom_components/ampere_modbus/

- Restart Home Assistant
- Add integration via UI:
  Settings → Devices & Services → Add Integration  
  Search for Ampere Storage Pro Modbus

---

## Notes

- Optimized for SAJ HS2 / Ampere Storage Pro
- Parallel Modbus operation (e.g. KiwiGrid) is explicitly supported
- Short invalid readings from the inverter are filtered automatically

---

## Future Improvements

- HACS default repository integration
- Writable control parameters (e.g. power limits)
- Battery control / load shifting support
- Extended diagnostics and monitoring

---

## Disclaimer

This is a custom integration and not officially supported by Home Assistant.  
Use at your own risk in production environments.

---
