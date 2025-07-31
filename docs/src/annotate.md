
# Binding Logical Infrastructure with Custom Attributes

The primary purpose of infra.proto is to define and design a generic network fabric. This enables end users to specify the devices as nodes and links as edges. The data model also allows for the definition and design of devices by adding links and components within the device, modeling the device internals as a subgraph.
Another data model, annotate.proto, allows for the definition and binding of various parameters within the generic infrastructure. Users can bind:

- Vendor-specific data
- Additional qualities of the infrastructure
- Specific device performance attributes, such as:
  - Latency
  - Routing tables

This helps to add more context and content to infrastructure elements.

The main objective is to decouple various bindings from the infrastructure, separating the concerns of designing the logical infrastructure from the additional data needed for specific use-cases.

## Example: Annotating Device Instances to device type

Lets annotate devices to types in our previous example:

The proposal is to include a `Device Type` for our infrastructure devices, with the types being `physical_switch`, `physical_host`, `vm_host`, and `vm_switch`. This categorization would offer additional insights into the nature of the device. Annotating the device instances present in our infra, we get the following schema:

<details open>
<summary><strong>YAML Definition</strong></summary>

```yaml
- targets:
    - infrastructure: Infrastructure
  data:
    name: DeviceTypes
    value:
      "@type": type.googleapis.com/google.protobuf.ListValue
      value:
        - device_instance: host
          device_type: physical_host
        - device_instance: susw
          device_type: physical_switch
        - device_instance: sosw
          device_type: physical_switch
```

</details>

<br>

<details>
<summary><strong>JSON Definition</strong></summary>

```json
[
  {
    "targets": [
      {
        "infrastructure": "Infrastructure"
      }
    ],
    "data": {
      "name": "DeviceTypes",
      "value": {
        "@type": "type.googleapis.com/google.protobuf.ListValue",
        "value": [
          {
            "device_instance": "host",
            "device_type": "physical_host"
          },
          {
            "device_instance": "rack_switch",
            "device_type": "physical_switch"
          }
        ]
      }
    }
  }
]
```

</details>

<br>

We need to set the target, a list of elements defined in the infrastructure, and provide a value. The value contains a schema defining the `device_instance` and its associated `device_type`.

> Note: The schema can be internal to an organization.

## Example: Annotating Scale Up Switch with Open Config Interface

Another example is to define an `OpenConfigInterface` for our `scale up switch(sosw)` :

<details open>
<summary><strong>YAML Definition</strong></summary>

```yaml
- targets:
    - device_instance: sosw
  data:
    name: OpenConfigInterface
    value:
      "@type": type.googleapis.com/google.protobuf.Struct
      value:
        config:
          type: ...
          mtu: ...
          loopback-mode: ...
          enabled: ...
```

</details>

<br>

<details>
<summary><strong>JSON Definition</strong></summary>

```json
[
  {
    "targets": [
      {
        "device_instance": "sosw"
      }
    ],
    "data": {
      "name": "OpenConfigInterface",
      "value": {
        "@type": "type.googleapis.com/google.protobuf.Struct",
        "value": {
          "config": {
            "type": [],
            "mtu": [],
            "loopback-mode": [],
            "enabled": []
          }
        }
      }
    }
  }
]
```

</details>

<br>
