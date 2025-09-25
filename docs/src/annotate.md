
# Binding Custom Attributes to Graph Nodes

The primary purpose of infra.proto is to define and design a generic network fabric. This enables end users to specify the devices as nodes and links as edges. The data model also allows for the definition and design of devices by adding links and components within the device, modeling the device internals as a subgraph.
Another data model, annotate.proto, allows for the definition and binding of various parameters within the generic infrastructure. Users can bind:

- Vendor-specific data
- Additional qualities of the infrastructure
- Specific device performance attributes, such as:
  - Latency
  - Routing tables

This helps to add more context and content to infrastructure elements.

The main objective is to decouple various bindings from the infrastructure, separating the concerns of designing the logical infrastructure from the additional data needed for specific use-cases.

## Adding a `Rank` attribute to all `NPU` nodes

The following code demonstrates adding a `rank` attribute to every node that is of type `NPU`.

<details open>
<summary><strong>Rank Annotation Test</strong></summary>
```python
{% include-markdown "../../src/tests/test_rank_annotations.py" %}
```
</details>


## Adding an `ip_address` attribute to all `NIC` nodes

The following code demonstrates adding an `ip_address` attribute to every node that is of type `NIC`.

<details open>
<summary><strong>IpAddress Annotation Test</strong></summary>
```python
{% include-markdown "../../src/tests/test_nic_annotations.py" %}
```
</details>
