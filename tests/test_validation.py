import pytest
import infragraph
from infragraph.examples.dgxa100 import DgxA100
from infragraph.examples.cx5 import Cx5


@pytest.mark.asyncio
@pytest.mark.parametrize("device", [DgxA100(count=4), Cx5()])
@pytest.mark.parametrize("serialization", [infragraph.Device.JSON, infragraph.Device.YAML])
async def test_device_serialization(device, serialization):
    """Test device validation"""
    pass
    # print(device.serialize(serialization))


@pytest.mark.asyncio
@pytest.mark.parametrize("device", [DgxA100(count=4), Cx5()])
async def test_device_append(device):
    """Test device append"""
    pass
    # infra = infragraph.Infrastructure(name="test", description="Test Infrastructure Device Append")
    # infra.devices.append(device)
    # print(infra)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
