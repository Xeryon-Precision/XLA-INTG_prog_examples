"""
homing.py

Demonstration of CiA 402 Homing with Xeryon drives.

Performs a full state-machine-compliant homing operation.

For more information, please read the README:
- homing.md

© 2025 Xeryon – All rights reserved.
"""

import logging
import sys
import time

from canopen import BaseNode402

from common.utils import setup_network, homing, configure_node, error_handler
from settings import NODE_ID

# ----- Logging setup -----
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)
logging.getLogger("canopen").setLevel(logging.WARNING)


def main() -> None:
    """
    Entry point for executing the homing.

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

        # Configure homing parameters (temporary — not stored on the device).
        # Arguments:
        #   direction_positive (bool): True = positive direction, False = negative.
        #   offset (int): Optional homing offset in counts (not persistent).
        #
        # Example (with custom offset):
        #   homing(node, direction_positive=True, offset=2000)
        #
        # Without arguments, uses existing device settings:
        homing(node)
        
        network.disconnect()

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
