"""
example_profile_position.py

Demonstration of CiA 402 Profile Position Mode with Xeryon drives.

Performs a full state-machine-compliant homing operation followed by a looped
positioning sequence. Showcases control mode switching, set-point signaling,
statusword monitoring.

For more information, please read the README:
- README_homing.md
- README_profile_position.md

© 2025 Xeryon – All rights reserved.
"""

import logging

import time
from canopen import BaseNode402

from config import (
    HomingMethod, ControlMode, DEFAULT_BOOTUP_TIMEOUT, DEFAULT_SDO_TIMEOUT, NODE_ID, NMTState, P402CWState
)
from utils import set_control_mode, wait_for_statusword_flags, setup_network, BIT, transition_402_cw_state

# ----- Logging setup -----
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)
logging.getLogger("canopen").setLevel(logging.WARNING)


def configure_node(node: BaseNode402) -> None:
    """
    Resets the node, waits for bootup, loads configuration, and enables the state machine.

    Args:
        node (BaseNode402): The CANopen device node.
    """
    node.nmt.state = NMTState.RESET
    node.nmt.wait_for_bootup(DEFAULT_BOOTUP_TIMEOUT)
    node.sdo.RESPONSE_TIMEOUT = DEFAULT_SDO_TIMEOUT

    log.info(f"Node {node.id}: Booted with state {node.nmt.state}")
    node.load_configuration()

    log.info(f"Node {node.id}: Configuration loaded, setting up CiA 402 state machine")
    node.setup_402_state_machine()

    node.nmt.state = NMTState.OPERATIONAL
    log.info(f"Node {node.id}: Switched to OPERATIONAL state")


def homing(node: BaseNode402, direction_positive=True) -> None:
    """
    Performs a homing operation using the configured homing method.

    Args:
        node (BaseNode402): The CANopen device node.
        direction_positive (bool): True = Homing method to use is positive index, otherwise negative.
    """
    log.info(f"Node {node.id}: Start Homing")

    # Set CiA 402 State machine to SWITCH ON DISABLED
    transition_402_cw_state(node, P402CWState.SWITCH_ON_DISABLED)
    
    # Set CiA 402 State machine to READY TO SWITCH ON
    transition_402_cw_state(node, P402CWState.READY_TO_SWITCH_ON)

    # Set CiA 402 State machine to SWITCHED ON
    transition_402_cw_state(node, P402CWState.SWITCH_ON)

    # Set mode to Homing
    set_control_mode(node, ControlMode.HOMING)

    # Set CiA 402 State machine to OPERATION ENABLED
    transition_402_cw_state(node, P402CWState.OPERATION_ENABLED)

    # Set the homing offset
    node.sdo["Home offset"].raw = 0

    if direction_positive:
        method = HomingMethod.POS_INDEX
    else:
        method = HomingMethod.NEG_INDEX

    node.sdo["Homing method"].raw = method

    # Start homing (set bit 4)
    log.info(f"Node {node.id}: Starting homing with method {method}")
    node.controlword = node.sdo["Controlword"].raw | BIT(4)

    # Wait until Homing attained
    try:
        log.info(f"Node {node.id}: Waiting for Homing attained")
        wait_for_statusword_flags(node, BIT(12))
    except Exception:
        log.error(f"Node {node.id}: Homing failed")

        # Clear bit 4 when homing failed
        node.controlword = node.sdo["Controlword"].raw & ~BIT(4)
        return

    # Clear bit 4 after homing is attained
    node.controlword = node.sdo["Controlword"].raw & ~BIT(4)

    log.info(f"Node {node.id}: Homing completed")


def position_loop(node: BaseNode402) -> None:
    """
    Loops through a list of target positions using profile position mode.

    Args:
        node (BaseNode402): The CANopen device node.
    """
    log.info(f"Node {node.id}: Start Position loop")

    # Set CiA 402 State machine to SWITCH ON DISABLED
    transition_402_cw_state(node, P402CWState.SWITCH_ON_DISABLED)

    # Set CiA 402 State machine to READY TO SWITCH ON
    transition_402_cw_state(node, P402CWState.READY_TO_SWITCH_ON)

    # Set CiA 402 State machine to SWITCHED ON
    transition_402_cw_state(node, P402CWState.SWITCH_ON)

    # Set mode to Profile Position Mode (Trajectory)
    set_control_mode(node, ControlMode.TRAJECTORY)

    # Set the position window parameters
    node.sdo["Position window"].raw = 5
    node.sdo["Position window time"].raw = 50  # ms

    # Set CiA 402 State machine to OPERATION ENABLED
    transition_402_cw_state(node, P402CWState.OPERATION_ENABLED)

    pos_1 = -10000
    pos_2 = 10000
    step = 5000

    positions = list(range(pos_1, pos_2, step)) + list(range(pos_2, pos_1, -step))
    step_delay = 0.5

    err_count = 0
    for i in range(5):
        try:
            for target_pos in positions:
                send_position_command(node, target_pos)
                time.sleep(step_delay)
        except Exception as e:
            log.warning(f"Node {node.id}: Communication failure: {e}")

            err_count += 1
            if err_count >= 2:
                log.error(f"Node {node.id}: Stopping loop after 2 consecutive errors.")
                break

    # Turn off the device after finishing the position loop
    # Set CiA 402 State machine to SWITCHED ON
    transition_402_cw_state(node, P402CWState.SWITCH_ON)

    # Set CiA 402 State machine to READY TO SWITCH ON
    transition_402_cw_state(node, P402CWState.READY_TO_SWITCH_ON)

    log.info(f"Node {node.id}: Position loop completed")


def send_position_command(node: BaseNode402, target_pos: int) -> None:
    """
    Sends a single position command and waits for movement to complete.

    Args:
        node (BaseNode402): The CANopen device node.
        target_pos (int): Target position in internal units.
    """
    log.info(f"Node {node.id}: Sending target position {target_pos}")
    node.sdo["Target Position"].raw = target_pos

    # Set bit 4 to signal new set-point
    node.controlword = node.sdo["Controlword"].raw | BIT(4)

    # Wait for Acknoledge bit 12 to be set in Statusword
    log.info(f"Node {node.id}: Waiting for target acknowledged")
    wait_for_statusword_flags(node, BIT(12))

    # Clear bit 4 after acknowledgment
    node.controlword = node.sdo["Controlword"].raw & ~BIT(4)

    # Wait for Target Reached bit 10 to be set in Statusword
    log.info(f"Node {node.id}: Waiting for arrival")
    wait_for_statusword_flags(node, BIT(10))

    # Read the actual position after target is reached
    current_pos = node.sdo["Position Actual Value"].raw
    log.info(f"Node {node.id}: Reached position {current_pos}")


def main() -> None:
    """
    Entry point for executing the homing and position.
    """
    try:
        network, absolute_path = setup_network()
        network.check()

        node = BaseNode402(NODE_ID, absolute_path)
        network.add_node(node)

        configure_node(node)

        time.sleep(1)

        homing(node)

        time.sleep(1)

        position_loop(node)

    except KeyboardInterrupt:
        log.info("Keyboard interrupt detected, stopping program..")
        pass

    except Exception as e:
        log.error(f"Error occured: {e}")


if __name__ == "__main__":
    main()
