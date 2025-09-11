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

from common.utils import setup_network, homing, configure_node

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
    try:
        network, absolute_path = setup_network()
        network.check()

        node = BaseNode402(32, absolute_path)
        network.add_node(node)

        configure_node(node)

        time.sleep(1)

        homing(node)
        
        network.disconnect()

    except KeyboardInterrupt:
        log.info("Keyboard interrupt detected, stopping program..")
        pass

    except Exception as e:
        log.error(f"Error occured: {e}")


if __name__ == "__main__":
    main()
    sys.exit(0)
