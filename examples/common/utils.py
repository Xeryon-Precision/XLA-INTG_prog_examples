"""
utils.py

This module provides reusable helper functions for working with CiA 402-compliant
CANopen devices.

© 2025 Xeryon – All rights reserved.
For demonstration purposes only. See README for disclaimer.
"""

import logging as log
import os
import time
from typing import Tuple, List, Optional

from can import CanError
from canopen import Network, BaseNode402, SdoAbortedError
from canopen.lss import LssError
from canopen.nmt import NmtError

try:
    from common.parameters import (
        NodeOperationMode, HomingMethod, NodeState, NMTState, LSS_SCAN_DELAY, LSS_RESET_DELAY, LSS_UNCONFIGURED_NODE_ID
    )
    from settings import (
        EDS_PATH, CAN_INTERFACE, CAN_CHANNEL, CAN_BITRATE, DEFAULT_TIMEOUT,
        DEFAULT_BOOTUP_TIMEOUT, DEFAULT_SDO_TIMEOUT
    )
except ImportError:
    from examples.common.parameters import (
        NodeOperationMode, HomingMethod, NodeState, NMTState, LSS_SCAN_DELAY, LSS_RESET_DELAY, LSS_UNCONFIGURED_NODE_ID
    )
    from examples.settings import (
        EDS_PATH, CAN_INTERFACE, CAN_CHANNEL, CAN_BITRATE, DEFAULT_TIMEOUT,
        DEFAULT_BOOTUP_TIMEOUT, DEFAULT_SDO_TIMEOUT
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
        bitrate: int = CAN_BITRATE,
        eds_relative_path: str = "../" + EDS_PATH
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
# Profile velocity (0x607F)
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
        node.rpdo[1]["Controlword"].raw = controlword
        node.rpdo[1].transmit()


def get_controlword(node: BaseNode402) -> int:
    """
    Reads the current controlword from the last received RPDO.

    Args:
        node (BaseNode402): The CANopen device node.

    Returns:
        int: The raw control word value (0x6040).
    """
    return node.rpdo[1]["Controlword"].raw


def get_statusword(node: BaseNode402) -> int:
    """
    Reads the current statusword from the last received TPDO.

    Args:
        node (BaseNode402): The CANopen device node.

    Returns:
        int: The raw status word value (0x6041).
    """
    return node.tpdo[1]["Statusword"].raw


def get_actual_position(node: BaseNode402) -> int:
    """
    Reads the current actual position from the last received TPDO.

    Args:
        node (BaseNode402): The CANopen device node.

    Returns:
        int: The raw actual position value (0x6064).
    """
    return node.tpdo[3]["Position Actual Value"].raw


def set_target_position(node: BaseNode402, target_position: int = None, profile_velocity: int = None) -> None:
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
        
    if profile_velocity is not None:
        node.rpdo[3]["Profile velocity"].raw = profile_velocity
    
    if target_position is not None or profile_velocity is not None:
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
def homing(node: BaseNode402, direction_positive: bool = True, offset: Optional[int] = None) -> None:
    """
    Performs a homing operation using the configured homing method.

    Args:
        node (BaseNode402): The CANopen device node.
        direction_positive (bool): True = Homing method to use is positive index, otherwise negative.
        offset ( Optional[int]): The homing offset to set in counts, or None if the stored parameter is used.

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

    # Set the homing offset
    if offset is not None:
        node.sdo["Home offset"].raw = offset

    if direction_positive:
        method = HomingMethod.POS_INDEX
    else:
        method = HomingMethod.NEG_INDEX

    node.sdo["Homing method"].raw = method

    # Set CiA 402 State machine to OPERATION ENABLED
    set_node_state(node, NodeState.OPERATION_ENABLED)

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


# -----------------------------------------------------------------------------
# LSS
# -----------------------------------------------------------------------------
def lss_check_configured_nodes(network: Network):
    """
    Check for currently configured nodes on the network.
    
    Args:
        network (Network): CANopen network instance
        
    Returns:
        List of configured node IDs
    """

    network.lss.send_switch_state_global(network.lss.CONFIGURATION_STATE)
    
    try:
        devices = network.lss.inquire_node_id()
        if devices:
            log.info(f"Found configured nodes")
            return devices
        else:
            log.info("No configured nodes found")
            return []
            
    except LssError:
        log.info("No configured nodes found on the network")
        return []
        
    finally:
        network.lss.send_switch_state_global(network.lss.WAITING_STATE)


def lss_unconfigure_all_nodes(network: Network):
    """
    Unconfigure all nodes by setting their IDs to 0xFF.
    
    Args:
        network (Network): CANopen network instance
        
    Returns:
        True if successful, False if errors occurred
    """
    log.info("Unconfiguring all nodes...")

    network.lss.send_switch_state_global(network.lss.CONFIGURATION_STATE)
    
    try:
        network.lss.configure_node_id(LSS_UNCONFIGURED_NODE_ID)
        log.debug(f"Set all node IDs to {LSS_UNCONFIGURED_NODE_ID:#02x}")

        try:
            network.lss.store_configuration()
            log.debug("Configuration stored")
        except Exception as e:
            log.warning(f"Could not store configuration: {e}")
            
        return True
        
    except LssError as e:
        log.warning(f"Error during unconfiguration: {e}")
        log.info("This can happen with multiple devices sharing the same ID")
        return False
        
    finally:
        network.lss.send_switch_state_global(network.lss.WAITING_STATE)

        log.info(f"Sending NMT command: 'RESET COMMUNICATION'")
        network.nmt.state = 'RESET COMMUNICATION'
        time.sleep(LSS_RESET_DELAY)


def lss_scan_and_configure_nodes(network: Network, first_node_id: int) -> List[dict]:
    """
    Scan for unconfigured nodes and assign sequential node IDs.
    
    Args:
        network (Network): CANopen network instance
        first_node_id (int): First Node ID to assign
        
    Returns:
        List of dictionaries containing device information and assigned IDs
    """
    log.info("Starting LSS Fast Scan for unconfigured nodes...")
    
    configured_devices = []
    current_node_id = first_node_id
    
    while True:
        network.lss.send_switch_state_global(network.lss.WAITING_STATE)
        time.sleep(LSS_SCAN_DELAY)

        try:
            found, device_info = network.lss.fast_scan()
            
            if not found:
                log.info("No more unconfigured nodes found")
                break

            vendor_id, product_code, revision, serial = device_info
            
            device = {
                'vendor_id': vendor_id,
                'product_code': product_code,
                'revision': revision,
                'serial_number': serial,
                'assigned_node_id': current_node_id
            }
            
            log.info(f"Found device: Vendor={vendor_id:#06x}, "
                       f"Product={product_code:#06x}, "
                       f"Serial={serial:#010x}")

            log.info(f"Assigning node ID {current_node_id}...")
            
            network.lss.configure_node_id(current_node_id)
            network.lss.store_configuration()
            
            configured_devices.append(device)
            current_node_id += 1
            
        except Exception as e:
            log.error(f"Error during scan/configuration: {e}")
            break
    
    return configured_devices


def lss_read_identity_via_sdo(node: BaseNode402) -> tuple[int, int, int, int]:
    """
    Reads the LSS identity by SDO commands

    Args:
        node (BaseNode402): The CANopen device node.

    Returns:
        Returns (vendor_id, product_code, revision_number, serial_number) from 0x1018.
        Tries named entries first, falls back to raw indices.
    """
    try:
        ident = node.sdo["Identity Object"] 
        vendor_id = int(ident["Vendor Id"].raw)
        product_code = int(ident["Product Code"].raw)
        revision_number = int(ident["Revision number"].raw)
        serial_number = int(ident["Serial number"].raw)
        return vendor_id, product_code, revision_number, serial_number
    except Exception:
        idx = node.sdo[0x1018]
        vendor_id = int(idx[1].raw)
        product_code = int(idx[2].raw)
        revision_number = int(idx[3].raw)
        serial_number = int(idx[4].raw)
        return vendor_id, product_code, revision_number, serial_number


def lss_configure_single_node_id(network: Network, node_id: int, new_node_id:int):
    """
    Changes the CANopen Node ID of a single device using LSS selective mode.
    
    Args:
        network (Network): Active CANopen network instance.
        node_id (int): Current Node ID of the target device.
        new_node_id (int): New Node ID to assign to the device.
        
    Returns:
        Status code indicating the result of the operation
    """
    
    eds_relative_path: str = "../" + EDS_PATH
    script_dir = os.path.dirname(os.path.abspath(__file__))
    eds_path = (os.path.abspath(os.path.join(script_dir, eds_relative_path))
                if not os.path.isabs(eds_relative_path) else eds_relative_path)

    node = BaseNode402(node_id, eds_path)
    network.add_node(node)

    log.info(f"[node {node_id}] Reading Identity (0x1018) via SDO...")
    try:
        vid, pid, rev, ser = lss_read_identity_via_sdo(node)
        log.info(
            f"[node {node_id}] Identity: VID=0x{vid:08X}, PID=0x{pid:08X}, "
            f"REV=0x{rev:08X}, SER=0x{ser:08X}"
        )
    except Exception as e:
        log.error(f"[node {node_id}] Failed to read identity via SDO: {e}")
        return 2

    try:
        log.info("Switching all nodes to LSS waiting state (global)...")
        network.lss.send_switch_state_global(waiting=True)
    except Exception as e:
        log.warning(f"Could not switch all nodes to waiting state: {e}")

    log.info("Selecting target via LSS selective using SDO-read identity...")
    try:
        network.lss.send_switch_state_selective(vid, pid, rev, ser)
    except Exception as e:
        log.error(f"LSS selective failed for identity (VID/PID/REV/SER): {e}")
        return 2
    
    try:
        current_id = network.lss.inquire_node_id()
        log.info(f"Device reports current Node ID: {current_id}")
    except Exception as e:
        log.error(f"Failed to inquire current Node ID via LSS: {e}")
        return 2

    if current_id != node_id:
        log.error(
            f"Safety stop: expected current Node ID {node_id}, "
            f"but device reports {current_id}. No changes applied."
        )
        return 3

    log.info(f"Configuring Node ID: {current_id} -> {new_node_id}")
    try:
        network.lss.configure_node_id(new_node_id)
        network.lss.store_configuration()
        log.info("Stored configuration successfully.")
    except Exception as e:
        log.error(f"Failed to set/store Node ID: {e}")
        return 1
    finally:
        try:
            network.lss.send_switch_state_global(waiting=True)
        except Exception:
            pass

    log.info("NMT RESET to apply new Node ID...")
    try:
        network.nmt.state = "RESET"
    except Exception as e:
        log.warning(f"NMT reset failed (device may still apply change): {e}")
    time.sleep(LSS_RESET_DELAY)

    log.info(f"Done. The device should now respond on Node ID {new_node_id}.")
    return 0


# -----------------------------------------------------------------------------
# ERRORS
# -----------------------------------------------------------------------------
def error_handler(exc: Exception, rethrow: bool = False) -> None:
    """
    Handles common CANopen / python-can exceptions with user-friendly messages.

    Args:
        exc (Exception):
        rethrow (bool):

    Returns:
        Optionally rethrows the exception after logging.
    """
    if isinstance(exc, SdoAbortedError):
        log.error(f"SDO transfer aborted: {exc}")

    elif isinstance(exc, LssError):
        log.error(f"LSS error during node discovery/configuration. \n {exc}")

    elif isinstance(exc, NmtError):
        msg = str(exc)
        if "Timeout waiting for boot-up message" in msg:
            log.error(
                "Timeout waiting for boot-up message.\n"
                "• Check the wiring and verify that the device is powered on.\n"
                "• Ensure that the configuration in settings.py (baudrate, channel, interface, node ID, etc.) "
                "matches the device and network."
            )
        else:
            log.error(f"NMT state transition failed: {msg}")

    elif isinstance(exc, CanError):
        log.error(f"CAN interface error — check interface name, drivers, and bus wiring. \n {exc}")

    elif isinstance(exc, TimeoutError):
        log.error(f"Operation timed out. Device may be offline or not responding. \n {exc}")

    elif isinstance(exc, FileNotFoundError):
        log.error(f"Device not found — check your CAN interface path.")

    elif isinstance(exc, ConnectionError):
        log.error(f"Failed to connect to CAN interface or gateway.")

    else:
        log.error(f"{exc.__class__.__name__}: {exc}")

    if rethrow:
        raise exc
