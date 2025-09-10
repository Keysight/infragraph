from typing import List, Union
import pytest
import networkx
import infragraph
from infragraph.examples.dgxa100 import DgxA100
from infragraph.examples.cx5 import Cx5


def to_graph(device: infragraph.Device) -> networkx.graph.Graph:
    """A recursive method that returns a networkx Graph object
    with all edges from the device and any nested devices within.
    """
    graph = networkx.graph.Graph()

    for edge in device.edges:
        for device_idx in range(device.count):
            endpoint2 = endpoint1 = f"{device.name}.{device_idx}"
            for piece in edge.ep1:
                endpoint1 += f".{piece}"
            for piece in edge.ep2:
                endpoint2 += f".{piece}"
        graph.add_edge(endpoint1, endpoint2, link=edge.link)

    return graph


@pytest.mark.asyncio
@pytest.mark.parametrize("device", [Cx5()])
async def test_device_graph(device):
    """Generate a graph from a device and validate the graph."""
    graph = to_graph(device)
    print(f"\n\nDevice: {device.name} {device.description}")
    print(f"\tEdges:")
    for u, v, link in graph.edges.data("link"):
        print(f"\t\t{u}.{link}.{v}")
    print(f"\tLeaf Components:")
    for node in [node for node, degree in graph.degree() if degree == 1]:
        print(f"\t\t{node}")

    assert networkx.is_connected(graph) is True


if __name__ == "__main__":
    pytest.main(["-s", __file__])
