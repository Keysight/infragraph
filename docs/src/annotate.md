
# The `annotate_graph` API

## Overview
Once the infrastructure or system of systems has been defined by using the `set_graph` API the base graph can be extended by using the `annotate_graph` API to add additional data using nodes and edges as endpoints for the data.

The main objective of the `annotate_graph` API is to separate the infrastructure model from specific use-case models by allowing the graph to be extended with any type of data.  This ensures that `InfraGraph` does not morph into an attempt to define every nuance present in a system of systems.

Any annotation efforts can always be proposed as model or service enhancements by submitting [issues](https://github.com/Keysight/infragraph/issues) or [pull requests](https://github.com/Keysight/infragraph/pulls) to the [InfraGraph repository](https://github.com/Keysight/infragraph).

### Additional Data
Some examples of additional data are:
- AI data such as:
  - ranks
  - communication groups
- Configuration data such as:
  - network interface card settings
  - device addresses
  - device routing tables

The following code examples demonstrates how to use the `query_graph` API in conjunction with the `annotate_graph` API to extend the graph with additional user specific data.

## Adding `rank` data
In the [Getting Started](create.md) example, the device `Server` has a specific number of `npu` components.

The following code demonstrates adding a `rank` attribute to every node that is of type `NPU`.
<details open>
<summary><strong>Add a rank to each npu</strong></summary>
```python
{% include-markdown "../../src/tests/test_rank_annotations.py" %}
```
</details>

## Adding `ipaddress` data
In the [Getting Started](create.md) example the instances of the `Server` device were created with the name of `host`.

The following code demonstrates how to add an `ipaddress` attribute to every node that is an instance of `host`.
<details open>
<summary><strong>Add an ipaddress to each host</strong></summary>
```python
{% include-markdown "../../src/tests/test_ipaddress_annotations.py" %}
```
</details>
