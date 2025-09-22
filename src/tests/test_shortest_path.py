import pytest
import conftest
import networkx
from infragraph import *
from infragraph.infragraph_service import InfraGraphService


@pytest.mark.asyncio
async def test_rank_annotations(closfabric: Infrastructure):
    """Test shortest path

    - Need to be able to answer queries like:
        - give me all the npus present
        - how many server/host nics are present

    - Given an infrastructure
        - how do i add rank annotations?
        - how do i add comm group annotations?
        - these structures seems to be outside the definition of the graph
    - determine that every path from every rank to every other rank
    resolves using shortest path and is valid
    - everything needs an instance or separate graphs for devices?
    """
    service = InfraGraphService()
    service.set_graph(closfabric.serialize())

    npu_endpoints = service.get_endpoints("type", Component.NPU)
    for idx, npu_name in enumerate(npu_endpoints):
        service.get_networkx_graph().nodes[npu_name]["rank"] = idx
        data = service.get_networkx_graph().nodes[npu_name]
        print(f"{npu_name}: {data}")

    # want to ask the service the following:
    # give me all the nic endpoints that are for a device role of "server"
    # give me all the endpoints that have role of "leaf" and type "port"

    # find all endpoints that are neighbors of a server nic endpoint
    nic_endpoints = service.get_endpoints("type", Component.NIC)

    # rank2edge = closfabric.infrastructure.annotations.add(
    #     name="rank2node",
    #     description="""
    #         components:
    #           schemas:
    #             Rank2Edge:
    #               type: array
    #               items:
    #                 type: object
    #                   properties:
    #                     rank:
    #                       type: integer
    #                     node:
    #                       type: string
    #     """,
    # )
    # rank2edge.nodes.add(id="server.0.npu.0", name="rank", value="0")
    # rank2edge.nodes.add(id="server.0.npu.1", name="rank", value="1")

    # rank2edge.data = {}

    #     "data: {
    #         0: {"device": "dgxa100", "device_index": 0, "component": "npu", "component_index": 0},
    #         1: {"device": "dgxa100", "device_index": 1, "component": "npu", "component_index": 0},
    #     },
    # }

    # rank2component = {
    #     f"{v['device']}.{v['device_index']}.{v['component']}.{v['component_index']}": k
    #     for k, v in annotations["data"].items()
    # }

    # fabric_graph = networkx.graph.Graph()

    # fabric_graph.add_node("dgxa100.0.npu.0", rank=0)
    # fabric_graph.add_node("dgxa100.1.npu.0", rank=1)

    # fabric_graph.add_edge("th5sw.0.port.0", "th5sw.0.asic.0")
    # fabric_graph.add_edge("th5sw.0.port.1", "th5sw.0.asic.0")
    # fabric_graph.add_edge("th5sw.1.port.0", "th5sw.1.asic.0")
    # fabric_graph.add_edge("th5sw.1.port.1", "th5sw.1.asic.0")

    # fabric_graph.add_edge("th5sw.0.port.0", "dgxa100.0.port.0")
    # fabric_graph.add_edge("th5sw.1.port.0", "dgxa100.0.port.1")
    # fabric_graph.add_edge("th5sw.0.port.1", "dgxa100.1.port.0")
    # fabric_graph.add_edge("th5sw.1.port.1", "dgxa100.1.port.1")

    # fabric_graph.add_edge("dgxa100.0.port.0", "dgxa100.0-cx5.0.port.0")
    # fabric_graph.add_edge("dgxa100.0.port.1", "dgxa100.0-cx5.0.port.1")
    # fabric_graph.add_edge("dgxa100.1.port.0", "dgxa100.1-cx5.0.port.0")
    # fabric_graph.add_edge("dgxa100.1.port.1", "dgxa100.1-cx5.0.port.1")

    # fabric_graph.add_edge("dgxa100.0-cx5.0.port.0", "dgxa100.0-cx5.0.dpu.0")
    # fabric_graph.add_edge("dgxa100.0-cx5.0.port.1", "dgxa100.0-cx5.0.dpu.0")
    # fabric_graph.add_edge("dgxa100.1-cx5.0.port.0", "dgxa100.1-cx5.0.dpu.0")
    # fabric_graph.add_edge("dgxa100.1-cx5.0.port.1", "dgxa100.1-cx5.0.dpu.0")

    # fabric_graph.add_edge("dgxa100.0-cx5.0.dpu.0", "dgxa100.0.pciesw.0")
    # fabric_graph.add_edge("dgxa100.1-cx5.0.dpu.0", "dgxa100.1.pciesw.0")

    # fabric_graph.add_edge("dgxa100.0.pciesw.0", "dgxa100.0.npu.0")
    # fabric_graph.add_edge("dgxa100.1.pciesw.0", "dgxa100.1.npu.0")

    # # print(fabric_graph.nodes.data())

    # path = networkx.shortest_path(fabric_graph, source="dgxa100.0.npu.0", target="dgxa100.1.npu.0")
    # print(f"\nShortest Path between dgxa100.0.npu.0 and dgxa100.1.npu.0")
    # for edge in path:
    #     print(edge)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
