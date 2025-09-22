"""
mode_profile_position.py

Demonstration of CiA 402 Profile Position Mode with Xeryon drives.

Performs a full state-machine-compliant homing operation followed by a looped
positioning sequence. Showcases control mode switching, set-point signaling,
statusword monitoring.

For more information, please read the README:
- homing.md
- mode_profile_position.md

© 2025 Xeryon – All rights reserved.
"""

import logging
import sys
import time

from canopen import BaseNode402

from common.parameters import NodeOperationMode, NodeState
from common.utils import (
    set_node_operation_mode, wait_for_statusword_flags, setup_network, BIT, set_node_state, homing, configure_node,
    set_target_position, set_controlword, get_actual_position, error_handler
)
from settings import NODE_ID, INC_PER_MM

# ----- Logging setup -----
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)
logging.getLogger("canopen").setLevel(logging.WARNING)


def position_loop(node: BaseNode402) -> None:
    """
    Loops through a list of target positions using profile position mode.

    Args:
        node (BaseNode402): The CANopen device node.

    Returns:
        None
    """
    log.info(f"Node {node.id}: Start Position loop")

    # Set CiA 402 State machine to SWITCH ON DISABLED
    set_node_state(node, NodeState.SWITCH_ON_DISABLED)

    # Set CiA 402 State machine to READY TO SWITCH ON
    set_node_state(node, NodeState.READY_TO_SWITCH_ON)

    # Set CiA 402 State machine to SWITCHED ON
    set_node_state(node, NodeState.SWITCH_ON)

    # Set mode to Profile Position Mode (Trajectory)
    set_node_operation_mode(node, NodeOperationMode.TRAJECTORY)

    # Set the position window parameters
    node.sdo["Position window"].raw = 10
    node.sdo["Position window time"].raw = 50  # ms

    # Set CiA 402 State machine to OPERATION ENABLED
    set_node_state(node, NodeState.OPERATION_ENABLED)

    pos_1 = -10 * INC_PER_MM
    pos_2 = 10 * INC_PER_MM
    step = 5 * INC_PER_MM

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
    
    time.sleep(5)

    # Turn off the device after finishing the position loop
    # Set CiA 402 State machine to SWITCHED ON
    set_node_state(node, NodeState.SWITCH_ON)

    # Set CiA 402 State machine to READY TO SWITCH ON
    set_node_state(node, NodeState.READY_TO_SWITCH_ON)

    log.info(f"Node {node.id}: Position loop completed")


def send_position_command(node: BaseNode402, target_pos: int) -> None:
    """
    Sends a single position command and waits for movement to complete.

    Args:
        node (BaseNode402): The CANopen device node.
        target_pos (int): Target position in internal units.

    Returns:
        None
    """
    cw = 0x0F
    set_controlword(node, controlword=cw)

    log.info(f"Node {node.id}: Sending target position {target_pos}")
    set_target_position(node, target_position=target_pos)

    # Set bit 4 to signal new set-point
    log.info(f"Node {node.id}: Setting new set-point to to initiate motion")
    set_controlword(node, controlword=cw | BIT(4))

    # Wait for Acknowledge bit 12 to be set in Statusword
    log.info(f"Node {node.id}: Waiting for acknowledged to be set")
    wait_for_statusword_flags(node, BIT(12))

    # Clear bit 4 after acknowledgment
    set_controlword(node, controlword=cw & ~BIT(4))

    # Wait for Target Reached bit 10 to be set in Statusword
    log.info(f"Node {node.id}: Waiting for target reached")
    wait_for_statusword_flags(node, BIT(10))

    # Read the actual position after target is reached
    current_pos = get_actual_position(node)
    log.info(f"Node {node.id}: Reached position {current_pos}")


def main() -> None:
    """
    Entry point for executing the homing and profile position mode.

    Returns:
        None
    """
    network = None
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
        error_handler(e)

    finally:
        if network:
            network.disconnect()


if __name__ == "__main__":
    main()
    sys.exit(0)
