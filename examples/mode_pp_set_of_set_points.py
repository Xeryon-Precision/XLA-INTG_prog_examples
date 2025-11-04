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
import csv

import pandas as pd
import matplotlib.pyplot as plt

from canopen import BaseNode402

from settings import NODE_ID,INC_PER_MM
from common.parameters import NodeOperationMode, NodeState
from common.utils import (
    set_node_operation_mode, wait_for_statusword_flags, setup_network, BIT, set_node_state, homing, configure_node,
    set_target_position, set_controlword
)

# ----- Logging setup -----
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)
logging.getLogger("canopen").setLevel(logging.WARNING)

def setup_profile_position(node: BaseNode402):
    """
    Setup of the profile position mode

    Args:
        node (BaseNode402): The CANopen device node.

    Returns:
        None
    """
    # Set CiA 402 State machine to SWITCH ON DISABLED
    set_node_state(node, NodeState.SWITCH_ON_DISABLED)

    # Set CiA 402 State machine to READY TO SWITCH ON
    set_node_state(node, NodeState.READY_TO_SWITCH_ON)

    # Set CiA 402 State machine to SWITCHED ON
    set_node_state(node, NodeState.SWITCH_ON)

    # Set mode to Profile Position Mode
    set_node_operation_mode(node, NodeOperationMode.PROFILE_POSITION)

    # Set the position window parameters
    node.sdo["Position window"].raw = 5
    node.sdo["Position window time"].raw = 50  # ms

    # Set CiA 402 State machine to OPERATION ENABLED
    set_node_state(node, NodeState.OPERATION_ENABLED)

    time.sleep(0.010)

def cleanup_profile_position(node: BaseNode402):
    """
    Cleanup of the profile position mode

    Args:
        node (BaseNode402): The CANopen device node.

    Returns:
        None
    """
    # Turn off the device after finishing the position loop
    # Set CiA 402 State machine to SWITCHED ON
    set_node_state(node, NodeState.SWITCH_ON)

    # Set CiA 402 State machine to READY TO SWITCH ON
    set_node_state(node, NodeState.READY_TO_SWITCH_ON)

def position_mode_normal(node: BaseNode402) -> None:
    """

    Args:
        node (BaseNode402): The CANopen device node.

    Returns:
        None
    """
    log.info("Example normal position")

    setup_profile_position(node)


    target_position = 10000
    target_velocity = 50 * INC_PER_MM

    cw = 0x0F
    set_controlword(node, controlword=cw)

    log.info(f"Node {node.id}: Sending target position {target_position}")
    set_target_position(node, target_position=target_position, profile_velocity=target_velocity)

    # Set bit 4 to signal new set-point
    log.info(f"Node {node.id}: Setting new set-point to to initiate motion")
    set_controlword(node, controlword=cw | BIT(4))

    # Wait for Acknoledge bit 12 to be set in Statusword
    log.info(f"Node {node.id}: Waiting for acknowledged to be set")
    wait_for_statusword_flags(node, BIT(12))

    # Clear bit 4 after acknowledgment
    set_controlword(node, controlword=cw & ~BIT(4))

    # Wait for Acknowledge bit 12 to be cleared
    log.info(f"Node {node.id}: Waiting for acknowledge to be cleared")
    wait_for_statusword_flags(node, BIT(12), expected_flag_state=False)

    # Wait for Target Reached bit 10 to be set in Statusword
    log.info(f"Node {node.id}: Waiting for target reached")
    wait_for_statusword_flags(node, BIT(10))

    # Read the actual position after target is reached
    current_pos = node.sdo["Position Actual Value"].raw
    log.info(f"Node {node.id}: Reached position {current_pos}")

    cleanup_profile_position(node)

