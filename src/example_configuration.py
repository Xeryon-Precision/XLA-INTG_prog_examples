"""
example_configuration.py

Device provisioning script for Xeryon CANopen CiA-402 drives.

Performs configuration of logging, I/O, overrides, motion control,
and homing behavior. Saves settings to non-volatile memory.

Use this script during initial setup, diagnostics, or automated
provisioning workflows. A manual device reset is required to
apply all configured settings.

For more information, please read the README:
- README_configuration.md

© 2025 Xeryon – All rights reserved.
"""

import logging

from canopen import BaseNode402

from config import (
    ControlMode, DEFAULT_BOOTUP_TIMEOUT, DEFAULT_SDO_TIMEOUT,
    INC_PER_MM, LEDMask, NODE_ID, NMTState, RESTORE_ALL_DEFAULT_PARAMETERS, DEFAULT_STATUS_LOGGING,
    SAVE_ALL_PARAMETERS
)
from utils import setup_network, BIT

# ----- Logging setup -----
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)
logging.getLogger("canopen").setLevel(logging.WARNING)


def reset_and_setup_logging(node: BaseNode402) -> None:
    """
    Performs a factory reset and enables runtime logging options on the device.

    Args:
        node (BaseNode402): The CANopen device node to configure.
    """
    log.info(f"Node {node.id}: Performing factory reset and enabling logging...")

    # Restore all Default Parameters
    node.sdo["Restore Default Parameters"][1].raw = RESTORE_ALL_DEFAULT_PARAMETERS

    # Enable logging options
    node.sdo["Status logging verbosity flags"].raw = DEFAULT_STATUS_LOGGING

    # Switch to mode profile position
    node.sdo["Mode of operation"].raw = ControlMode.TRAJECTORY


def configure_io(node: BaseNode402) -> None:
    """
    Configures digital and analog I/O mappings, and LED behavior.

    Args:
        node (BaseNode402): The CANopen device node to configure.
    """
    log.info(f"Node {node.id}: Configuring I/O and LEDs...")
    node.sdo["I/O Configuration"][1].raw = 1  # AI1 / speed pin config
    node.sdo["I/O Configuration"][2].raw = 1  # DI1 config
    node.sdo["I/O Configuration"][3].raw = 1  # DI2 config
    node.sdo["I/O Configuration"][4].raw = 1  # DI3 config

    node.sdo["LED Configuration"].raw = LEDMask.ALL


def configure_input_overrides(node: BaseNode402) -> None:
    """
    Configures optional overrides for digital inputs such as enable, direction,
    speed control, and homing trigger.

    Args:
        node (BaseNode402): The CANopen device node to configure.
    """
    log.info(f"Node {node.id}: Configuring input overrides...")

    enable_speed_override = False
    enable_direction_override = False
    enable_enable_override = False
    enable_homing_override = False

    override_cfg = 0

    if enable_enable_override:
        node.sdo["I/O Override settings"][1].raw = 0  # Enable
        override_cfg |= BIT(0)

    if enable_direction_override:
        node.sdo["I/O Override settings"][2].raw = 0  # Direction
        override_cfg |= BIT(1)

    if enable_speed_override:
        node.sdo["I/O Override settings"][3].raw = 0.4  # Speed
        override_cfg |= BIT(2)

    if enable_homing_override:
        node.sdo["I/O Override settings"][4].raw = 0  # Home
        override_cfg |= BIT(3)

    node.sdo["I/O Override Enable"].raw = override_cfg
    node.sdo["Hybrid control switch point"].raw = 40


def configure_frequency(node: BaseNode402):
    """
    Configures motor frequency bounds.

    Args:
        node (BaseNode402): The CANopen device node to configure.
    """
    frequency = 85000
    node.sdo["Motor frequency bounds"][1].raw = frequency  # Minimum
    node.sdo["Motor frequency bounds"][2].raw = frequency  # Nominal
    node.sdo["Motor frequency bounds"][3].raw = frequency  # Maximum


