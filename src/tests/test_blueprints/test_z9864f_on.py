import networkx
import pytest
from infragraph.infragraph import Api
from infragraph.infragraph_service import InfraGraphService
from infragraph.blueprints.devices.dell.z9864f_on import DellPowerSwitchZ9864FOn
from infragraph.visualizer.visualize import run_visualizer

def print_graph(graph):
    for node, attrs in graph.nodes(data=True):
        print(f"Node: {node}, Attributes: {attrs}")

    for u, v, attrs in graph.edges(data=True):
        print(f"Edge: ({u}, {v}), Attributes: {attrs}")
    pass

@pytest.mark.asyncio
@pytest.mark.parametrize("count", [1, 2])
async def test_z9864fon(count):
    # create device
    device = DellPowerSwitchZ9864FOn()

    # create infrastructure
    infrastructure = Api().infrastructure()
    infrastructure.devices.append(device)
    infrastructure.instances.add(
        name=device.name,
        device=device.name,
        count=count,
    )

    # validate
    device.validate()
    service = InfraGraphService()
    service.set_graph(infrastructure)

    # validations
    g = service.get_networkx_graph()
    print(f"\ndevice {device.name} is a {g}")
    print(networkx.write_network_text(g, vertical_chains=True))
    print_graph(g)

if __name__ == "__main__":
    pytest.main(["-s", __file__])