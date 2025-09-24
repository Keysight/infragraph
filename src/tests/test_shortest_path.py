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
    g = service.get_networkx_graph()
    print(f"\nInfrastructure is a {g}")
    print(networkx.write_network_text(g, vertical_chains=True))

    # find shortest path from one rank to another
    src_endpoint = service.get_endpoints("rank", "0")[0]
    dst_endpoint = service.get_endpoints("rank", "1")[0]
    path = service.get_shortest_path(src_endpoint, dst_endpoint)
    print(f"\nShortest Path between {src_endpoint} and {dst_endpoint}")
    for edge in path:
        print(edge)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
