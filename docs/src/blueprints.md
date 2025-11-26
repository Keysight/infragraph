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
from infragraph.blueprints.devices.nvidia.dgx import Dgx
from infragraph.blueprints.fabrics.single_tier_fabric import SingleTierFabric

Instantiate a DGX device
dgx = Dgx()

# Create a single-tier fabric connecting two DGX devices via a single switch
fabric = SingleTierFabric(dgx, 2) # 2 DGX devices
# 'fabric' now contains the infrastructure graph with two DGX devices and the connecting switch
```


The `SingleTierFabric` blueprint returns an Infragraph object that includes two DGX devices along with a generic switch defined in the device blueprints, connected to form a simple topology.

---

### Example: Creating a CLOS Fat Tree Fabric with DGX Hosts

The following example demonstrates how to use the `ClosFatTreeFabric` class to create a clos fat tree fabric connecting dgx devices via a generic switch:


```python
from infragraph.blueprints.fabrics.clos_fat_tree_fabric import ClosFatTreeFabric
from infragraph.blueprints.devices.dgx import Dgx
from infragraph.blueprints.devices.generic_switch import Switch

# Instantiate a DGX device
dgx = Dgx()

# Instantiate a Switch
switch = Switch(port_count=16)

# Create a clos fat tree fabric with switch radix as 16 and with two levels:
clos_fat_tree = ClosFatTreeFabric(switch, dgx, 2, [])
# 'fabric' now contains the infrastructure graph with two tier clos fat tree fabric
```

### CLOS Fat Tree Fabric Overview

The CLOS Fat Tree fabric builds a scalable network using multiple levels of identical switches connected in a tree pattern. It is defined by FT(k, L), where:
- **k** = number of ports per switch (switch radix)  
- **L** = number of levels in the fabric (depth)

### Inputs

- **Switch device:** Defines the switch type and port count (k).  
- **Host device:** Defines the servers or hosts (e.g., DGX) connected to the fabric edge.  
- **Levels (L):** Number of switch layers (tiers) in the network.  
- **Bandwidth array:** Link speeds at each level, e.g., host-to-edge (tier_0), edge-to-aggregation (tier_0 -> tier_1), aggregation-to-spine (tier_1 -> tier_2).


### Case L = 2 (Two-level Fat Tree)
1. **switch downlink**: k/2 
2. **Number of Hosts:** 
    = (2 * (switch_downlink) ^ Levels)/ (total ports in host)
3. **tier_0 (rack switches):** Number of switches facing hosts.  
   = (2 * (switch_downlink) ^ Levels - 1)
4. **tier_1 (spine switches):** Uplink switches connecting tier_0 switches.  
   = ((switch_downlink) ^ Levels - 1)


**Connections:** Hosts → tier_0 (rack) → tier_1 (spines).

### Case L = 3 (Three-level Fat Tree)
1. **switch downlink**: k/2 
2. **Number of Hosts:** 
    = (2 * (switch_downlink) ^ Levels)/ (total ports in host)
1. **Tier_0 (rack switches):**  
   = (2 * (switch_downlink) ^ Levels - 1)
2. **Tier_1 (aggregation switches):** Same number as tier_0:  
   = (2 * (switch_downlink) ^ Levels - 1)
3. **Pods:** Derived by dividing tier_0 by the downlinks per switch (k/2), matching pod size:  
   = switch downlink = k/2
4. **Spines (core switches):** Number of spines is:  
   = ((switch_downlink) ^ Levels - 1)
5. **Spine Sets:** Spine switches grouped to connect to tier_0 switches in pods.  
   = ((switch_downlink/2) * (tier_0 to tier_1 bandwidth)/(tier_1 to tier_2 bandwidth))

**Example FT(32, 2):**  
- Switch Radix = 32
- Levels = 2
- Host per switch = 2
- Total Hosts = 64 
- tier_0 switches = 32
- tier_1 switches = 16
- Pods = 2
- Spine sets = 16

**Connections:** Hosts → tier_0 → tier_1 (spine switches).

---
