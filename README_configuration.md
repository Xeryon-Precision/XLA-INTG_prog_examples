# Xeryon Configuration Example

This README provides a detailed explanation for configuring CiA 402-compliant devices from Xeryon over CANopen. It walks through how to connect to a device, apply common runtime settings, and save them to non-volatile memory.

---

## Overview

Before an actuator can be used for positioning or homing, it must be configured.<br>
This includes:
* Resetting parameters to factory defaults (optional)
* Configuring I/O and LED mappings
* Setting control mode
* Setting trajectory parameters
* Setting homing parameters
* Saving changes to flash

---

## Step-by-Step Configuration Structure

### 1. Establish CANopen Network Connection

```python
network, eds_path = setup_network()
node = BaseNode402(NODE_ID, eds_path)
network.add_node(node)
```

### 2. Reset and Enable Logging

```python
node.sdo["Restore Default Parameters"][1].raw = RESTORE_ALL_DEFAULT_PARAMETERS
node.sdo["Status logging verbosity flags"].raw = DEFAULT_STATUS_LOGGING
node.sdo["Mode of operation"].raw = ControlMode.TRAJECTORY
```

### 3. Configure Digital and Analog I/O

```python
node.sdo["I/O Configuration"][1].raw = 1  # AI1 config
node.sdo["I/O Configuration"][2].raw = 1  # DI1
node.sdo["I/O Configuration"][3].raw = 1  # DI2
node.sdo["I/O Configuration"][4].raw = 1  # DI3
node.sdo["LED Configuration"].raw = LEDMask.ALL
```

### 4. Set Optional Input Overrides

```python
node.sdo["I/O Override Enable"].raw = 0b0000  # Modify bits as needed
node.sdo["Hybrid control switch point"].raw = 40
```

### 5. Define Motion Profile Parameters

```python
node.sdo["Max profile velocity"].raw = 400 * INC_PER_MM        # Max velocity (inc/s)         | 400 mm/s
node.sdo["Profile velocity"].raw     = 200 * INC_PER_MM        # Target velocity (inc/s)      | 200 mm/s
node.sdo["Profile acceleration"].raw = 1000 * INC_PER_MM       # Target acceleration (inc/s²) | 1000 mm/s²
node.sdo["Max acceleration"].raw     = 3000 * INC_PER_MM       # Max acceleration (inc/s²)    | 3000 mm/s²
node.sdo["Profile jerk"][1].raw      = 1_000_000 * INC_PER_MM  # Profile Jerk (inc/s³)        | 1_000_000 mm/s³
```

### 6. Configure Homing Settings

```python
node.sdo["Home offset"].raw = 0
node.sdo["Homing parameters"][1].raw = 250      # Step size
node.sdo["Homing parameters"][2].raw = 2        # Tolerance
node.sdo["Homing parameters"][3].raw = 100      # Time (ms)
node.sdo["Homing speeds"][2].raw = 50           # Homing speed
node.sdo["Homing acceleration"].raw = 10000
```

### 7. Save to Flash

```python
node.sdo["Store Parameter Field"][1].raw = SAVE_ALL_PARAMETERS
```

A reset must be performed after this to load all parameters from flash.

---

## Object Dictionary Reference

| Object Name                    | Index  | Purpose                         |
| ------------------------------ | ------ | ------------------------------- |
| Restore Default Parameters     | 0x1011 | Factory reset                   |
| Store Parameter Field          | 0x1010 | Save all config to flash        |
| Status logging verbosity flags | 0x5000 | Enables internal logging        |
| Mode of operation              | 0x6060 | Sets control mode               |
| I/O Configuration              | 0x4000 | Analog/digital pin mapping      |
| LED Configuration              | 0x4001 | Drive LED behavior              |
| I/O Override Enable            | 0x3000 | Mask to enable overrides        |
| I/O Override settings          | 0x3001 | Override control parameters     |
| Hybrid control switch point    | 0x2012 | Switching threshold             |
| Max profile velocity           | 0x607F | Maximum profile velocity        |
| Profile velocity               | 0x6081 | Nominal target velocity         |
| Profile acceleration           | 0x6083 | Acceleration for motion         |
| Max acceleration               | 0x60C5 | Acceleration cap                |
| Profile jerk                   | 0x60A4 | Optional smoothing (jerk limit) |
| Software position limit        | 0x607D | Safety position limits          |
| Home offset                    | 0x607C | Offset after homing             |
| Homing method                  | 0x6098 | Choose homing strategy          |
| Homing parameters              | 0x2013 | Tuning for standstill detection |
| Homing speeds                  | 0x6099 | Speed used during homing        |
| Homing acceleration            | 0x609A | Acceleration used for homing    |

---

## Notes

* You must call save_configuration()` to persist changes after setup.
* Homing and motion parameters should only be set when the device is in a safe state (e.g. SWITCHED ON).
* Reset the device after configuration to ensure the saved parameters are loaded from non-volatile memory.
