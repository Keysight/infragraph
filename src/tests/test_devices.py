import pytest
import conftest
import networkx
from infragraph.infragraph import Api
from infragraph.infragraph_service import InfraGraphService
from infragraph.cx5 import Cx5
from infragraph.dgx import Dgx
from infragraph.server import Server
from infragraph.switch import Switch


@pytest.mark.asyncio
@pytest.mark.parametrize("count", [1, 3])
@pytest.mark.parametrize("instance", ["a", "b"])
@pytest.mark.parametrize(
    "device",
    [
        Server(),
        Switch(),
        Cx5(),
        Dgx(),
    ],
)
async def test_set_graph(count, instance, device):
    """Validate the device, generate a graph from a device and validate the graph."""
    device.validate()
    infrastructure = Api().infrastructure()
    infrastructure.devices.append(device)
    infrastructure.instances.add(name=instance, device=device.name, count=count)
    service = InfraGraphService()
    service.set_graph(infrastructure.serialize())
    g = service.get_networkx_graph()
    print(f"{device.name} is a {g}")
    print(service.get_graph())
    print(networkx.write_network_text(g, vertical_chains=True))


if __name__ == "__main__":
    pytest.main(["-s", __file__])
