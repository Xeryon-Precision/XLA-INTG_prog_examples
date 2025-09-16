"""
verify_communication.py

This script verifies communication with a CANopen node.

Typical usage:
    python check_communication.py

Behavior:
    • On successful communication:
        [INFO] Node <NODE_ID>: Communication successful
    • On failure (e.g. timeout, NMT error):
        [ERROR] Failed to connect to node <NODE_ID>

This script is primarily intended for quick connectivity checks or diagnostic
purposes during development, production testing, or troubleshooting.

© 2025 Xeryon – All rights reserved.
"""
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import logging

from canopen import BaseNode402, nmt

try:
    from settings import NODE_ID
    from common.utils import setup_network
except ImportError:
    from examples.settings import NODE_ID
    from examples.common.utils import setup_network

# ----- Logging setup -----
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)
logging.getLogger("canopen").setLevel(logging.WARNING)


def main() -> None:
    """
    Verifies communication with the node.

    Returns:
        On error:
            [ERROR] Failed to connect to node 32.

        On success:
            [INFO] Node 32: Communication successful.
    """
    network = None
    try:
        network, eds_path = setup_network()
        node = BaseNode402(NODE_ID, eds_path)
        network.add_node(node)

        node.nmt.state = "RESET"

        # Increase the timeout (in seconds) if necessary
        node.nmt.wait_for_bootup(timeout=2.0) 

        log.info(f"Node {node.id}: Communication is succesfull")

    except KeyboardInterrupt:
        log.info("Keyboard interrupt detected, stopping program..")
        pass

    except nmt.NmtError:
        log.error(f"Failed to connect to Node")
        pass

    except Exception as e:
        log.error(f"Error occured: {e}")
        raise e
    
    finally:
        if network:
            network.disconnect()


if __name__ == "__main__":
    main()
    sys.exit(0)
