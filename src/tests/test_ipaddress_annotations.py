import pytest
import conftest
import ipaddress
from infragraph import *
from infragraph.closfabric import ClosFabric
from infragraph.infragraph_service import InfraGraphService


@pytest.mark.asyncio
async def test_ipaddress_annotations():
    """Test adding an ipaddress attribute to every server nic node"""
    # create the graph
    service = InfraGraphService()
    service.set_graph(ClosFabric())

    # query the graph for host nics
    npu_request = QueryRequest()
    filter = npu_request.node_filters.add(name="nic filter")
    filter.choice = QueryNodeFilter.ID_FILTER
    filter.id_filter.operator = QueryNodeId.REGEX
    filter.id_filter.value = r"host\.\d+\.nic\.\d+"
    nic_response = service.query_graph(npu_request)

    # annotate the graph
    annotate_request = AnnotateRequest()
    for idx, match in enumerate(nic_response.node_matches):
        annotate_request.nodes.add(
            name=match.id,
            attribute="ipaddress",
            value=str(ipaddress.ip_address(idx)),
        )
    service.annotate_graph(annotate_request)

    # query the graph for ipaddress attributes
    ipaddress_request = QueryRequest()
    filter = ipaddress_request.node_filters.add(name="ipaddress filter")
    filter.choice = QueryNodeFilter.ATTRIBUTE_FILTER
    filter.attribute_filter.name = "ipaddress"
    filter.attribute_filter.operator = QueryNodeId.REGEX
    filter.attribute_filter.value = r".*"
    ipaddress_response = service.query_graph(ipaddress_request)

    # validation
    assert len(nic_response.node_matches) > 0
    assert len(nic_response.node_matches) == len(annotate_request.nodes)
    assert len(annotate_request.nodes) == len(ipaddress_response.node_matches)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
