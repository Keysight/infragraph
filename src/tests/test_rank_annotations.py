import pytest
import conftest
from infragraph import *
from infragraph.closfabric import ClosFabric
from infragraph.infragraph_service import InfraGraphService


@pytest.mark.asyncio
async def test_rank_annotations():
    """Test adding rank attribute to every npu node"""
    service = InfraGraphService()
    service.set_graph(ClosFabric().serialize())

    npu_endpoints = service.get_endpoints("type", Component.NPU)  # FIXME replace with query_graph API
    annotate_request = AnnotateRequest()
    for idx, npu_endpoint in enumerate(npu_endpoints):
        annotate_request.nodes.add(name=npu_endpoint, attribute="rank", value=str(idx))
    service.annotate_graph(annotate_request.serialize())
    npu_endpoints = service.get_endpoints("rank")  # FIXME replace with query_graph API
    assert len(npu_endpoints) == len(annotate_request.nodes)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
