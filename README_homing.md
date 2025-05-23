# Xeryon Homing mode example

This README provides a focused explanation of how to configure and execute a homing sequence using CiA 402-compliant devices from Xeryon over CANopen.

---

## Overview

Homing is a standard operation in CiA 402 that moves the actuator to a known mechanical reference point. It is essential before operating in absolute position modes. The procedure requires correct state transitions, mode setting, and use of homing-specific objects from the Object Dictionary.

The general steps are:

1. Prepare the state machine (SWITCHED ON)
2. Set homing mode
3. Configure homing parameters (method, offset, etc.)
4. Start homing via Controlword (0x6040)
5. Wait for homing complete
6. Exit homing mode or continue to next operation

---

## State Machine Transitions

```text
+-------------------------+
| SWITCH ON DISABLED      |  <- Power stage off
+-----------+-------------+
            |
            v
+-------------------------+
| READY TO SWITCH ON      |  <- Internal checks passed
+-----------+-------------+
            |
            v
+-------------------------+
| SWITCHED ON             |  <- Logic active, power not yet enabled
+-----------+-------------+
            |
            v
+-------------------------+
| OPERATION ENABLED       |  <- Drive is active
+-------------------------+
```

You must reach `OPERATION ENABLED` before homing will start.

---

## Full Example Structure – Homing Operation

### 1. Initialize State Machine

```python
transition_402_cw_state(node, P402CWState.SWITCH_ON_DISABLED)
transition_402_cw_state(node, P402CWState.READY_TO_SWITCH_ON)
transition_402_cw_state(node, P402CWState.SWITCH_ON)
```

### 2. Set Operation Mode to Homing

```python
set_control_mode(node, ControlMode.HOMING)
transition_402_cw_state(node, P402CWState.OPERATION_ENABLED)
```

### 3. Configure Homing Parameters

```python
node.sdo["Home offset"].raw = 0                             # Home offset (0x607C)

if direction_positive:
    method = HomingMethod.POS_INDEX
else:
    method = HomingMethod.NEG_INDEX

node.sdo["Homing method"].raw = method                      # Homing method (0x6098)
```

### 4. Trigger Homing

```python
node.controlword = node.sdo["Controlword"].raw | BIT(4)     # Set bit 4 to start homing
```

### 5. Wait for Homing to Complete

```python
wait_for_statusword_flags(node, BIT(12))                    # Bit 12 = homing attained
```

### 6. Finalize

```python
node.controlword = node.sdo["Controlword"].raw & ~BIT(4)    # Clear bit 4

log.info(f"Node {node.id}: Homing completed")
```

---

## Object Dictionary References

| Name                   | Index  | Purpose                     |
| ---------------------- | ------ | --------------------------- |
| Controlword            | 0x6040 | State control bits          |
| Statusword             | 0x6041 | Current state confirmation  |
| Modes of Operation     | 0x6060 | Select operation mode       |
| Modes Display (active) | 0x6061 | Confirm active mode         |
| Homing method          | 0x6098 | Choose homing strategy      |
| Home offset            | 0x607C | Position shift after homing |

---

## Notes

* Do not set homing parameters while in OPERATION ENABLED..
* Once homed, transition to another mode (e.g. PROFILE\_POSITION) before continuing.
* If homing offset is set, move to position 0 using PROFILE\_POSITION to move the device to the offset.
* Always check bit 12 in Statusword (0x6041) to confirm homing completion.
