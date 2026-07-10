
# The `annotate_graph` API

## Overview
Once the infrastructure or system of systems has been defined by using the `set_graph` API the base graph can be extended by using the `annotate_graph` API to add additional data using nodes, edges, and links as endpoints for the data.

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

### Annotation Structure
The `annotate_graph` API accepts an `Annotation` object that targets **nodes**, **edges**, **links**, or the **graph** itself. Each target supports one or more key-value attributes:

```python
annotation = Annotation()

# add a node annotation
node = annotation.nodes.add(name="host.0.xpu.0")
node.attributes.add(attribute="rank", value="0")

# add an edge annotation
edge = annotation.edges.add(ep1="host.0.xpu.0", ep2="switch.0")
edge.attributes.add(attribute="bandwidth", value="400G")

# add a link annotation
link = annotation.links.add(name="pcie")
link.attributes.add(attribute="version", value="5.0")

# add a graph-level annotation
annotation.graph.add(attribute="cluster", value="rack-a")
annotation.graph.add(attribute="experiment", value="run-42")

service.annotate_graph(annotation)
```

### Node Name Slicing
Node names support a slicing operator that expands to the fully qualified dot-separated format, making it easy to target ranges of nodes without enumerating each one individually:

| Slice notation | Expands to |
|---|---|
| `server[0]xpu[0]` | `server.0.xpu.0` |
| `server[0:2]` | `server.0`, `server.1` |
| `server[0:2]xpu[0:3]` | `server.0.xpu.0`, `server.0.xpu.1`, `server.0.xpu.2`, `server.1.xpu.0`, ... |
| `switch` | `switch` (unchanged) |

The following code examples demonstrates how to use the `query_graph` API in conjunction with the `annotate_graph` API to extend the graph with additional user specific data.

## Adding `rank` data
In the [Getting Started](create.md) example, the instances of the `Server` device were created with the name of `host` and each instance having a specific number of components with a name of `xpu`.

The following code demonstrates adding a `rank` attribute to every `host` instance that has a component with the name of `xpu`. Each matching node is added to the `Annotation` object and a `rank` attribute is attached via `attributes.add`.
<details open>
<summary><strong>Add a rank to each host xpu</strong></summary>
```python
{% include-markdown "../../src/tests/test_rank_annotations.py" %}
```
</details>

## Adding `ipaddress` data
In the [Getting Started](create.md) example, the instances of the `Server` device were created with the name of `host` and each instance having a `mgmt` nic component.

The following code demonstrates adding an `ipaddress` attribute to the `host` instance `mgmt` nic. Each matching node is added to the `Annotation` object and an `ipaddress` attribute is attached via `attributes.add`.
<details open>
<summary><strong>Add an ipaddress to each host mgmt component</strong></summary>
```python
{% include-markdown "../../src/tests/test_ipaddress_annotations.py" %}
```
</details>

## Adding graph-level metadata
Graph-level annotations attach key-value attributes directly to the graph itself, rather than to a specific node, edge, or link. This is useful for tagging the entire infrastructure with metadata such as cluster identity, experiment context, environment, or ownership.

Graph attributes are stored in the NetworkX `Graph.graph` dictionary and are returned in the `annotations.graph` field of both `infragraph` and `networkx` `get_graph` responses.

Immutable infrastructure-derived attributes (e.g., `type`, `link`) are rejected on graph targets, consistent with node and edge annotation rules.

<details open>
<summary><strong>Add metadata attributes to the graph</strong></summary>
```python
{% include-markdown "../../src/tests/test_graph_annotations.py" %}
```
</details>

## Querying graph-level metadata
Graph-level attributes added with `annotate_graph` can be queried with the `query_graph` API using a `graph_filters` request, filtering by attribute name using the `eq`, `contains`, or `regex` operators.

<details open>
<summary><strong>Query metadata attributes on the graph</strong></summary>
```python
{% include-markdown "../../src/tests/test_graph_query.py" %}
```
</details>
