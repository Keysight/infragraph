import pytest
import conftest
import networkx
import ipaddress
from infragraph import *
from infragraph.infragraph_service import InfraGraphService


@pytest.mark.asyncio
async def test_rank_annotations(closfabric: Infrastructure):
    """Test adding rank attribute to every npu node"""
    service = InfraGraphService()
    service.set_graph(closfabric.serialize())

    npu_endpoints = service.get_endpoints("type", Component.NPU)  # FIXME replace with query_graph API
    annotate_request = AnnotateRequest()
    for idx, npu_endpoint in enumerate(npu_endpoints):
        annotate_request.nodes.add(name=npu_endpoint, attribute="rank", value=str(idx))
    service.annotate_graph(annotate_request.serialize())
    npu_endpoints = service.get_endpoints("rank")  # FIXME replace with query_graph API
    assert len(npu_endpoints) == len(annotate_request.nodes)


@pytest.mark.asyncio
async def test_nic_annotations(closfabric: Infrastructure):
    """Test adding nic attributes to every server nic node"""
    service = InfraGraphService()
    service.set_graph(closfabric.serialize())

    nic_endpoints = service.get_endpoints("type", Component.NIC)  # FIXME replace with query_graph API
    annotate_request = AnnotateRequest()
    for idx, nic_endpoint in enumerate(nic_endpoints):
        annotate_request.nodes.add(
            name=nic_endpoint, attribute="ip_address", value=str(ipaddress.ip_address(idx))
        )
    service.annotate_graph(annotate_request.serialize())
    nic_endpoints = service.get_endpoints("ip_address")  # FIXME replace with query_graph API
    assert len(nic_endpoints) == len(annotate_request.nodes)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
