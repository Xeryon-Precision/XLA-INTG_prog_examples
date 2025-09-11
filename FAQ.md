# Frequently Asked Questions (FAQ)

This page provides answers to common questions related to using Xeryon CiA 402-compliant devices with CANopen.

## LEDs & Power

**Q: The device is powered ON but no LEDs are visible**

A: The LEDs are only active in certain modes. Please use the example scripts to verify operation.

**Q: Is it possible to disable the LEDs?**

A: You can configure which LEDs are enabled and disabled using configruation.py.

**Q: The orange motor LED is on but the motor does not move**

A: Check if STO has a high signal (2 V–24 V).

## Daisy-Chaining

**Q: How many devices can be daisy-chained?**

A: There are two ways of daisy chaining, it is recommended to set the CAN baudrate to 1 Mbps when daisy-chaining multiple devices.
- Up to 4, if connected on a single breakout PCB (FFC cable).
- It is also possible to daisy chain the breakout boards instead to create a larger network.

## Configuration

**Q: What is the Node ID?**

A: Each CANopen device on the network has a unique identifier called the *Node ID*. The default Node ID for Xeryon devices is **32**. You can change this value in `settings.py` or by using the daisy-chaining configuration script.

## Troubleshooting

**Q: My CAN interface is not detected on Linux. What should I do?**

A: When using Linux please ensure that kernel CAN drivers are loaded and that your device appears under `/dev/`.

**Q: I receive timeout errors when running an example.**

A: Check that:

* The CAN adapter is correctly installed and configured.
* `settings.py` contains the correct `CAN_INTERFACE` and `CAN_CHANNEL`.
* The Node ID matches the device configuration.

**Q: I receive timeout errors when positioning.**

A: Depending on the configuration, speed, and application it is possible that the default timeout settings are insufficient. You can change these settings in `settings.py`

**Q: I cannot communicate with the controller**

A: Work through these checks in order.

* Power check

   * Measure the supply voltage at the controller terminals.
   * Check current draw. If it is **0 mA**, the supply may be off or incorrectly wired. If it is **non‑zero**, continue.

* Check the wiring

* Check the selected COM port

* Try communication using test_communication.py


## Additional Support

If your question is not answered here, please:

* Review the guides in the `docs` folder.
* Check the [README.md](README.md) for setup and installation details.
* Contact Xeryon support for further assistance.
