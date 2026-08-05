
# The `query_graph` API

## Overview
Once the infrastructure has been defined with `set_graph` and, optionally, extended with `annotate_graph`, the `query_graph` API is used to retrieve nodes, edges, or graph-level attributes that match a set of filters, or to resolve the shortest path between two nodes.

A single `QueryRequest` is a `choice` of exactly one of:

- `attribute_query` — one or more named node/edge/graph filters, evaluated independently.
- `shortest_path_query` — a source/destination pair to resolve via the graph's shortest path.

The `QueryResponse` mirrors this with a matching `choice` of `attribute_query` or `shortest_path_query`.

## Attribute Query Requests
`Query.Request.Filter` accepts arrays of `node_filters` and `edge_filters`, plus a single `graph_filter`:

```python
query = QueryRequest()
query.attribute_query.node_filters.add(name="...")   # 0 or more
query.attribute_query.edge_filters.add(name="...")   # 0 or more
query.attribute_query.graph_filter.attributes.add(attribute="...", value="...")
```

Every node/edge filter requires a unique **`name`**. Names are what let you tell the results of one filter apart from another when a request carries several — the response groups matches by that name rather than merging everything into one list.

### Node and Edge Matching Rules
Each `node_filter` combines `node_identifiers` (or `endpoints` for edges) with `attribute_filters`. Both are optional, but at least one must be set:

| `node_identifiers` / `endpoints` | `attribute_filters` | Result |
|---|---|---|
| unset | unset | No results. |
| set | unset | All matching nodes/edges, with every attribute. |
| unset | set | Every node/edge in the graph that matches the attribute filter. |
| set | set | Matching nodes/edges that also satisfy the attribute filter. |

`node_identifiers` and edge `endpoints` support the same [slicing operator](annotate.md#node-name-slicing) used by `annotate_graph`, so a single entry like `server[0:2]xpu[0:3]` expands to every matching node.

`attribute_filters` takes one or more `attribute`/`value` pairs and an optional `logic` (`and`/`or`, defaults to `and`) to combine them.

`attribute_filters` is a single filter shared across **every** entry in `node_identifiers`/`endpoints` within that filter — it cannot be set differently per identifier. If you need different attribute criteria for different node identifiers or edge endpoints, use separate `node_filters`/`edge_filters` entries (each with its own `name`), one per distinct attribute criteria.

### Default Schema Properties
Every node and edge carries a set of attributes derived directly from the infrastructure schema, in addition to anything added later via `annotate_graph`. `attribute_filters` can match against these the same way it matches user-added annotations.

Node (component) attributes:

| Attribute | Description |
|---|---|
| `type` | The component type of this node (e.g. `xpu`, `nic`, `cpu`). |
| `device` | Name of the device model this component belongs to (e.g. `dgx_h100`). |
| `instance` | The parent instance path this component belongs to. |
| `instance_idx` | Numeric index of the parent instance. |
| `composed_device` | Full instance path this component was composed under. |

Edge attributes:

| Attribute | Description |
|---|---|
| `link` | Name of the link/interconnect connecting the two endpoints (e.g. `pcie`, `nvlink`). |
| `bandwidth` | Present when the link's physical bandwidth is defined in the schema, e.g. `"1400 Gbps"`. |
| `latency` | Present when the link's physical latency is defined in the schema, e.g. `"5 ns"`. |

`type`, `device`, `instance`, `instance_idx`, `composed_device`, and `link` are immutable — `annotate_graph` rejects attempts to overwrite them. `bandwidth` and `latency` are not immutable and may be overwritten.

### Node Attribute Filter
```python
query = QueryRequest()
node_filter = query.attribute_query.node_filters.add(name="smart_nic_filter")
node_filter.node_identifiers = ["dgx_h100"]
node_filter.attribute_filters.attributes.add(attribute="cx7_type", value="smart")

query_response = service.query_graph(query)
result = query_response.attribute_query.nodes[0]
for node in result.nodes:
    print(node.name, {a.attribute: a.value for a in node.attributes})
```

### Edge Attribute Filter
```python
query = QueryRequest()
edge_filter = query.attribute_query.edge_filters.add(name="nvlink_filter")
edge_filter.attribute_filters.attributes.add(attribute="link_type", value="nvlink")

query_response = service.query_graph(query)
result = query_response.attribute_query.edges[0]
for edge in result.edges:
    print(edge.ep1, edge.ep2, {a.attribute: a.value for a in edge.attributes})
```

### Graph Attribute Filter
```python
query = QueryRequest()
query.attribute_query.graph_filter.attributes.add(attribute="region", value="us-east")

query_response = service.query_graph(query)
graph_attrs = {a.attribute: a.value for a in query_response.attribute_query.graph}
```

### Multiple Filters in One Request
Because `node_filters`/`edge_filters` are arrays of named filters, a single request can ask for several independent things at once, and the response keeps each one's matches separate:

```python
query = QueryRequest()

xpus = query.attribute_query.node_filters.add(name="xpus")
xpus.attribute_filters.attributes.add(attribute="type", value="xpu")

nics = query.attribute_query.node_filters.add(name="smart_nics")
nics.attribute_filters.attributes.add(attribute="cx7_type", value="smart")

query_response = service.query_graph(query)
for result in query_response.attribute_query.nodes:
    print(result.name, len(result.nodes))
```

## Shortest Path Requests
```python
query = QueryRequest()
query.shortest_path_query.name = "rank0-rank1"
query.shortest_path_query.source = service.get_endpoints("rank", "0")[0]
query.shortest_path_query.destination = service.get_endpoints("rank", "1")[0]

query_response = service.query_graph(query)
path = [node.name for node in query_response.shortest_path_query.nodes]
```

`source` and `destination` must be exact node IDs (not slice expressions) already present in the graph.

## Full Examples
<details open>
<summary><strong>Node, edge, and graph attribute filter queries</strong></summary>
```python
{% include-markdown "../../src/tests/test_graph_query.py" %}
```
</details>

<details open>
<summary><strong>Shortest path query</strong></summary>
```python
{% include-markdown "../../src/tests/test_shortest_path.py" %}
```
</details>
