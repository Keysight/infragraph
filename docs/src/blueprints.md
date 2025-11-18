# Infragraph Blueprints

Infragraph provides users with multiple **blueprints** that help define the foundational components of an infrastructure. These blueprints cover both **devices** and **fabrics**, enabling flexible and extensible modeling of network and compute infrastructure.

Each blueprint is implemented as Python source code, allowing users to create classes and objects that inherit from the generated SDK. This approach makes it possible to define more realistic and customizable representations of devices and fabrics while maintaining compatibility with Infragraph’s schema and data models.

All available blueprints can be found in the following directory:

```
src/infragraph/blueprints
```

---

## Device Blueprints

Device blueprints enable you to instantiate specific device types using the Infragraph schema format. Each blueprint encapsulates attributes, component definitions, and configuration logic that represent actual hardware or node types within a network topology.

All device blueprints are organized under:
```
src/infragraph/blueprints/devices/
```


---

### Creating a Custom DGX Device Blueprint

The `Dgx` class defines a device blueprint for the Nvidia DGX system. It inherits from the base `Device` class and specifies internal components, their descriptions, quantities, and interconnections in detail.

#### Example: `dgx.py` Blueprint


```python
from typing import Optional
from infragraph import *

class Dgx(Device):
def init(self, nic_device: Optional[Device] = None):
"""Adds an InfraGraph device representing a DGX system.
    Components include:
    - 2 CPUs
    - 8 NPUs (Nvidia A100 GPUs)
    - 4 PCIe switches
    - 8 NICs (Network Interface Cards)
    - 1 NVLink switch
    """
    super(Device, self).__init__()
    self.name = "dgx"
    self.description = "Nvidia DGX System"

    # CPU component
    cpu = self.components.add(
        name="cpu",
        description="AMD Epyc 7742 CPU",
        count=2,
    )
    cpu.choice = Component.CPU

    # NPU component
    npu = self.components.add(
        name="npu",
        description="Nvidia A100 GPU",
        count=8,
    )
    npu.choice = Component.NPU

    # NVLink switch
    nvlsw = self.components.add(
        name="nvlsw",
        description="NVLink Switch",
        count=1,
    )
    nvlsw.choice = Component.CUSTOM

    # PCIe switch
    pciesw = self.components.add(
        name="pciesw",
        description="PCI Express Switch Gen 4",
        count=4,
    )
    pciesw.choice = Component.CUSTOM

    # NICs - either generic or custom device passed as argument
    if nic_device is None:
        nic = self.components.add(
            name="nic",
            description="Generic Nic",
            count=8,
        )
        nic.choice = Component.NIC
    else:
        nic = self.components.add(
            name=nic_device.name,
            description=nic_device.description,
            count=8,
        )
        nic.choice = Component.DEVICE

    # Fabric and link definitions
    cpu_fabric = self.links.add(name="fabric", description="AMD Infinity Fabric")
    pcie = self.links.add(name="pcie")
    nvlink = self.links.add(name="nvlink")

    # CPU to CPU connections via AMD Infinity Fabric
    edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=cpu_fabric.name)
    edge.ep1.component = "cpu"
    edge.ep2.component = "cpu"

    # NPUs connected to NVLink switch
    edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=nvlink.name)
    edge.ep1.component = "npu"
    edge.ep2.component = "nvlsw"

    # Connecting NPUs to PCIe switches (grouped pairs)
    for npu_idx, pciesw_idx in zip(["0:2", "2:4", "4:6", "6:8"], range(pciesw.count)):
        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie.name)
        edge.ep1.component = f"npu[{npu_idx}]"
        edge.ep2.component = f"pciesw[{pciesw_idx}]"

    # Connecting NICs to PCIe switches (grouped pairs)
    for nic_idx, pciesw_idx in zip(["0:2", "2:4", "4:6", "6:8"], range(pciesw.count)):
        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie.name)
        edge.ep1.component = f"nic[{nic_idx}]"
        edge.ep2.component = f"pciesw[{pciesw_idx}]"

if name == "main":
    device = Dgx()
    print(device.serialize(encoding=Device.YAML))
```

---

## Fabric Blueprints

Fabric blueprints allow users to define network fabric topologies by combining multiple devices and specifying their interconnections. They provide an intuitive way to model complex infrastructure setups such as datacenter tiers, clusters, or multi-device fabrics.

All fabric blueprints are located in:
```
src/infragraph/blueprints/fabrics/
```


### Example: Creating a Single Tier Fabric with Multiple DGX Hosts

The following example demonstrates how to use the `SingleTierFabric` class to create a simple fabric connecting two DGX devices via a generic switch:


```python
from infragraph.blueprints.devices.dgx import Dgx
from infragraph.blueprints.fabrics.single_tier_fabric import SingleTierFabric

Instantiate a DGX device
dgx = Dgx()

# Create a single-tier fabric connecting two DGX devices via a single switch
fabric = SingleTierFabric(dgx, 2) # 2 DGX devices
# 'fabric' now contains the infrastructure graph with two DGX devices and the connecting switch
```


The `SingleTierFabric` blueprint returns an Infragraph object that includes two DGX devices along with a generic switch defined in the device blueprints, connected to form a simple topology.

---


