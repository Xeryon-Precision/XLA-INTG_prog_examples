"""
utils.py

This module provides reusable helper functions for working with CiA 402-compliant
CANopen devices.

© 2025 Xeryon – All rights reserved.
"""

import logging as log
import os
from typing import Tuple

import time
from canopen import Network, BaseNode402

from src.config import ControlMode, EDS_PATH, CAN_INTERFACE, CAN_CHANNEL, CAN_DEFAULT_BITRATE, DEFAULT_TIMEOUT, P402CWState

# -----------------------------------------------------------------------------
# Bit manipulation utilities
# -----------------------------------------------------------------------------
BIT = lambda n: 1 << n
CLRBIT = lambda n: ~(1 << n)


def transition_402_cw_state(node: BaseNode402, state: P402CWState, timeout: float = DEFAULT_TIMEOUT) -> None:
    """
    Transitions the device through the CiA 402 state machine using controlword updates,
    and waits until the requested state is confirmed.

    This function updates the node's state attribute, which issues the appropriate controlword
    to the drive. It then polls the device's current state until it matches the requested target.

    Args:
        node (BaseNode402): The CANopen device node.
        state (str): Desired CiA 402 state (e.g., "READY TO SWITCH ON", "OPERATION ENABLED").
        timeout (float): Maximum duration to wait for the state transition (in seconds).

    Raises:
        TimeoutError: If the node fails to reach the desired state within the timeout period.
    """
    node.state = state

    time_limit = time.monotonic() + timeout
    while node.state != state:
        if time.monotonic() > time_limit:
            raise TimeoutError(f"Node {node.id}: Timeout while changing 402 state to '{state}'")

        time.sleep(0.1)

    mode_set = node.sdo["Mode of operation"].raw
    mode_active = node.sdo["Mode of operation display"].raw
    log.info(
        f"Node {node.id}: 402 State = {node.state}, NMT State = {node.nmt.state}, "
        f"Mode [set: {mode_set}; active: {mode_active}]")


def set_control_mode(node: BaseNode402, new_mode: ControlMode, timeout: float = DEFAULT_TIMEOUT) -> None:
    """
    Sets the desired control mode and verifies it is accepted by the device.

    Args:
        node (BaseNode402): The CANopen device node.
        new_mode (ControlMode): Desired control mode from config.ControlMode.
        timeout (float): Max time to wait for mode confirmation (in seconds).

    Raises:
        TimeoutError: If the mode is not confirmed within the timeout.
    """
    node.sdo["Mode of operation"].raw = new_mode.value

    time_limit = time.monotonic() + timeout
    while time.monotonic() < time_limit:
        if node.sdo["Mode of operation"].raw == new_mode.value:
            log.info(f"Node {node.id}: Control mode confirmed: {new_mode.name}")
            return

        time.sleep(0.1)

    raise TimeoutError(f"Node {node.id}: Failed to confirm control mode '{new_mode.name}'")


def wait_for_statusword_flags(
        node: BaseNode402,
        flags: int,
        expected_flag_state: bool = True,
        time_interval: float = 0.1,
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
    """
    flag_match = lambda sw: (sw & flags) == flags if expected_flag_state else (sw & flags) == 0

    time_limit = time.monotonic() + timeout
    while time.monotonic() < time_limit:
        statusword = node.sdo["Statusword"].raw
        log.debug(f"Node {node.id}: Statusword = {statusword:#06x}")
        if flag_match(statusword):
            return
        time.sleep(time_interval)

    raise TimeoutError(
        f"Node {node.id}: Timeout waiting for flags {flags:#06x} to be "
        f"{'set' if expected_flag_state else 'cleared'} in statusword."
    )


def setup_network(
        interface: str = CAN_INTERFACE,
        channel: str = CAN_CHANNEL,
        bitrate: int = CAN_DEFAULT_BITRATE
) -> Tuple[Network, str]:
    """
    Initializes the CANopen network and validates the EDS file path.

    Args:
        interface (str): CAN interface type (e.g., "slcan", "socketcan").
        channel (str): Interface channel (e.g., "COM3", "/dev/ttyACM0").
        bitrate (int): Bitrate in bps (e.g., 125_000).

    Returns:
        Tuple[Network, str]: The connected CANopen network object and absolute EDS file path.

    Raises:
        FileNotFoundError: If the EDS file does not exist.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    eds_path = os.path.abspath(os.path.join(script_dir, EDS_PATH))

    if not os.path.exists(eds_path):
        raise FileNotFoundError(f"EDS file not found: {eds_path}")

    log.info(f"EDS path resolved: {eds_path}")
    log.info(f"Object Dictionary documentation: {os.path.dirname(eds_path)}/xeryon_xla_5_eds_docu.txt")

    network = Network()
    network.connect(interface=interface, channel=channel, bitrate=bitrate)
    network.check()

    return network, eds_path
