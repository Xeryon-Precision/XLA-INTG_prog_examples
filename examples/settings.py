"""
settings.py

Configuration definitions for Xeryon CANopen CiA-402 example scripts.

Includes interface settings, default parameters, bitrates, control modes, and
protocol constants for use across all example implementations.

© 2025 Xeryon – All rights reserved.
For demonstration purposes only. See README for disclaimer.
"""

from common.parameters import EncoderRes, CANBitrate

# -----------------------------------------------------------------------------
# Configuration
#
# TODO: Select the correct resoltion
#  ENC_RES = EncoderRes.ENC_RES_1MU
#
# TODO: Please set the following CAN configuration values
#  Windows example:
#     CAN_INTERFACE = "slcan"
#     CAN_CHANNEL = "COM3"
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#  Linux example:
#     SLCAN
#         CAN_INTERFACE = "slcan"
#         CAN_CHANNEL = "/dev/ttyACM0"
#     Socketcan
#         CAN_INTERFACE = "socketcan"
#         CAN_CHANNEL = "can0"
#
# -----------------------------------------------------------------------------
# Encoder resolution
#  - EncoderRes.ENC_RES_10MU
#  - EncoderRes.ENC_RES_1MU
#  - EncoderRes.ENC_RES_250NAN
#  - EncoderRes.ENC_RES_100NAN
ENC_RES = EncoderRes.ENC_RES_1MU

# Default Node ID is 32
NODE_ID = 32

# Interface (str): Interface type (e.g., "slcan", "socketcan").
CAN_INTERFACE = "slcan"

# Channel (str): CAN channel (e.g., "COM3", "/dev/ttyACM0", "can0").
CAN_CHANNEL = "COM3"

# Default bitrate is 125kbps
CAN_BITRATE = CANBitrate.BITRATE_125K

# Filename of the EDS file
EDS_PATH = "../eds/xeryon_xla_5_eds.eds"

# -----------------------------------------------------------------------------
# Default timeouts
# -----------------------------------------------------------------------------
DEFAULT_SDO_TIMEOUT = 5.0      # seconds
DEFAULT_BOOTUP_TIMEOUT = 3.0   # seconds
DEFAULT_TIMEOUT = 15.0         # seconds

# -----------------------------------------------------------------------------
# Conversion factors
# -----------------------------------------------------------------------------
INC_PER_MM = float(ENC_RES.value)
MM_PER_INC = 1.0 / float(INC_PER_MM)
