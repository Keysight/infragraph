# Model

## Formal Model - Infrastructure As A Graph
The formal [model specification](https://github.com/Keysight/infrastructure/blob/readme-refactor/keysight_chakra/infra/infra.proto) can be found on GitHub under [Infrastructure](https://github.com/Keysight/infrastructure) organization. The model has been defined as a protobuf message because Protocol Buffers provide a highly efficient, compact, and language-neutral way to serialize structured data. This binary serialization format results in significantly smaller message sizes compared to text-based formats like JSON or YAML, which reduces network bandwidth usage and storage requirements

## Building Blocks

The infra.proto provides multiple building blocks to define the infrastructure. These blocks include:

* Inventory
* Device
* Components
* Links
* Device Instances
* Connections

### Devices

```proto
message Device {
  optional string name = 1;
  map<string, Component> components = 3;
  map<string, Link> links = 4;
  repeated string connections = 5;
}
```

The Device message defines a device which is a part of the infrastructure. This contains a collection of components, links between the components and the connections. The main fields are:
* name: An optional field allowing users to define the name of the device
* components: A dictionary which stores the component message with the key as the component name. This message is defined in the later section
* links: Another dictionary which stores the link message with the link name. 
* connections: A list of connections that describe how components are connected to each other in a single device. Each element of this list is a string that describe the component connection and is described as:
    ```
    source_component_name "." source_component_index "." link_name "." destination_component_name "." destination_component_index 
    ```
    example:
    ```
    nic.0.pcie.cpu.0
    npu.0.pcie.nvswitch.0
    asic.0.mii.nic.0
    ```
    The **source_component_name** and **destination_component_name** is the name field present in the component message. This name also corresponds to the **key** of the **components** dictionary field which is a part of the device message. Each component message holds a **count** field which defines the number of components present in the device. These fields are defined later in the components section.

### Components
```proto
message Component {
  optional string name = 1;
  optional uint32 count = 2;
  oneof type {
    CustomComponent custom = 10;
    Cpu cpu = 11;
    Npu npu = 12;
    Nic nic = 13;
    Switch switch = 14;
  }
}
```

The component message defines three major fields:
* name: An optional field which gives the name of the component. The name is also provided as a **key** in the **components** dictionary field type of device message.
* count: The count defines the total components present. Lets assume we have a *nic* component with a count of 8. This would create 8 instances of the nic component whose properies would remain the same with a zero based indexing. This is analogous to the concept of classes and objects where the component message acts as the blueprint and count indicates the number of objects created. 
* type: The component datamodel allows to describe component of a certain type. The type can be:
    * CPU
    * NPU
    * NIC
    * Switch
    * Custom

    Each of these types are defined as another message. The section below describes the message format of component type.

#### CPU Component

```proto
message Cpu {
  MemoryType memory = 1;
}
```
This message defines the CPU type component. This allows the user to assign a certain memory type to the CPU. The MemoryType is covered in the later section.


#### NPU Component
```proto
message Npu {
  MemoryType memory = 1;
}
```

This message defines the NPU type component. This allows the user to assign a certain memory type to the NPU. The MemoryType is covered in the later section.

#### Custom Component

```proto
message CustomComponent {
  MemoryType memory = 1;
}
```

This message defines the CustomComponent type component. This allows the user to assign a certain memory type to the Custom Component. The MemoryType is covered in the later section.

##### Memory Type

```proto
enum MemoryType {
  MEM_UNSPECIFIED = 0;

  // random access memory
  MEM_RAM = 1;

  // high bandwidth memory interface for 3D stacked sync dynamic random-access memory
  MEM_HBM = 2;

  // memory that uses compute express link interconnect to the cpu
  MEM_CXL = 3;
}
```
The user can set either of the memory type to the CPU, NPU or CustomComponent Type. The memory could be either:
* Unspecified
* Random Access Memory
* High Bandwidth Memory Interface
* Compute Express Link

The enum can be extended to add more memory types which can be used by custom component

#### NIC Component

```proto
message Nic {
  oneof type {
    Ethernet ethernet = 10;
    Infiniband infinband = 11;
  }
}

message Infiniband {
}

message Ethernet {
}
```

This describes the NIC Component. Each nic component can be of the following type:
* Ethernet
* Infiniband
These types are defined as a message. 

#### Switch Component

```proto
message Switch {
  oneof type {
    Pcie pcie = 1;
    NvLink nvswitch = 2;
    Custom custom = 3;
  }
}

message Pcie {
}

message NvLink {
}

message Custom {
}
```

This section defines the Switch Component type. The switch component can be either of the following:
* pcie
* nvlink
* custom

These types are defined as a message. 

### Link

```proto
message Link {
  optional string name = 1;
  optional string description = 2;
  Bandwidth bandwidth = 10;
}

message Bandwidth {
  oneof type {
    uint32 gbps = 1;
    uint32 gBs = 2;
    uint32 gts = 3;
  }
}
```

The Link message allows to define a "link" between the device as well as components. This model has three fields:
* name
* description
* bandwidth

The Bandwidth is defined as a message and allows to define the link bandwidth as:
* gbps: gigabits per second
* gBs: gigabytes per second
* gts: giga transfers per second

These take an unsigned integer value. The Links use the Bandwidth message model to define the link speed. 

### Inventory

```proto
message Inventory {
  map<string, Device> devices = 1;
  map<string, Link> links = 2;
}
```

Inventory is a collection of all unique types of Devices and Links in the infrastructure. This has two major fields:
* devices: 
    
    A collection of all unique types of devices in the infrastructure. The uniqueness is determined by the Device.name field.

* links:

    A collection of all unique types of links in the infrastructure. These links can be reused multiple times when creating connections between devices. The key is the Link.name which is used to guard against duplicates.

### Device Instances

```proto
message DeviceInstances {
  optional string name = 1;
  optional string device = 2;
  optional uint32 count = 3;
}
```

The Device Instances message is used to instantiate the Device in the infrastructure. This message contains three fields:
* name: the name of the device instance. This is used to categorize the device. For example: a switch defined in the **inventory - devices** message can be used as a Rack Switch, POD Switch or a Spine Switch. The name allows to create/provide a unique name to a set of devices. 
* device: The name of the actual device that exist in the **inventory - devices**  field. This links the device which we want to use.
* count: The number of instances of device in the infrastructure under this name. This should always be >= 1. This also indiates the number of instances we need for a specific device under a certain name. This is again analogous to component modelling but done on a device level. The indexing starts at 0 and provides a unique identifier to create a device instance.

### Infrastructure

```proto
message Infrastructure {
  Inventory inventory = 1;
  map<string, DeviceInstances> device_instances = 2;
  repeated string connections = 3;
}
```

The Infrastructure message establishes an inventory of devices and links, instances of the inventory, connectivity between those instances and any custom user information about devices, components, links and instances.

This holds the inventory which contains the devices, links; the device_instances map that hold all the devices instantiated and a list of connections. The connection format is defined as a string of the following elements separated by a "."

```
source_device_instance_name
source_device_index 
source_device_component_name
source_device_component_index
link_name
destination_device_instance_name
destination_device_index
destination_device_component_name
destination_device_component_index
```

This utilizes the device instances naming convention with the count which internally links to the 
*device* message that defines the component, its name and the count and connects two different device instances with the *link name* that is defined in the *inventory*. 

## Building Infrastructure

The model allows us to define devices, its internal components, as nodes and links as edges and creates connection as a link between the nodes thereby allowing to create a graph based representation. A step by step guide to create infrastructure is defined in [Building A Cluster](create.md).