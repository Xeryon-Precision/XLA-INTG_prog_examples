## EDS File and eds\_docu.txt

### What is an EDS?

An EDS (Electronic Data Sheet) is a standardized INI-style file that describes the object dictionary of a CANopen device. It is required for correct SDO access and symbolic mapping of object names.

### What is `eds_docu.txt`?

This is a human-readable reference exported from the EDS for easier debugging and script development. It includes:

* Object indexes
* Subindex descriptions
* Access types and data types

### Why is it useful?

* EDS files can be imported into CANopen master tools for symbolic access.
* They help configure network parameters (PDO mapping, heartbeat, etc.).
* They serve as documentation for firmware updates and version compatibility.

### Where do I configure it?

The path to your `.eds` file is set in `settings.py` as `EDS_PATH`:

```python
EDS_PATH = "../eds/xeryon_xla_5_eds.eds"
```
