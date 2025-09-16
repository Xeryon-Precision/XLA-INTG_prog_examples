"""
change_node_ids.py

This script will give all the connected nodes a unique Node ID.

Description:
    This script connects to a CANopen network and performs a full
    Layer Setting Services (LSS) reconfiguration of all connected devices.
    The process involves:
        1. Checking for devices already configured with Node IDs.
        2. Unconfiguring all nodes (resetting Node IDs).
        3. Scanning the network for available devices.
        4. Assigning unique Node IDs sequentially, starting from START_NODE_ID.
        5. Resetting the network so devices start using their new Node IDs.
        6. Printing a configuration summary including Vendor ID, Product Code,
           and Serial Number for each device.

Usage:
    Run this script directly from the command line after connecting your
    CAN interface:

        python change_node_ids.py

    Make sure that:
        - The CAN interface, channel, and bitrate are correctly set in
          `settings.py` (CAN_INTERFACE, CAN_CHANNEL, CAN_BITRATE).
        - The devices on the CAN network are powered and in a state where
          they can respond to LSS requests.

Configuration:
    You can edit the value of `START_NODE_ID` at the top of this file to
    set a different starting Node ID for the first device. Each subsequent
    device will receive an incremented Node ID (START_NODE_ID + 1, +2, ...).

Exit Codes:
    0   - Success (Configuration process completed successfully)
    1   - Unexpected error occurred
    130 - Interrupted by user (Ctrl+C)

© 2025 Xeryon – All rights reserved.
"""
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import logging
import time

from canopen import Network

try:
    from common.utils import lss_check_configured_nodes, lss_scan_and_configure_nodes, lss_unconfigure_all_nodes
    from common.parameters import LSS_RESET_DELAY
    from settings import CAN_BITRATE, CAN_CHANNEL, CAN_INTERFACE
except ImportError:
    from examples.common.utils import lss_check_configured_nodes, lss_scan_and_configure_nodes, lss_unconfigure_all_nodes
    from examples.common.parameters import LSS_RESET_DELAY
    from examples.settings import CAN_BITRATE, CAN_CHANNEL, CAN_INTERFACE

# ---- Configuration ----------------------------------------------------------------
START_NODE_ID = 32              # The starting Node ID
# -----------------------------------------------------------------------------------

# ----- Logging setup -----
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)
logging.getLogger("canopen").setLevel(logging.WARNING)

def main():
    """
    Main execution function for the LSS configuration example to change all the Node IDs.
    
    Change the start_node_id value if a different first node id is expected.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """  
    
    log.info("CANopen LSS Configuration Example Starting...")
    log.info(f"Configuration: Interface={CAN_INTERFACE}, Channel={CAN_CHANNEL}")
    log.info(f"Node IDs will start from {START_NODE_ID}")
    
    network = None
    
    try:
        network = Network()
    
        log.info(f"Connecting to {CAN_INTERFACE} on channel {CAN_CHANNEL}...")
        network.connect(
            interface=CAN_INTERFACE,
            channel=CAN_CHANNEL,
            bitrate=CAN_BITRATE
        )
        log.info("Successfully connected to CAN network")
        
        log.info("-" * 60)
        configured_nodes = lss_check_configured_nodes(network)
        
        if configured_nodes:
            log.info("-" * 60)
            lss_unconfigure_all_nodes(network)
        
        log.info("-" * 60)
        devices = lss_scan_and_configure_nodes(network, START_NODE_ID)
        
        if devices:
            log.info("-" * 60)
            log.info("Applying final configuration...")
            network.nmt.state = 'RESET'
            time.sleep(LSS_RESET_DELAY)
        
        if not devices:
            log.info("No devices were configured")
            return
        
        log.info("=" * 60)
        log.info("CONFIGURATION SUMMARY")
        log.info("=" * 60)
        
        for device in devices:
            log.info(
                f"Node {device['assigned_node_id']:3d} | "
                f"Vendor: {device['vendor_id']:#06x} | "
                f"Product: {device['product_code']:#06x} | "
                f"Serial: {device['serial_number']:#010x}"
            )
        
        log.info("-" * 60)
        log.info(f"Total devices configured: {len(devices)}")
        log.info("=" * 60)
        
        log.info("Configuration process completed successfully")
        return 0
        
    except KeyboardInterrupt:
        log.info("\nProcess interrupted by user")
        return 130
        
    except Exception as e:
        log.error(f"Unexpected error: {e}", exc_info=True)
        return 1
        
    finally:
        if network:
            try:
                network.disconnect()
                log.info("Disconnected from CAN network")
            except Exception as e:
                log.error(f"Error during disconnect: {e}")


if __name__ == "__main__":
    main()
    sys.exit(0)