def configure_motion_parameters(node: BaseNode402) -> None:
    """
    Configures motor phase, duty cycle, and trajectory profile parameters.

    Args:
        node (BaseNode402): The CANopen device node to configure.
    """
    log.info(f"Node {node.id}: Configuring motion parameters...")

    # Motor phase
    node.sdo["Motor phase bounds"][1].raw = 0  # Minimum
    node.sdo["Motor phase bounds"][2].raw = 90  # Nominal
    node.sdo["Motor phase bounds"][3].raw = 90  # Maximum

    # Duty cycle
    node.sdo["Motor duty cycle bounds"][1].raw = 20  # Minumum
    node.sdo["Motor duty cycle bounds"][2].raw = 50  # Nominal
    node.sdo["Motor duty cycle bounds"][3].raw = 50  # Maximum

    # Trajectory parameters
    node.sdo["Max profile velocity"].raw = int(400 * INC_PER_MM)  # Max velocity (inc/s)         | 400 mm/s
    node.sdo["Profile velocity"].raw = int(200 * INC_PER_MM)  # Target velocity (inc/s)      | 200 mm/s
    node.sdo["Profile acceleration"].raw = int(1000 * INC_PER_MM)  # Target acceleration (inc/s²) | 1000 mm/s²
    node.sdo["Max acceleration"].raw = int(3000 * INC_PER_MM)  # Max acceleration (inc/s²)    | 3000 mm/s²
    node.sdo["Profile jerk"][1].raw = int(1_000_000 * INC_PER_MM)  # Profile Jerk (inc/s³)        | 1_000_000 mm/s³

    # Position limits (disabled)
    node.sdo["Software position limit"][1].raw = 0  # Min position limit
    node.sdo["Software position limit"][2].raw = 0  # Max position limit


def configure_homing_parameters(node: BaseNode402) -> None:
    """
    Configures the homing procedure: offset, step size, tolerance, and speed.

    Args:
        node (BaseNode402): The CANopen device node to configure.
    """
    log.info(f"Node {node.id}: Configuring homing parameters...")

    # Homing position
    node.sdo["Home offset"].raw = 0  # Home offset

    # Homing method
    node.sdo["Homing parameters"][1].raw = 250  # Step size
    node.sdo["Homing parameters"][2].raw = 2  # Standstill Tolerance
    node.sdo["Homing parameters"][3].raw = 100  # Standstill time (ms)

    # Homing speed
    node.sdo["Homing speeds"][2].raw = 50  # Homing Speed during search for zero
    node.sdo["Homing acceleration"].raw = 10_000  # Homing acceleration


def save_configuration(node: BaseNode402) -> None:
    """
    Saves all parameter changes on the device.

    Args:
        node (BaseNode402): The CANopen device node to save.
    """
    log.info(f"Node {node.id}: Saving configuration to flash...")

    # Save all Parameters
    node.sdo["Store Parameter Field"][1].raw = SAVE_ALL_PARAMETERS


def main() -> None:
    """
    Entry point. Sets up the network and applies all configurations.
    """
    try:
        network, eds_path = setup_network()
        node = BaseNode402(NODE_ID, eds_path)
        network.add_node(node)

        log.info(f"Node {NODE_ID}: Connecting to CAN network...")

        node.nmt.state = NMTState.RESET
        node.nmt.wait_for_bootup(DEFAULT_BOOTUP_TIMEOUT)
        node.sdo.RESPONSE_TIMEOUT = DEFAULT_SDO_TIMEOUT

        log.info(f"Node {node.id}: Booted. Current NMT state: {node.nmt.state}")
        node.nmt.state = NMTState.OPERATIONAL
        log.info(f"Node {node.id}: Switched to OPERATIONAL state")

        reset_and_setup_logging(node)

        configure_io(node)

        # configure_frequency()

        configure_input_overrides(node)

        configure_motion_parameters(node)

        configure_homing_parameters(node)

        save_configuration(node)

        log.warning(f"Node {node.id}: Configuration complete. Please reset the device to apply changes.")

    except KeyboardInterrupt:
        log.info("Keyboard interrupt detected, stopping program..")
        pass

    except Exception as e:
        log.error(f"Error occured: {e}")


if __name__ == "__main__":
    main()