def position_mode_constant_velocity(node: BaseNode402) -> None:
    """

    Args:
        node (BaseNode402): The CANopen device node.

    Returns:
        None
    """
    log.info("Example normal position")

    setup_profile_position(node)


    target_position = 10000
    target_velocity = 50 * INC_PER_MM

    cw = 0x0F | BIT(9)
    set_controlword(node, controlword=cw)

    log.info(f"Node {node.id}: Sending target position {target_position}")
    set_target_position(node, target_position=target_position, profile_velocity=target_velocity)

    # Set bit 4 to signal new set-point
    log.info(f"Node {node.id}: Setting new set-point to to initiate motion")
    set_controlword(node, controlword=cw | BIT(4))

    # Wait for Acknoledge bit 12 to be set in Statusword
    log.info(f"Node {node.id}: Waiting for acknowledged to be set")
    wait_for_statusword_flags(node, BIT(12))

    # Clear bit 4 after acknowledgment
    set_controlword(node, controlword=cw & ~BIT(4))

    # Wait for Acknowledge bit 12 to be cleared
    log.info(f"Node {node.id}: Waiting for acknowledge to be cleared")
    wait_for_statusword_flags(node, BIT(12), expected_flag_state=False)

    # Wait for Target Reached bit 10 to be set in Statusword
    log.info(f"Node {node.id}: Waiting for target reached")
    wait_for_statusword_flags(node, BIT(10))

    # Read the actual position after target is reached
    current_pos = node.sdo["Position Actual Value"].raw
    log.info(f"Node {node.id}: Reached position {current_pos}")

    cleanup_profile_position(node)

def position_mode_set_of_set_points(node: BaseNode402) -> None:
    """

    Args:
        node (BaseNode402): The CANopen device node.

    Returns:
        None
    """
    log.info("Example normal position")

    setup_profile_position(node)

    target_position_1 = 10000
    target_velocity_1 = 50 * INC_PER_MM

    target_position_2 = 15000
    target_velocity_2 = 25 * INC_PER_MM

    cw = 0x0F | BIT(9)
    set_controlword(node, controlword=cw)

    # Configure the first motion
    log.info(f"Node {node.id}: Sending target position {target_position_1}")
    set_target_position(node, target_position=target_position_1, profile_velocity=target_velocity_1)

    # Set bit 4 to signal new set-point and start the motion
    log.info(f"Node {node.id}: Setting new set-point to to initiate motion")
    set_controlword(node, controlword=cw | BIT(4))

    # Wait for Acknowledge bit 12 to be set in Statusword
    log.info(f"Node {node.id}: Waiting for acknowledged to be set")
    wait_for_statusword_flags(node, BIT(12))

    # Clear bit 4 after acknowledgment has been set
    set_controlword(node, controlword=cw & ~BIT(4))

    # Wait for Acknowledge bit 12 to be cleared
    log.info(f"Node {node.id}: Waiting for acknowledge to be cleared")
    wait_for_statusword_flags(node, BIT(12), expected_flag_state=False)

    # Start of second motion
    # Configure the second motion
    log.info(f"Node {node.id}: Sending target position {target_position_2}")
    set_target_position(node, target_position=target_position_2, profile_velocity=target_velocity_2)

    # Set bit 4 to signal new set-point and start the motion
    log.info(f"Node {node.id}: Setting new set-point to to initiate motion")
    set_controlword(node, controlword=cw | BIT(4))

    # Wait for Acknowledge bit 12 to be set in Statusword
    log.info(f"Node {node.id}: Waiting for acknowledged to be set")
    wait_for_statusword_flags(node, BIT(12))

    # Clear bit 4 after acknowledgment has been set
    set_controlword(node, controlword=cw & ~BIT(4))

    # Wait for Acknowledge bit 12 to be cleared
    log.info(f"Node {node.id}: Waiting for acknowledge to be cleared")
    wait_for_statusword_flags(node, BIT(12), expected_flag_state=False)

    # End of second motion

    # Wait for Target Reached bit 10 to be set in Statusword
    log.info(f"Node {node.id}: Waiting for target reached")
    wait_for_statusword_flags(node, BIT(10))

    # Read the actual position after target is reached
    current_pos = node.sdo["Position Actual Value"].raw
    log.info(f"Node {node.id}: Reached position {current_pos}")

    cleanup_profile_position(node)

