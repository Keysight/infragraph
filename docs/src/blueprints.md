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
src/infragraph/blueprints/devices/<vendor>
```

Each Infragraph device can expose **multiple variants**, allowing the same blueprint to represent different SKUs or generations of hardware. For example, a ``QSFP`` device supports the following variants:
- `qsfp_plus_40g`
- `qsfp28_100g`
- `qsfp56_200g`
- `qsfp_dd_400g`
- `qsfp_dd_800g`

Infragraph devices support variant selection at initialization time, enabling end users to choose the exact hardware variant they want to model when creating a device object.

The example below shows **QSFP** class definition and initialization using a specific variant, demonstrating how variants are applied in practice.

---

### Creating a QSFP Transceiver Blueprint

The `QSFP` class defines a **device blueprint** for QSFP-family pluggable transceivers in InfraGraph.  
It inherits from the base `Device` class and models the **internal structure, ports, and signal binding** of a QSFP module in a consistent and reusable way.

All QSFP variants share the same internal topology:

- One **electrical host-facing interface**
- One **optical media-facing interface**
- A fixed **one-to-one electrical ↔ optical binding**

Only the **capabilities** (form factor, speed, and lane count) differ across variants, and these are strictly controlled using a variant catalog.


#### Example: `qsfp.py` Blueprint located in /src/infragraph/blueprints/devices/common

<details open>
<summary><strong>QSFP device definition using OpenApiArt generated classes</strong></summary>
```python
{% include-markdown "../../src/infragraph/blueprints/devices/common/transceiver/qsfp.py" %}
```
</details>

## Composability

Infragraph supports modeling a **device inside another device**, where the nested device behaves as a **component** of the parent device using `Component.Device`.

The idea is that we can add a **CX5** device to a **DGX**, and then add a **QSFP** to the **CX5**:

```python
qsfp = QSFP("qsfp28_100g")
cx5 = Cx5(variant="cx5_100g_single", transceiver=qsfp)
dgx = NvidiaDGX("dgx_h100", cx5)
infrastructure = Api().infrastructure()
# we need to append added devices
infrastructure.devices.append(dgx).append(cx5).append(qsfp)
infrastructure.instances.add(name=dgx.name, device=dgx.name, count=1)
service = InfraGraphService()
service.set_graph(infrastructure)
g = service.get_networkx_graph()
```

This creates a single **DGX h100** variant composed of a **CX5 100g single port** which is composed of a **QSFP 28 100g**. Generated YAML:

<details closed>
<summary><strong>DGX-CX5-QSFP composed device definition as yaml</strong></summary>
```yaml
{% include-markdown "./yaml/dgx_cx5_qsfp_composed.yaml" %}
```
</details>


In some scenarios, a user may prefer to model ``CX5`` as an **abstracted NIC** within a ``DGX`` device rather than as a fully instantiated device.

To add ``CX5`` as a `NIC` component, the user can initialize the ``DGX`` device by passing the CX5 variant directly, as shown below:


```python
dgx_profile = "dgx_h100"
cx5_variant = "cx5_100g_single"
device = NvidiaDGX(dgx_profile, cx5_variant)
infrastructure = Api().infrastructure()
infrastructure.devices.append(device)
infrastructure.instances.add(name=device.name, device=device.name, count=1)
service = InfraGraphService()
service.set_graph(infrastructure)
g = service.get_networkx_graph()
```

This creates a `CX5` as a nic component in `DGX` device. Generated YAML:

<details closed>
<summary><strong>DGX with CX5 NIC definition as yaml</strong></summary>
```yaml
{% include-markdown "./yaml/dgx_cx5_nic.yaml" %}
```
</details>

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
from infragraph.blueprints.devices.nvidia.dgx import NvidiaDGX
from infragraph.blueprints.fabrics.single_tier_fabric import SingleTierFabric

Instantiate a DGX device
dgx = NvidiaDGX()

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
from infragraph.blueprints.devices.dgx import NvidiaDGX
from infragraph.blueprints.devices.generic.generic_switch import Switch

# Instantiate a DGX device
dgx = NvidiaDGX()

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


### Use Case L = 2 (Two-level Fat Tree)
1. **switch downlink**: k/2 
2. **Number of Hosts:** 
    = (2 * (switch_downlink) ^ Levels)/ (total ports in host)
3. **tier_0 (rack switches):** Number of switches facing hosts.  
   = (2 * (switch_downlink) ^ Levels - 1)
4. **tier_1 (spine switches):** Uplink switches connecting tier_0 switches.  
   = ((switch_downlink) ^ Levels - 1)


**Connections:** Hosts → tier_0 (rack) → tier_1 (spines).

### Use Case L = 3 (Three-level Fat Tree)
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

**Please note that fabric builders only work with non-composed devices.**

---