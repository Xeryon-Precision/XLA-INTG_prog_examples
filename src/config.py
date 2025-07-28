"""
config.py

Configuration definitions for Xeryon CANopen CiA-402 example scripts.

Includes interface settings, default parameters, bitrates, control modes, and
protocol constants for use across all example implementations.

© 2025 Xeryon – All rights reserved.
"""

from enum import IntEnum, IntFlag, unique, StrEnum

from canopen.profiles.p402 import OperationMode


# -----------------------------------------------------------------------------
# Encoder resolution
# -----------------------------------------------------------------------------
@unique
class EncoderRes(IntEnum):
    ENC_RES_10MU = 100      # XLA-5-X-1MU-INTG      (10 µm resolution)
    ENC_RES_1MU = 1000      # XLA-5-X-1MU-INTG      (1 µm resolution)
    ENC_RES_250NAN = 4000   # XLA-5-X-1MU-INTG      (250 nm resolution)
    ENC_RES_100NAN = 10000  # XLA-5-X-100NAN-INTG   (100 nm resolution)


# -----------------------------------------------------------------------------
# Configuration
#
# TODO: Please set the following configuration values
#  Windows example:
#     CAN_INTERFACE = "slcan"
#     CAN_CHANNEL = "COM3"
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#  Linux example:
#     CAN_INTERFACE = "slcan"
#     CAN_CHANNEL = "/dev/ttyACM0"
#
# -----------------------------------------------------------------------------
# Interface (str): Interface type (e.g., "slcan", "socketcan").
CAN_INTERFACE = "slcan"

# Channel (str): CAN channel (e.g., "COM3", "/dev/ttyACM0", "can0").
CAN_CHANNEL = "COM3"

# Filename of the EDS file
EDS_PATH = "../eds/xeryon_xla_5_eds.eds"

# Encoder resolution
ENC_RES = EncoderRes.ENC_RES_1MU

# Default Node ID is 32
NODE_ID = 32

# -----------------------------------------------------------------------------
# DEFAULT TIMEOUTS
# -----------------------------------------------------------------------------
DEFAULT_SDO_TIMEOUT = 10.0      # seconds
DEFAULT_BOOTUP_TIMEOUT = 15.0   # seconds
DEFAULT_TIMEOUT = 15.0          # seconds

# -----------------------------------------------------------------------------
# Conversion factors
# -----------------------------------------------------------------------------
INC_PER_MM = int(ENC_RES)
MM_PER_INC = 1.0 / INC_PER_MM


# -----------------------------------------------------------------------------
# CAN bitrates
# -----------------------------------------------------------------------------
@unique
class CANBitrate(IntEnum):
    K10 = 10_000
    K20 = 20_000
    K50 = 50_000
    K125 = 125_000
    K250 = 250_000
    K500 = 500_000
    K800 = 800_000
    M1 = 1_000_000


SUPPORTED_BITRATES = list(CANBitrate)
CAN_DEFAULT_BITRATE = CANBitrate.K125


# -----------------------------------------------------------------------------
# NMT States
# -----------------------------------------------------------------------------
@unique
class NMTState(StrEnum):
    OPERATIONAL = "OPERATIONAL"
    STOPPED = "STOPPED"
    SLEEP = "SLEEP"
    STANDBY = "STANDBY"
    PRE_OPERATIONAL = "PRE-OPERATIONAL"
    INITIALISING = "INITIALISING"
    RESET = "RESET"
    RESET_COMMUNICATION = "RESET COMMUNICATION"


# -----------------------------------------------------------------------------
# CiA 402 Profile Controlword States
# -----------------------------------------------------------------------------
@unique
class NodeState(StrEnum):
    SWITCH_ON_DISABLED = "SWITCH ON DISABLED"
    DISABLE_VOLTAGE = "DISABLE VOLTAGE"
    READY_TO_SWITCH_ON = "READY TO SWITCH ON"
    SWITCH_ON = "SWITCHED ON"
    OPERATION_ENABLED = "OPERATION ENABLED"
    QUICK_STOP = "QUICK STOP ACTIVE"


# -----------------------------------------------------------------------------
# Control mode identifiers
# -----------------------------------------------------------------------------
@unique
class NodeOperationMode(IntEnum):
    HOMING = OperationMode.HOMING
    TRAJECTORY = OperationMode.PROFILED_POSITION
    OFF = OperationMode.NO_MODE
    HYBRID = -1
    OPEN_LOOP = OperationMode.OPEN_LOOP_VECTOR_MODE
    VELOCITY = -3
    BUS = -5
    TEST_1 = -6


# -----------------------------------------------------------------------------
# Homing methods
# -----------------------------------------------------------------------------
@unique
class HomingMethod(IntEnum):
    NEG_INDEX = 33
    POS_INDEX = 34
    CURRENT_POSITION = 37


# -----------------------------------------------------------------------------
# LED bit-mask flags
# -----------------------------------------------------------------------------
class LEDMask(IntFlag):
    OFF = 0  # 0b000
    POWER = 1 << 0  # 0b001
    ERROR = 1 << 1  # 0b010
    MOTOR = 1 << 2  # 0b100
    ALL = POWER | ERROR | MOTOR


# -----------------------------------------------------------------------------
# Parameter settings
# -----------------------------------------------------------------------------
RESTORE_ALL_DEFAULT_PARAMETERS = 0x64616F6C
DEFAULT_STATUS_LOGGING = 3 + 8
SAVE_ALL_PARAMETERS = 0x65766173
