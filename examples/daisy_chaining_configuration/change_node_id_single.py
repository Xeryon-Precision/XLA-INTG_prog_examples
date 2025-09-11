"""
change_single_node_id_from_sdo.py 

Change one node's ID using SDO LSS.

Summary:
    1. Connect to node NODE_ID using SDO and read 0x1018 (Identity Object).
    2. Use LSS selective with the read identity to target exactly that device.
    3. Verify current Node ID == NODE_ID (safety).
    4. Configure Node ID to NEW_NODE_ID, store, and NMT RESET.

Usage:
    python change_single_node_id_from_sdo.py

Edit me:
    - NODE_ID and NEW_NODE_ID
    - settings.py must define CAN_INTERFACE, CAN_CHANNEL, CAN_BITRATE, EDS_PATH

Exit Codes:
    0   Success
    1   Unexpected error
    2   Node not reachable / SDO read failed
    3   Current Node ID mismatch (safety stop)
    130 Interrupted by user
    
© 2025 Xeryon – All rights reserved.
"""

import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import logging

from canopen import Network

from common.utils import lss_configure_single_node_id
from settings import CAN_BITRATE, CAN_CHANNEL, CAN_INTERFACE, EDS_PATH

# ---- Configuration ----------------------------------------------------------------
NODE_ID     = 32                 # Current (known) Node ID on the bus
NEW_NODE_ID = 1                  # New Node ID to assign
# -----------------------------------------------------------------------------------

# ----- Logging setup -----
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)
logging.getLogger("canopen").setLevel(logging.WARNING)

def main() -> int:
    """
    Main execution function for the LSS configuration example to change a single Node ID.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """  
    
    log.info("CANopen LSS Single-Node ID Change (SDO→LSS) Starting...")
    log.info(f"Interface={CAN_INTERFACE}, Channel={CAN_CHANNEL}, Bitrate={CAN_BITRATE}")
    log.info(f"Planned change: Node {NODE_ID} -> {NEW_NODE_ID}")

    network = None
    try:
        network = Network()
        log.info(f"Connecting to {CAN_INTERFACE} on {CAN_CHANNEL}...")
        network.connect(interface=CAN_INTERFACE, channel=CAN_CHANNEL, bitrate=CAN_BITRATE)
        log.info("Connected to CAN network.")
        return lss_configure_single_node_id(network, NODE_ID, NEW_NODE_ID)

    except KeyboardInterrupt:
        log.info("Interrupted by user.")
        return 130
    except Exception as e:
        log.error(f"Unexpected error: {e}", exc_info=True)
        return 1
    finally:
        if network:
            try:
                network.disconnect()
                log.info("Disconnected from CAN network.")
            except Exception as e:
                log.error(f"Error during disconnect: {e}")


if __name__ == "__main__":
    sys.exit(main())
