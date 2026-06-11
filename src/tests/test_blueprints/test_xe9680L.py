import pytest
import networkx
from infragraph.infragraph import Api
from infragraph.infragraph_service import InfraGraphService
from infragraph.blueprints.devices.dell.xe9680L import Dellxe9680L


@pytest.mark.asyncio
@pytest.mark.parametrize("count", [1, 2])
@pytest.mark.parametrize(
    "xpu_type, nic_device",
    [
        ("h200", None),
        ("h200", "ocp"),
        ("b200", None),
        ("b200", "ocp"),
    ],
)
async def test_dellxe9680L(count, xpu_type, nic_device):
    """From a Dellxe9680L device, generate a graph and validate the graph.

    - with a count > 1 there should be no connectivity between device instances
    """
    device = Dellxe9680L(
        xpu_type=xpu_type,
        nic_device=nic_device,
    )
    device.validate()
    infrastructure = Api().infrastructure()
    infrastructure.devices.append(device)
    infrastructure.instances.add(name=device.name, device=device.name, count=count)
    service = InfraGraphService()
    service.set_graph(infrastructure)

    g = service.get_networkx_graph()
    print(f"\ndevice {device.name} xpu={xpu_type} nic={nic_device} count={count}")
    print(networkx.write_network_text(g, vertical_chains=True))


if __name__ == "__main__":
    pytest.main(["-s", __file__])