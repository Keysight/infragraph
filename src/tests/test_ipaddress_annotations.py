import pytest
import conftest
import ipaddress
from infragraph import *
from infragraph.closfabric import ClosFabric
from infragraph.infragraph_service import InfraGraphService


@pytest.mark.asyncio
async def test_ipaddress_annotations():
    """Test adding an ipaddress attribute to every server nic node"""
    service = InfraGraphService()
    service.set_graph(ClosFabric().serialize())

    nic_endpoints = service.get_endpoints("type", Component.NIC)  # FIXME replace with query_graph API
    annotate_request = AnnotateRequest()
    for idx, nic_endpoint in enumerate(nic_endpoints):
        annotate_request.nodes.add(
            name=nic_endpoint, attribute="ipaddress", value=str(ipaddress.ip_address(idx))
        )
    service.annotate_graph(annotate_request.serialize())
    nic_endpoints = service.get_endpoints("ipaddress")  # FIXME replace with query_graph API
    assert len(nic_endpoints) == len(annotate_request.nodes)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
