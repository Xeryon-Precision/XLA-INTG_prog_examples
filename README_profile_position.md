# Xeryon Profile position mode example

TThis README provides a detailed explanation for profile position mode using CiA 402-compliant devices from Xeryon over CANopen. It outlines when and where to apply configuration, how to transition through the state machine, and how to interact with standard CiA 402 objects like Controlword (0x6040), Statusword (0x6041), and Target Position (0x607A).

---

## Overview

CiA 402 defines a standard state machine for controlling motion devices. A proper workflow involves:

1. Initializing and configuring the drive
2. Setting the desired operation mode
3. Enabling operation through the state machine
4. Sending profile position commands
5. Disabling the drive after movement

---

## CiA 402 State Machine

The primary states involved in motion control are:

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

These transitions are triggered by writing to Controlword (0x6040) and are confirmed through Statusword (0x6041).

---

## Full Example Structure

This structure shows a full positioning routine using the CiA 402 state machine:

### 1. Initialize State Machine

```python
transition_402_cw_state(node, P402CWState.SWITCH_ON_DISABLED)
transition_402_cw_state(node, P402CWState.READY_TO_SWITCH_ON)
transition_402_cw_state(node, P402CWState.SWITCH_ON)
```

### 2. Configure Mode and Position Settings

```python
set_control_mode(node, ControlMode.TRAJECTORY)

node.sdo["Position window"].raw = 5                  # Position window (0x6067)
node.sdo["Position window time"].raw = 50            # Position window time (0x6068)
```

### 3. Enable Operation

```python
transition_402_cw_state(node, P402CWState.OPERATION_ENABLED)
```

### 4. Send Position Commands

```python
for target_pos in positions:
    send_position_command(node, target_pos)
```

The `send_position_command()` function does the following:

* Writes target to Target Position (0x607A)
* Sets the new set-point bit (bit 4) in Controlword (0x6040)
* Waits for acknowledgement bit (bit 12) via Statusword (0x6041)
* Clears the new set-point bit (bit 4) in Cotrolword (0x6040)
* Waits for Target reached bit (bit 10) via Statusword (0x6041)

### 5. Safely Disable the Drive

```python
transition_402_cw_state(node, P402CWState.SWITCH_ON)
transition_402_cw_state(node, P402CWState.READY_TO_SWITCH_ON)
```

This powers off the drive while maintaining communication.

---

## Summary Flow (Code-Level)

```python
transition_402_cw_state(node, P402CWState.SWITCH_ON_DISABLED)
transition_402_cw_state(node, P402CWState.READY_TO_SWITCH_ON)
transition_402_cw_state(node, P402CWState.SWITCH_ON)

set_control_mode(node, ControlMode.TRAJECTORY)
node.sdo["Position window"].raw = 5        # (0x6067)
node.sdo["Position window time"].raw = 50  # (0x6068)

transition_402_cw_state(node, P402CWState.OPERATION_ENABLED)

for pos in positions:
    send_position_command(node, pos)

transition_402_cw_state(node, P402CWState.SWITCH_ON)
transition_402_cw_state(node, P402CWState.READY_TO_SWITCH_ON)
```

---

## Important Object Dictionary Entries

| Object                     | Index  | Purpose                       |
| -------------------------- | ------ | ----------------------------- |
| Controlword                | 0x6040 | State control bits            |
| Statusword                 | 0x6041 | Current drive state           |
| Modes of Operation         | 0x6060 | Select operation mode         |
| Modes of Operation Display | 0x6061 | Confirmed active mode         |
| Target Position            | 0x607A | Desired position              |
| Position Actual Value      | 0x6064 | Read-back current position    |
| Position window            | 0x6067 | Acceptable window size        |
| Position window time       | 0x6068 | Time the window must be valid |

---

