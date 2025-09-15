# Xeryon CANopen Example

This repository provides examples for working with CiA 402-compliant devices from Xeryon over CANopen. The repository includes installation instructions, communication setup, and Python programming examples for motion control.

## Table of Contents

* [Wiring](#wiring)
* [Installation](#installation)
* [Quick Start](#quick-start)
* [Documentation](#documentation)
* [Project Structure](#project-structure)
* [FAQ](#faq)

## Wiring

> ⚠️ **Safety Warning:**
> Always disconnect power before wiring. Incorrect wiring while powered can damage the device.

Before proceeding, please refer to the wiring diagram for the correct setup. The wiring involves connecting the breakout board, STO, and power supply to the motor and CAN adapter.

We use the **Fysetc UCAN** USB-to-CAN adapter. However, you are free to use any compatible USB-to-CAN device. 

### Wiring Steps

1. **Power Off** - Ensure the breakout PCB is not powered, and the power plug is disconnected.
2. **Connect FFC to XLA** - Attach the FFC cable to the XLA. ([Wiring example](docs/wiring.md))
3. **Connect FFC to Breakout Board** - Attach the other end of the FFC cable to the breakout board.
4. **Connect STO** - Connect the STO (Safe Torque Off) pin to the **3.3 V** pin on the breakout board.
5. **Connect CAN Bus** - Connect the **CAN_H**, **CAN_L**, and **GND** terminals of the USB-to-CAN adapter to the corresponding pins on the breakout PCB.
6. **Connect USB** - Plug the USB-C cable between the USB-to-CAN adapter and your PC.
7. **Connect Power Cables** - Attach the power cables to the screw terminals.
8. **Verify Connections** - Double-check that all connections are secure and correctly placed.
9. **Power On** - Connect the power plug and switch on the power supply.

> **Note:** No LEDs will be on when the device is powered

<img src="img/XLA-INTG-CTRL_wiring_diagram.jpg" alt="Wiring Diagram" style="border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.2);" />

## Installation

### 1. Python

Make sure Python 3.12 or higher is installed before continuing.

### 2. Install dependencies

You can install the required dependencies by running the following command.

```bash
pip install -r requirements.txt
```

### 3. Open the examples directory

Make sure you are in the `examples` directory before running the following commands:

```bash
cd examples
```

### 4. Interface Compatibility

Ensure your hardware (e.g., USB-to-CAN adapter) is connected and supported by your system:

* For Linux `socketcan`: ensure kernel CAN drivers are loaded

### 5. Change `settings.py`

To configure the CAN interface and channel for your platform, open `settings.py` and update the following values:

```python
# Encoder resolution
ENC_RES = EncoderRes.ENC_RES_1MU

# Default Node ID is 32
NODE_ID = 32

# Interface (str): Interface type (e.g., "slcan", "socketcan").
CAN_INTERFACE = "slcan"

# Channel (str): CAN channel (e.g., "COM3", "/dev/ttyACM0", "can0").
CAN_CHANNEL = "COM3"

# Default bitrate is 125kbps
CAN_BITRATE = CANBitrate.K125

# Filename of the EDS file
EDS_PATH = "../eds/xeryon_xla_5_eds.eds"
```

## Quick Start

To quickly verify your setup, run the configuration example:

```bash
python configuration.py
```

This will configure all the configuration settings to the default values. 
An error will occur when there is a communication issue.
(Ensure you have updated `settings.py` with your CAN interface details first.)

You can also run other examples:

```bash
python <filename>.py
```

## Documentation

These are detailed guides on how to configure, home, and perform motion with the motor:

| Guide Type                                             | Description                             |
| ------------------------------------------------------ | --------------------------------------- |
| [Configuration](docs/configuration.md)                 | How to set parameters and save them     |
| [Homing](docs/homing.md)                               | How to execute a homing operation       |
| [Profile Position mode](docs/mode_profile_position.md) | How to use profile position mode        |
| [Daisy Chaining](docs/daisy_chaining.md)               | How to use daisy chaining               |
| [Wiring example](docs/wiring.md)                       | Wiring example                          |
| [CANopen documentation](https://xeryon.com/wp-content/uploads/2025/08/CANopen-Introduction.pdf)                         | CANopen introduction manual      |
| [EDS](docs/eds.md)                                     | EDS file information                    |
| [FAQ](FAQ.md)                                          | Frequently asked questions              |

## Project Structure

```
.
├── docs/
│   ├── configuration.md              # Guide for configuration                             
│   ├── daisy_chaining.md             # Guide for daisy chaining
│   ├── eds.md                        # Information about EDS
│   ├── homing.md                     # Guide for homing
│   ├── mode_profile_position.md      # Guide for mode profile position
│   └── wiring.md                     # Wiring example
│   
├── eds/
│   ├── xeryon_xla_5_eds.eds          # EDS file
│   └── xeryon_xla_5_eds_docu.txt     # Documentation of EDS fields
│   
├── examples/                         # Code Examples
│   ├── daisy_chaining_configuration
│   │   ├── change_node_id_all.py     # Example to automatically reassign all Node IDs
│   │   └── change_node_id_single.py  # Example to change Node ID of specific node
│   │
│   ├── configuration.py              # Example script for configuration
│   ├── homing.py                     # Example script for homing
│   └── mode_profile_position.py      # Example script for mode profile position
│
├── FAQ.md                            # Frequently asked questions
├── README.md                         # General Guide for running the examples
└── requirements.txt                  # Dependency file for python setup
```

## FAQ

Please refer to [FAQ](FAQ.md) for a complete list of common questions and answers.


