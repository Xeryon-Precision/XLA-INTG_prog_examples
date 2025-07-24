"""
utils.py

This module provides reusable helper functions for working with CiA 402-compliant
CANopen devices.

© 2025 Xeryon – All rights reserved.
"""

import logging as log
import os
import time
from typing import Tuple

from canopen import Network, BaseNode402

from config import (
    NodeOperationMode, EDS_PATH, CAN_INTERFACE, CAN_CHANNEL, CAN_DEFAULT_BITRATE, DEFAULT_TIMEOUT, NodeState,
    HomingMethod,
    DEFAULT_BOOTUP_TIMEOUT, DEFAULT_SDO_TIMEOUT, NMTState
)

# -----------------------------------------------------------------------------
# Bit manipulation utilities
# -----------------------------------------------------------------------------
BIT = lambda n: 1 << n
CLRBIT = lambda n: ~(1 << n)


# -----------------------------------------------------------------------------
# Node Functions
# -----------------------------------------------------------------------------
def setup_network(
        interface: str = CAN_INTERFACE,
        channel: str = CAN_CHANNEL,
        bitrate: int = CAN_DEFAULT_BITRATE,
        eds_relative_path: str = EDS_PATH  # <-- import this from config
) -> Tuple[Network, str]:
    """
    Initializes the CANopen network and validates the EDS file path.

     Args:
        interface (str): The socketCAN interface to use (e.g. 'can0').
        channel (str): The channel name for the CAN interface.
        bitrate (int): Bus bitrate in kbps.
        eds_relative_path (str): Relative path to the device's EDS file.

    Returns:
        Tuple[Network, str]:
            network: An initialized `canopen.Network` object
            eds_path: Path to the EDS file
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))

    eds_path = (os.path.abspath(os.path.join(script_dir, eds_relative_path))
                if not os.path.isabs(eds_relative_path) else eds_relative_path)

    if not os.path.exists(eds_path):
        raise FileNotFoundError(f"EDS file not found: {eds_path}")

    log.info(f"EDS path resolved: {eds_path}")
    log.info(f"Object Dictionary documentation: {os.path.dirname(eds_path)}/xeryon_xla_5_eds_docu.txt")

    network = Network()
    network.connect(interface=interface, channel=channel, bitrate=bitrate)
    network.check()

    return network, eds_path


def configure_node(node: BaseNode402) -> None:
    """
    Resets the node, waits for bootup, loads configuration, and enables the state machine.

    Args:
        node (BaseNode402): The CANopen device node.

    Returns:
        None
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

    log.info(f"Node {node.id}: Read PDOs")
    node.tpdo.read()
    node.rpdo.read()

    for i, tpdo in node.tpdo.items():
        log.info(f"TPDO{i} ({tpdo.cob_id:#04x})")
        for var in tpdo.map:
            if var.subindex:
                log.info(f"  - {var.name} ({var.index:#04x}[{var.subindex}])")
            else:
                log.info(f"  - {var.name} ({var.index:#04x})")

    for i, rpdo in node.rpdo.items():
        log.info(f"TPDO{i} ({rpdo.cob_id:#04x})")
        for var in rpdo.map:
            if var.subindex:
                log.info(f"  - {var.name} ({var.index:#04x}[{var.subindex}])")
            else:
                log.info(f"  - {var.name} ({var.index:#04x})")


def reset_node(node: BaseNode402) -> None:
    """
    Resets the node, waits for bootup, loads configuration, and enables the state machine.

    Args:
        node (BaseNode402): The CANopen device node.

    Returns:
        None
    """
    log.info(f"Node {node.id}: Resetting the device to apply changes.")
    node.nmt.state = NMTState.RESET
    node.nmt.wait_for_bootup(DEFAULT_BOOTUP_TIMEOUT)


def set_node_state(node: BaseNode402, state: NodeState, timeout: float = DEFAULT_TIMEOUT) -> None:
    """
    Transitions the device through the CiA 402 state machine using controlword updates,
    and waits until the requested state is confirmed.

    This function updates the node's state attribute, which issues the appropriate controlword
    to the drive. It then polls the device's current state until it matches the requested target.

    Args:
        node (BaseNode402): The CANopen device node.
        state (NodeState): Desired CiA 402 state (e.g., NodeState.SWITCH_ON).
        timeout (float): Maximum duration to wait for the state transition (in seconds).

    Raises:
        TimeoutError: If the node fails to reach the desired state within the timeout period.

    Returns:
        None
    """
    node.state = state.value

    time_limit = time.monotonic() + timeout
    while time.monotonic() < time_limit:
        if node.state == state.value:
            log.info(f"Node {node.id}: State = {node.state}")
            return

        time.sleep(0.1)

    raise TimeoutError(f"Node {node.id}: Timeout while changing node state to '{state.value}'")


def set_node_operation_mode(node: BaseNode402, mode: NodeOperationMode, timeout: float = DEFAULT_TIMEOUT) -> None:
    """
    Sets the desired control mode and verifies it is accepted by the device.

    Args:
        node (BaseNode402): The CANopen device node.
        mode (NodeOperationMode): Desired control mode from config.ControlMode.
        timeout (float): Max time to wait for mode confirmation (in seconds).

    Raises:
        TimeoutError: If the mode is not confirmed within the timeout.

    Returns:
        None
    """
    node.sdo["Mode of operation"].raw = mode.value

    time_limit = time.monotonic() + timeout
    while time.monotonic() < time_limit:
        if node.sdo["Mode of operation"].raw == mode.value:
            log.info(f"Node {node.id}: Control mode confirmed: {mode.name}")
            return

        time.sleep(0.1)

    raise TimeoutError(f"Node {node.id}: Failed to confirm control mode '{mode.name}'")