def position_mode_trajectory(node: BaseNode402) -> None:
    """

    Args:
        node (BaseNode402): The CANopen device node.

    Returns:
        None
    """
    log.info("Example normal position")

    setup_profile_position(node)

    # Example data [position, velocity]
    position_data = [
        [13500, 25000],
        [12450, 24300],
        [11400, 23500],
        [10350, 22600],
        [9300, 21600],
        [8250, 20500],
        [7200, 19400],
        [6150, 18200],
        [5100, 17000],
        [4050, 15800],
        [3000, 14600],
        [1950, 13400],
        [900, 12200],
        [-150, 11000],
        [-1200, 9950],
        [-2250, 9050],
        [-3300, 8250],
        [-4350, 7550],
        [-5400, 7250],
        [-6450, 7000],
        [-7500, 6000],
        [-8550, 5000],
        [-9600, 4000],
        [-10800, 3000],
        [-13500, 2000],
    ]


    cw = 0x0F | BIT(9)
    set_controlword(node, controlword=cw)

    for pos, vel in position_data:
        # Save the target position and velocity
        set_target_position(node, target_position=pos, profile_velocity=vel)

        # Set bit 4 to signal new set-point and start the motion
        set_controlword(node, controlword=cw | BIT(4))

        # Wait for Acknowledge bit 12 to be set in Statusword
        wait_for_statusword_flags(node, BIT(12))

        # Clear bit 4 after acknowledgment has been set
        set_controlword(node, controlword=cw & ~BIT(4))

        # Wait for Acknowledge bit 12 to be cleared
        wait_for_statusword_flags(node, BIT(12), expected_flag_state=False)


    # Wait for Target Reached bit 10 to be set in Statusword
    log.info(f"Node {node.id}: Waiting for target reached")
    wait_for_statusword_flags(node, BIT(10))

    # Read the actual position after target is reached
    current_pos = node.sdo["Position Actual Value"].raw
    log.info(f"Node {node.id}: Reached position {current_pos}")

    time.sleep(1)
    #
    # cleanup_profile_position(node)

def view_csv():
    # Load the CSV
    df = pd.read_csv('position_log.csv')

    # Plot
    plt.figure(figsize=(8, 4))
    plt.plot(df['timestamp'], df['position_actual_value'], linestyle='-')
    plt.xlabel('timestamp')
    plt.ylabel('Position Actual Value')
    plt.title('Position over Time')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def on_position_update(pdo):
    # You could optimise this time.time() usage for more accurate timings
    writer.writerow([time.time()-time_start, pdo['Position Actual Value'].raw])


def main() -> None:
    """
    Entry point for executing the homing and profile position mode.

    Returns:
        None
    """
    try:
        network, absolute_path = setup_network()
        network.check()

        node = BaseNode402(NODE_ID, absolute_path)
        network.add_node(node)

        configure_node(node)

        tpdo = node.tpdo[3]

        # Change this value to select one of the examples (1 - 4)
        example = 4
        
        if example == 1:
            log.info("======== Example 1: Profile position mode with default jerk-limited motion")
            homing(node)
            time.sleep(0.25)
            tpdo.add_callback(on_position_update)
            position_mode_normal(node)
            time.sleep(0.5)

        elif example == 2:
            log.info("======== Example 2: Profile position mode using constant velocity mode")
            homing(node)
            time.sleep(0.25)
            tpdo.add_callback(on_position_update)
            position_mode_constant_velocity(node)
            time.sleep(0.5)

        elif example == 3:
            log.info("======== Example 3: Profile position mode using set of set-points (2 target positions)")
            homing(node)
            time.sleep(0.25)
            tpdo.add_callback(on_position_update)
            position_mode_set_of_set_points(node)
            time.sleep(0.5)

        elif example == 4:
            log.info("======== Example 4: Profile position mode for set_of_set_points")
            homing(node)
            time.sleep(0.5)
            tpdo.add_callback(on_position_update)
            position_mode_trajectory(node)
            time.sleep(0.5)

        else:
            log.error("Invalid example")

        tpdo.callbacks.clear()

        csvfile.close()

        view_csv()

    except KeyboardInterrupt:
        log.info("Keyboard interrupt detected, stopping program..")
        pass

    except Exception as e:
        log.error(f"Error occured: {e}")

if __name__ == "__main__":
    csvfile = open('position_log.csv', 'w', newline='')
    writer = csv.writer(csvfile)
    writer.writerow(['timestamp', 'position_actual_value'])
    time_start = time.time()

    main()
