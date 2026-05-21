import pytest
import networkx
from infragraph.infragraph import Api
from infragraph.infragraph_service import InfraGraphService
from infragraph.blueprints.devices.amd.mi300x import MI300X


@pytest.mark.asyncio
@pytest.mark.parametrize("count", [1, 2])
@pytest.mark.parametrize(
    "device",
    [
        MI300X(),
    ],
)
async def test_mi300x(count, device):
    """From an MI300X device, generate a graph and validate the graph.

    - with a count > 1 there should be no connectivity between device instances
    """
    device.validate()
    infrastructure = Api().infrastructure()
    infrastructure.devices.append(device)
    infrastructure.instances.add(name=device.name, device=device.name, count=count)
    service = InfraGraphService()
    service.set_graph(infrastructure)

    g = service.get_networkx_graph()
    print(f"\ndevice {device.name} is a {g}")
    print(networkx.write_network_text(g, vertical_chains=True))


if __name__ == "__main__":
    pytest.main(["-s", __file__])