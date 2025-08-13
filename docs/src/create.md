## Case Study: Two Tier Clos Fabric
The main steps in designing a network infrastructure are as follows:

* Use text and/or diagrams to create an `infrastructure description`
* Then `use the standardized schema to capture the infrastructure description` in a machine readable format by doing the following:
    * Define `device` subgraphs using `components` and `links` and create `instances` of each device
    * Define `infrastructure links` to define the types of connectivity that exists between `device instances` in the infrastructure
    * Create `infrastructure connections` between `device instances` using `infrastructure links`

## Infrastructure Description
The following is a diagrammatic and textual description of a `generic` two tier clos fabric that will be modeled using the standardized schema.

![spine and leaf](./images/spine-and-leaf.jpg)

It consists of the following devices:

* 4 generic `servers` with each server composed of 4 npus and 4 nics with each nic directly connected to one npu via a pcie link.  Also every npu in a server is connected to every other npu by an nvlink switch.
* 4 `leaf switches` composed of one asic and 16 ethernet ports
* 3 `spine switches` composed of one asic and 16 ethernet ports

The above devices will be interconnected in the following manner:

* each `leaf` switch is connected directly to 1 `server` and to all `spine` switches
* each nic in the `server` is connected to a `leaf` switch port at 100 gpbs
* a port in the `leaf` switch is connected to every `spine` switch at 400 gpbs

## Standardized Definitions
A standardized definition of the preceding two tier clos fabric can be created by following these steps:

* The device is a subgraph which is composed of two components connected to each other using a link.
* It acts as a blueprint allowing for a single definition to be reused multiple times for optimal space complexity.

#### Create a Server Device and Instances
Define a server device based on the preceding infrastructure description.
<details open>
<summary><strong>Server Device Definition using OpenAPI Device Model</strong></summary>
```yaml
{% include-markdown "./examples/two-tier-clos-fabric-server.yaml" %}
```
</details>

#### Create a Switch Device and Instances
Define a switch device based on the preceding infrastructure description.
<details open>
<summary><strong>Switch Device Definition using OpenAPI Device Model</strong></summary>
```yaml
{% include-markdown "./examples/two-tier-clos-fabric-switch.yaml" %}
```
</details>

#### Create an Infrastructure of Links and Connections
<details open>
<summary><strong>Two Tier Clos Fabric Infrastructure using OpenAPI Device Model</strong></summary>
```yaml
{% include-markdown "./examples/two-tier-clos-fabric-infrastructure.yaml" %}
```
</details>

