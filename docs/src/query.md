
# The `query_graph` API

## Overview
Once the infrastructure has been defined with `set_graph` and, optionally, extended with `annotate_graph`, the `query_graph` API is used to retrieve nodes, edges, or graph-level attributes that match a set of filters, or to resolve the shortest path between two nodes.

A single `QueryRequest` is a `choice` of exactly one of:

- `filters` — one or more named node/edge/graph filters, evaluated independently.
- `shortest_path` — a source/destination pair to resolve via the graph's shortest path.

The `QueryResponse` mirrors this with a matching `choice` of `filter_query_response` or `shortest_path_query_response`.

## Filter Requests
`Query.Request.Filter` accepts arrays of `node_filters` and `edge_filters`, plus a single `graph_filter`:

```python
query = QueryRequest()
query.filters.node_filters.add(name="...")   # 0 or more
query.filters.edge_filters.add(name="...")   # 0 or more
query.filters.graph_filter.attributes.add(attribute="...", value="...")
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

### Node Attribute Filter
```python
query = QueryRequest()
node_filter = query.filters.node_filters.add(name="smart_nic_filter")
node_filter.node_identifiers = ["dgx_h100"]
node_filter.attribute_filters.attributes.add(attribute="cx7_type", value="smart")

query_response = service.query_graph(query)
result = query_response.filter_query_response.node_filter_results[0]
for node in result.nodes:
    print(node.name, {a.attribute: a.value for a in node.attributes})
```

### Edge Attribute Filter
```python
query = QueryRequest()
edge_filter = query.filters.edge_filters.add(name="nvlink_filter")
edge_filter.attribute_filters.attributes.add(attribute="link_type", value="nvlink")

query_response = service.query_graph(query)
result = query_response.filter_query_response.edge_filter_results[0]
for edge in result.edges:
    print(edge.ep1, edge.ep2, {a.attribute: a.value for a in edge.attributes})
```

### Graph Attribute Filter
```python
query = QueryRequest()
query.filters.graph_filter.attributes.add(attribute="region", value="us-east")

query_response = service.query_graph(query)
graph_attrs = {a.attribute: a.value for a in query_response.filter_query_response.graph}
```

### Multiple Filters in One Request
Because `node_filters`/`edge_filters` are arrays of named filters, a single request can ask for several independent things at once, and the response keeps each one's matches separate:

```python
query = QueryRequest()

xpus = query.filters.node_filters.add(name="xpus")
xpus.attribute_filters.attributes.add(attribute="type", value="xpu")

nics = query.filters.node_filters.add(name="smart_nics")
nics.attribute_filters.attributes.add(attribute="cx7_type", value="smart")

query_response = service.query_graph(query)
for result in query_response.filter_query_response.node_filter_results:
    print(result.name, len(result.nodes))
```

## Shortest Path Requests
```python
query = QueryRequest()
query.shortest_path.name = "rank0-rank1"
query.shortest_path.source = service.get_endpoints("rank", "0")[0]
query.shortest_path.destination = service.get_endpoints("rank", "1")[0]

query_response = service.query_graph(query)
path = [node.name for node in query_response.shortest_path_query_response.nodes]
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
