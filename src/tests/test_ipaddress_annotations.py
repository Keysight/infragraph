import pytest
import ipaddress
from infragraph import *
from infragraph.blueprints.fabrics.closfabric import ClosFabric
from infragraph.infragraph_service import InfraGraphService


@pytest.mark.asyncio
async def test_ipaddress_annotations():
    """Test adding an ipaddress attribute to every server nic node"""
    # create the graph
    service = InfraGraphService()
    service.set_graph(ClosFabric())

    # query the graph for host nics
    npu_request = QueryRequest()
    npu_request.filters.node_filters.attribute_filters.attributes.add(attribute="type", value="mgmt-nic")
    nic_response = service.query_graph(npu_request)
    assert len(nic_response.nodes) > 0

    # annotate the graph
    annotation = Annotation()
    for idx, match in enumerate(nic_response.nodes):
        annotation_node = annotation.nodes.add(
            name=match.name
        )
        annotation_node.attributes.add(attribute="ipaddress", value=str(ipaddress.ip_address(idx)))
    service.annotate_graph(annotation)

    # query the graph for ipaddress attributes
    ipaddress_request = QueryRequest()
    ipaddress_request.filters.node_filters.attribute_filters.attributes.add(attribute="ipaddress", value="")
    ipaddress_response = service.query_graph(ipaddress_request)

    # validation
    assert len(nic_response.nodes) > 0
    assert len(nic_response.nodes) == len(annotation.nodes)
    assert len(annotation.nodes) == len(ipaddress_response.nodes)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
