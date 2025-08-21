import pytest
import networkx


@pytest.mark.asyncio
async def test_edges(closfabric):
    """Add networkx edges, get shortest path
    - Need to be able to answer simple questions like, how many npus are present, how many are being used etc
    - given an infrastructure, rank annotations, and an all to all scenario
    - determine that every path from every rank to every other rank
    resolves using shortest path and is valid
    - everything needs an instance or separate graphs for devices?
    """
    annotations = {
        "name": "rank2component",
        "description": "Rank number to device and component instance",
        "data": {
            0: {"device": "dgxa100", "device_index": 0, "component": "npu", "component_index": 0},
            1: {"device": "dgxa100", "device_index": 1, "component": "npu", "component_index": 0},
        },
    }

    rank2component = {
        f"{v['device']}.{v['device_index']}.{v['component']}.{v['component_index']}": k for k, v in annotations["data"].items()
    }

    fabric_graph = networkx.graph.Graph()

    fabric_graph.add_node("dgxa100.0.npu.0", rank=0)
    fabric_graph.add_node("dgxa100.1.npu.0", rank=1)

    fabric_graph.add_edge("th5sw.0.port.0", "th5sw.0.asic.0")
    fabric_graph.add_edge("th5sw.0.port.1", "th5sw.0.asic.0")
    fabric_graph.add_edge("th5sw.1.port.0", "th5sw.1.asic.0")
    fabric_graph.add_edge("th5sw.1.port.1", "th5sw.1.asic.0")

    fabric_graph.add_edge("th5sw.0.port.0", "dgxa100.0.port.0")
    fabric_graph.add_edge("th5sw.1.port.0", "dgxa100.0.port.1")
    fabric_graph.add_edge("th5sw.0.port.1", "dgxa100.1.port.0")
    fabric_graph.add_edge("th5sw.1.port.1", "dgxa100.1.port.1")

    fabric_graph.add_edge("dgxa100.0.port.0", "dgxa100.0-cx5.0.port.0")
    fabric_graph.add_edge("dgxa100.0.port.1", "dgxa100.0-cx5.0.port.1")
    fabric_graph.add_edge("dgxa100.1.port.0", "dgxa100.1-cx5.0.port.0")
    fabric_graph.add_edge("dgxa100.1.port.1", "dgxa100.1-cx5.0.port.1")

    fabric_graph.add_edge("dgxa100.0-cx5.0.port.0", "dgxa100.0-cx5.0.dpu.0")
    fabric_graph.add_edge("dgxa100.0-cx5.0.port.1", "dgxa100.0-cx5.0.dpu.0")
    fabric_graph.add_edge("dgxa100.1-cx5.0.port.0", "dgxa100.1-cx5.0.dpu.0")
    fabric_graph.add_edge("dgxa100.1-cx5.0.port.1", "dgxa100.1-cx5.0.dpu.0")

    fabric_graph.add_edge("dgxa100.0-cx5.0.dpu.0", "dgxa100.0.pciesw.0")
    fabric_graph.add_edge("dgxa100.1-cx5.0.dpu.0", "dgxa100.1.pciesw.0")

    fabric_graph.add_edge("dgxa100.0.pciesw.0", "dgxa100.0.npu.0")
    fabric_graph.add_edge("dgxa100.1.pciesw.0", "dgxa100.1.npu.0")

    # print(fabric_graph.nodes.data())

    path = networkx.shortest_path(fabric_graph, source="dgxa100.0.npu.0", target="dgxa100.1.npu.0")
    print(f"\nShortest Path between dgxa100.0.npu.0 and dgxa100.1.npu.0")
    for edge in path:
        print(edge)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
