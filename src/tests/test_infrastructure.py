import pytest
import conftest
import networkx
from infragraph import *
from infragraph.closfabric import ClosFabric
from infragraph.infragraph_service import InfraGraphService


@pytest.mark.asyncio
async def test_infrastructure():
    """Validate the device, generate a graph from a device and validate the graph."""
    # create the graph
    service = InfraGraphService()
    service.set_graph(ClosFabric())

    # validations
    g = service.get_networkx_graph()
    print(f"\nInfrastructure is a {g}")
    print(networkx.write_network_text(g, vertical_chains=True))

    npu_request = QueryRequest()
    query_filter = npu_request.node_filters.add(name="npu filter")
    query_filter.choice = QueryNodeFilter.ATTRIBUTE_FILTER
    query_filter.attribute_filter.name = "type"
    query_filter.attribute_filter.operator = QueryNodeId.EQ
    query_filter.attribute_filter.value = "npu"
    query_filter = npu_request.node_filters.add(name="instance filter")
    query_filter.choice = QueryNodeFilter.ATTRIBUTE_FILTER
    query_filter.attribute_filter.name = "instance"
    query_filter.attribute_filter.operator = QueryNodeId.EQ
    query_filter.attribute_filter.value = "host"
    query_filter = npu_request.node_filters.add(name="instance idx filter")
    query_filter.choice = QueryNodeFilter.ATTRIBUTE_FILTER
    query_filter.attribute_filter.name = "instance_idx"
    query_filter.attribute_filter.operator = QueryNodeId.EQ
    query_filter.attribute_filter.value = "0"
    npu_response = service.query_graph(npu_request)
    print('Nodes')
    npu_nodes = []
    for nodes in npu_response.node_matches:
        print(nodes.id)
        npu_nodes.append(nodes.id)
    

if __name__ == "__main__":
    pytest.main(["-s", __file__])
