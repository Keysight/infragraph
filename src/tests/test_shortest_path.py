from typing import Tuple, Generator
import pytest
from infragraph import *
from infragraph.closfabric import ClosFabric
from infragraph.infragraph_service import InfraGraphService


@pytest.mark.asyncio
@pytest.mark.parametrize("ranks", [(i, i + 1) for i in range(0, 7)])
async def test_shortest_path(ranks: Tuple[int, int]):
    """Test resolving the shortest path from one rank to another"""
    service = InfraGraphService()
    service.set_graph(ClosFabric().serialize())

    # add ranks
    npu_endpoints = service.get_endpoints("type", Component.NPU)
    annotate_request = AnnotateRequest()
    for idx, npu_endpoint in enumerate(npu_endpoints):
        annotate_request.nodes.add(name=npu_endpoint, attribute="rank", value=str(idx))
    service.annotate_graph(annotate_request.serialize())

    # find shortest path from one rank to another
    src_endpoint = service.get_endpoints("rank", str(ranks[0]))[0]
    dst_endpoint = service.get_endpoints("rank", str(ranks[1]))[0]
    path = service.get_shortest_path(src_endpoint, dst_endpoint)
    print(f"\nShortest Path between rank {ranks[0]} and rank {ranks[1]}")
    print(f"\t{' -> '.join(path)}")


if __name__ == "__main__":
    pytest.main(["-s", __file__])
