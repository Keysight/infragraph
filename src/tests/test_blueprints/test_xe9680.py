import pytest
import networkx
from infragraph.infragraph import Api
from infragraph.infragraph_service import InfraGraphService
from infragraph.blueprints.devices.dell.xe9680 import Dellxe9680


@pytest.mark.asyncio
@pytest.mark.parametrize("count", [1, 2])
@pytest.mark.parametrize(
    "xpu_type, storage_type, nic_device",
    [
        ("h200", "u.2nvme", None),
        ("h100", "e3.s", None),
        ("a100", "u.2nvme", None),
        ("h20", "u.2sas/sata", None),
        ("mi300x", "u.2nvme", None),
        ("gaudi3", "e3.s", None),
        ("h200", "u.2nvme", "ocp"),
    ],
)
async def test_dellxe9680(count, xpu_type, storage_type, nic_device):
    """From a Dellxe9680 device, generate a graph and validate the graph.

    - with a count > 1 there should be no connectivity between device instances
    """
    device = Dellxe9680(
        xpu_type=xpu_type,
        storage_type=storage_type,
        nic_device=nic_device,
    )
    device.validate()
    infrastructure = Api().infrastructure()
    infrastructure.devices.append(device)
    infrastructure.instances.add(name=device.name, device=device.name, count=count)
    service = InfraGraphService()
    service.set_graph(infrastructure)

    g = service.get_networkx_graph()
    print(f"\ndevice {device.name} xpu={xpu_type} storage={storage_type} nic={nic_device} count={count}")
    print(networkx.write_network_text(g, vertical_chains=True))


if __name__ == "__main__":
    pytest.main(["-s", __file__])