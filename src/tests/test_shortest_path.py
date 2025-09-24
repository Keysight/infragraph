import pytest
import conftest
import networkx
from infragraph import *
from infragraph.infragraph_service import InfraGraphService


@pytest.mark.asyncio
async def test_shortest_path(closfabric: Infrastructure):
    service = InfraGraphService()
    service.set_graph(closfabric.serialize())

    # add ranks
    npu_endpoints = service.get_endpoints("type", Component.NPU)
    annotate_request = AnnotateRequest()
    for idx, npu_endpoint in enumerate(npu_endpoints):
        annotate_request.nodes.add(name=npu_endpoint, attribute="rank", value=str(idx))
    service.annotate_graph(annotate_request.serialize())

    # find shortest path from one rank to another
    # path = networkx.shortest_path(fabric_graph, source="dgxa100.0.npu.0", target="dgxa100.1.npu.0")
    # print(f"\nShortest Path between dgxa100.0.npu.0 and dgxa100.1.npu.0")
    # for edge in path:
    #     print(edge)
