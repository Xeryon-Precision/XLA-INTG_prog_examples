# Frequently Asked Questions (FAQ)

This page provides answers to common questions related to using Xeryon CiA 402-compliant devices with CANopen.

## Configuration

<details>
<summary><strong>What is the Node ID?</strong></summary>

Each CANopen device on the network has a unique identifier called the *Node ID*. The default Node ID for Xeryon devices is **32**.
You can change this value in `settings.py` or by using the daisy-chaining configuration script.

</details>

<details>
<summary><strong>How do I set the homing offset?</strong></summary>

There are two ways to set the homing offset:

1. **Temporary (for testing):**
   Use the Python function:

   ```python
   homing(node, offset=value)
   ```

   This applies the offset until the next reboot.

2. **Persistent (recommended):**
   Use `configure_homing_parameters()` in `configuration.py`.
   Run `configuration.py` after setting it to store the offset in persistent memory.

**Tip:** First experiment with the `homing()` function to find the correct offset, then set it permanently with `configure_homing_parameters()`.
Once set, moving to position `0` will move to the home position with the offset applied.

</details>

## LEDs & Power

<details>
<summary><strong>The device is powered ON but no LEDs are visible.</strong></summary>

The LEDs are only active in certain modes. Please use the example scripts to verify operation.

</details>

<details>
<summary><strong>Is it possible to disable the LEDs?</strong></summary>

You can configure which LEDs are enabled and disabled using `configuration.py`.

</details>

<details>
<summary><strong>The orange motor LED is on but the motor does not move.</strong></summary>

Check if STO has a high signal (2 V–24 V).

</details>

## Troubleshooting

<details>
<summary><strong>I cannot communicate with the controller.</strong></summary>

Work through these checks in order:

* Check the wiring
* Check the selected COM port
* Try communication using `verify_communication.py`
* Power check

  * Measure the supply voltage at the controller terminals.
  * Check current draw. If it is **0 mA**, the supply may be off or incorrectly wired. If it is **non‑zero**, continue.

</details>

<details>
<summary><strong>My CAN interface is not detected on Linux. What should I do?</strong></summary>

When using Linux please ensure that kernel CAN drivers are loaded and that your device appears under `/dev/`.

</details>

<details>
<summary><strong>I receive timeout errors when running an example.</strong></summary>

Check that:

* The CAN adapter is correctly installed and configured.
* `settings.py` contains the correct `CAN_INTERFACE` and `CAN_CHANNEL`.
* The Node ID matches the device configuration.

</details>

<details>
<summary><strong>I receive timeout errors when positioning.</strong></summary>

Depending on the configuration, speed, and application it is possible that the default timeout settings are insufficient.
You can change these settings in `settings.py`.

</details>

## Daisy-Chaining

<details>
<summary><strong>How many devices can be daisy-chained?</strong></summary>

There are two ways of daisy chaining, it is recommended to set the CAN baudrate to 1 Mbps when daisy-chaining multiple devices.

* Up to 4, if connected on a single breakout PCB (FFC cable).
* It is also possible to daisy chain the breakout boards instead to create a larger network.

</details>

## Additional Support

If your question is not answered here, please:

* Review the guides in the `docs` folder.
* Check the [README.md](README.md) for setup and installation details.
* If you need further assistance please contact our support team: [support@xeryon.com](mailto:support@xeryon.com)
