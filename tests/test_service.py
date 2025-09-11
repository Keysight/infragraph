import pytest
from infragraph import Api
from infragraph.examples.dgxa100 import DgxA100
from infragraph.examples.cx5 import Cx5
from infragraph.infragraph_service import InfraGraphService


@pytest.mark.asyncio
@pytest.mark.parametrize("device", [Cx5(), DgxA100(count=1)])
async def test_set_graph(device):
    """Generate a graph from a device and validate the graph."""
    pass
    # infrastructure = Api().infrastructure()
    # infrastructure.devices.append(device)
    # service = InfraGraphService()
    # service.set_graph(infrastructure.serialize())


if __name__ == "__main__":
    pytest.main(["-s", __file__])