# -----------------------------------------------------------------------------
# Statusword flags
# -----------------------------------------------------------------------------
def wait_for_statusword_flags(
        node: BaseNode402,
        flags: int,
        expected_flag_state: bool = True,
        time_interval: float = 0.001,
        timeout: float = DEFAULT_TIMEOUT
) -> None:
    """
    Waits for specific bits in the device's statusword to become set or cleared.

    Args:
        node (BaseNode402): The CANopen device node.
        flags (int): Bitmask (use BIT(n)) to test against statusword (0x6041).
        expected_flag_state (bool): True = wait for bits to be set, False = wait for them to clear.
        time_interval (float): Time between polling attempts (seconds).
        timeout (float): Max time to wait before raising exception (seconds).

    Raises:
        TimeoutError: If the flag condition is not met within the timeout.

    Returns:
        None
    """
    flag_match = lambda sw: (sw & flags) == flags if expected_flag_state else (sw & flags) == 0

    time_limit = time.monotonic() + timeout
    while time.monotonic() < time_limit:
        statusword = get_statusword(node)

        if flag_match(statusword):
            return

        time.sleep(time_interval)

    raise TimeoutError(
        f"Node {node.id}: Timeout waiting for flags {flags:#06x} to be "
        f"{'set' if expected_flag_state else 'cleared'} in statusword."
    )


# -----------------------------------------------------------------------------
# PDOs
# Control Word (0x6040)
# Status Word (0x6041)
# Target Position (0x607A)
# Position Actual Value (0x6064)
# -----------------------------------------------------------------------------
def set_controlword(node: BaseNode402, controlword: int = None) -> None:
    """
    Writes a new controlword to the device and transmits the RPDO.

    Args:
        node (BaseNode402): The CANopen device node.
        controlword (int, optional): The new control word value to send.
            If None, no action is taken.

    Returns:
        None
    """
    if controlword is not None:
        node.rpdo[3]["Controlword"].raw = controlword
        node.rpdo[3].transmit()


def get_controlword(node: BaseNode402) -> int:
    """
    Reads the current controlword from the last received RPDO.

    Args:
        node (BaseNode402): The CANopen device node.

    Returns:
        int: The raw control word value (0x6040).
    """
    return node.rpdo[3]["Controlword"].raw


def get_statusword(node: BaseNode402) -> int:
    """
    Reads the current statusword from the last received TPDO.

    Args:
        node (BaseNode402): The CANopen device node.

    Returns:
        int: The raw status word value (0x6041).
    """
    return node.tpdo[3]["Statusword"].raw


def get_actual_position(node: BaseNode402) -> int:
    """
    Reads the current actual position from the last received TPDO.

    Args:
        node (BaseNode402): The CANopen device node.

    Returns:
        int: The raw actual position value (0x6064).
    """
    return node.tpdo[3]["Position Actual Value"].raw


def set_target_position(node: BaseNode402, target_position: int = None) -> None:
    """
    Writes a new target position to the device and transmits the RPDO.

    Args:
        node (BaseNode402): The CANopen device node.
        target_position (int, optional): The target position value to send.
            If None, no action is taken.

    Returns:
        None
    """
    if target_position is not None:
        node.rpdo[3]["Target Position"].raw = target_position
        node.rpdo[3].transmit()


def get_target_position(node: BaseNode402) -> int:
    """
    Reads the last‐set target position from the last transmitted RPDO.

    Args:
        node (BaseNode402): The CANopen device node.

    Returns:
        int: The raw target position value (0x607A).
    """
    return node.rpdo[3]["Target Position"].raw


# -----------------------------------------------------------------------------
# Homing
# -----------------------------------------------------------------------------
def homing(node: BaseNode402, direction_positive: bool = True, offset: int = 0) -> None:
    """
    Performs a homing operation using the configured homing method.

    Args:
        node (BaseNode402): The CANopen device node.
        direction_positive (bool): True = Homing method to use is positive index, otherwise negative.
        offset (int): The homing offset to set in counts.

    Raises:
        RuntimeError: If the homing failed to be attained.

    Returns:
        None
    """
    log.info(f"Node {node.id}: Start Homing")

    # Set CiA 402 State machine to SWITCH ON DISABLED
    set_node_state(node, NodeState.SWITCH_ON_DISABLED)

    # Set CiA 402 State machine to READY TO SWITCH ON
    set_node_state(node, NodeState.READY_TO_SWITCH_ON)

    # Set CiA 402 State machine to SWITCHED ON
    set_node_state(node, NodeState.SWITCH_ON)

    # Set mode to Homing
    set_node_operation_mode(node, NodeOperationMode.HOMING)

    # Set CiA 402 State machine to OPERATION ENABLED
    set_node_state(node, NodeState.OPERATION_ENABLED)

    # Set the homing offset
    node.sdo["Home offset"].raw = offset

    if direction_positive:
        method = HomingMethod.POS_INDEX
    else:
        method = HomingMethod.NEG_INDEX

    node.sdo["Homing method"].raw = method

    # Start homing (set bit 4)
    log.info(f"Node {node.id}: Starting homing with method {method}")
    set_controlword(node, 0x0F | BIT(4))

    time.sleep(0.5)

    try:
        log.info(f"Node {node.id}: Waiting for Homing attained")
        wait_for_statusword_flags(node, BIT(12))
    except Exception as e:
        log.error(f"Node {node.id}: Homing failed \n {e}")

        # Clear bit 4 when homing failed
        set_controlword(node, 0x0F)
        raise RuntimeError("Homing failed")

    # Clear bit 4 after homing is attained
    set_controlword(node, 0x0F)

    log.info(f"Node {node.id}: Homing completed")

    # Set CiA 402 State machine to SWITCHED ON
    set_node_state(node, NodeState.SWITCH_ON)
