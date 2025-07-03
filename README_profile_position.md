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
# Set CiA 402 State machine to SWITCH ON DISABLED
set_node_state(node, NodeState.SWITCH_ON_DISABLED)

# Set CiA 402 State machine to READY TO SWITCH ON
set_node_state(node, NodeState.READY_TO_SWITCH_ON)

# Set CiA 402 State machine to SWITCHED ON
set_node_state(node, NodeState.SWITCH_ON)
```

### 2. Configure Mode and Position Settings

```python
# Set mode to Profile Position Mode (Trajectory)
set_node_operation_mode(node, NodeOperationMode.TRAJECTORY)

# Set the position window parameters
node.sdo["Position window"].raw = 10       # Position window (0x6067)
node.sdo["Position window time"].raw = 50  # Position window time (0x6068)
```

### 3. Enable Operation

```python
set_node_state(node, NodeState.OPERATION_ENABLED)
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
set_node_state(node, NodeState.SWITCH_ON)
set_node_state(node, NodeState.READY_TO_SWITCH_ON)
```

This powers off the drive while maintaining communication.

---

## Executing a single motion cycle

### 1. Prepare the controlword
```python
cw = 0x0F
set_controlword(node, controlword=cw)
```

### 2. Set the target position
```python
set_target_position(node, target_position=target_pos)
```

### 3. Start a motion by setting bit 4 in the controlword
```python
set_controlword(node, controlword=cw | BIT(4))
```

### 4. Wait for the drive to acknowledge
```python
wait_for_statusword_flags(node, BIT(12))
```

### 5. Clear the start bit
```python
set_controlword(node, controlword=cw & ~BIT(4))
```

### 6. Wait until the target is reached
```python
wait_for_statusword_flags(node, BIT(10))
```

### 7. Read the actual position
```python
current_pos = get_actual_position(node)
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

