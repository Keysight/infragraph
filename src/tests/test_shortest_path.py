from typing import Tuple
import pytest
from infragraph import *
from infragraph.blueprints.fabrics.closfabric import ClosFabric
from infragraph.infragraph_service import InfraGraphService


@pytest.mark.asyncio
@pytest.mark.parametrize("ranks", [(i, i + 1) for i in range(0, 7)])
async def test_shortest_path(ranks: Tuple[int, int]):
    """Test resolving the shortest path from one rank to another"""
    service = InfraGraphService()
    service.set_graph(ClosFabric().serialize())

    # add ranks
    npu_endpoints = service.get_endpoints("type", Component.XPU)
    annotation = Annotation()
    for idx, npu_endpoint in enumerate(npu_endpoints):
        annotation_node = annotation.nodes.add(
            name=npu_endpoint
        )
        annotation_node.attributes.add(attribute="rank", value=str(idx))
    service.annotate_graph(annotation.serialize())

    # find shortest path from one rank to another
    query = Query()
    query.shortest_path.name = "rank0-rank1"
    
    
    query.shortest_path.source = service.get_endpoints("rank", str(ranks[0]))[0]
    query.shortest_path.destination = service.get_endpoints("rank", str(ranks[1]))[0]

    query_response = service.query_graph(query)
    shortest_route = ""
    for node in query_response.nodes:
        shortest_route = shortest_route + " -> " + node.name
    
    print(f"\nShortest Path between rank {ranks[0]} and rank {ranks[1]}")
    print(shortest_route)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
