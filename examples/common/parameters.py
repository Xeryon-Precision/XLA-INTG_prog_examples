"""
parameters.py

© 2025 Xeryon – All rights reserved.
For demonstration purposes only. See README for disclaimer.
"""

from enum import IntEnum, IntFlag, unique, StrEnum, Enum

from canopen.profiles.p402 import OperationMode


# -----------------------------------------------------------------------------
# Encoder resolution
# -----------------------------------------------------------------------------
@unique
class EncoderRes(Enum):
    # Effective increments per millimetre (inc/mm)
    ENC_RES_10MU    = (1_000_000.0 / 9407.4)  # XLA-5-X-1MU-INTG      (10  µm resolution)
    ENC_RES_1MU     = (1_000_000.0 / 1007.9)  # XLA-5-X-1MU-INTG      (1   µm resolution)
    ENC_RES_250NAN  = (1_000_000.0 / 249.8)   # XLA-5-X-1MU-INTG      (250 nm resolution)
    ENC_RES_100NAN  = (1_000_000.0 / 100.8)   # XLA-5-X-100NAN-INTG   (100 nm resolution)


# -----------------------------------------------------------------------------
# CAN bitrates
# -----------------------------------------------------------------------------
class CANBitrate(IntEnum):
    BITRATE_10K = 10_000
    BITRATE_20K = 20_000
    BITRATE_50K = 50_000
    BITRATE_125K = 125_000     # Default
    BITRATE_250K = 250_000
    BITRATE_500K = 500_000
    BITRATE_800K = 800_000
    BITRATE_1000K = 1_000_000


SUPPORTED_BITRATES = list(CANBitrate)

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
    PROFILE_POSITION = OperationMode.PROFILED_POSITION
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
RESTORE_ALL_DEFAULT_PARAMETERS = 0x64616F6C # "load"
SAVE_ALL_PARAMETERS = 0x65766173            # "save"
DEFAULT_STATUS_LOGGING = 3 + 8

# -----------------------------------------------------------------------------
# LSS Configuration
# -----------------------------------------------------------------------------
LSS_RESET_DELAY = 1.0             # Delay after network reset (seconds)
LSS_SCAN_DELAY = 0.1              # Delay between scan attempts (seconds)
LSS_UNCONFIGURED_NODE_ID = 0xFF   # LSS unconfigured node ID value
