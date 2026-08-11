import pytest
from infragraph.infragraph_service import InfraGraphService


@pytest.fixture
def service():
    return InfraGraphService()


def test_device_only(service):
    """device — no slice, single name returned as-is"""
    result = service.expand_node_string("dgx")
    assert result == ["dgx"]


def test_device_with_slice(service):
    """device[] — one level with slice"""
    result = service.expand_node_string("dgx[0:3]")
    assert result == ["dgx.0", "dgx.1", "dgx.2"]


def test_device_component_no_component_slice(service):
    """device[]component — device has slice, component has no slice"""
    result = service.expand_node_string("dgx[0:2]cpu")
    assert result == ["dgx.0.cpu", "dgx.1.cpu"]


def test_device_component_with_slices(service):
    """device[]component[] — both levels have slices"""
    result = service.expand_node_string("dgx[0:2]cpu[0:2]")
    assert result == [
        "dgx.0.cpu.0",
        "dgx.0.cpu.1",
        "dgx.1.cpu.0",
        "dgx.1.cpu.1",
    ]


def test_device_two_components_last_no_slice(service):
    """device[]component[]component — two components, last has no slice"""
    result = service.expand_node_string("dgx[0:2]cpu[0:2]port")
    assert result == [
        "dgx.0.cpu.0.port",
        "dgx.0.cpu.1.port",
        "dgx.1.cpu.0.port",
        "dgx.1.cpu.1.port",
    ]


def test_device_two_components_all_slices(service):
    """device[]component[]component[] — all three levels have slices"""
    result = service.expand_node_string("dgx[0:2]cpu[0:2]port[0:3]")
    assert result == [
        "dgx.0.cpu.0.port.0",
        "dgx.0.cpu.0.port.1",
        "dgx.0.cpu.0.port.2",
        "dgx.0.cpu.1.port.0",
        "dgx.0.cpu.1.port.1",
        "dgx.0.cpu.1.port.2",
        "dgx.1.cpu.0.port.0",
        "dgx.1.cpu.0.port.1",
        "dgx.1.cpu.0.port.2",
        "dgx.1.cpu.1.port.0",
        "dgx.1.cpu.1.port.1",
        "dgx.1.cpu.1.port.2",
    ]


def test_empty_string(service):
    """empty input returns empty list"""
    result = service.expand_node_string("")
    assert result == []


def test_full_slice_uses_counts_from_instance_and_device_data(service):
    """dgx[:] — open slice resolved via _instance_data/_device_data counts"""
    from infragraph.infragraph_service import InstanceData, DeviceData

    service._instance_data["dgx"] = InstanceData("dgx_device", 3)
    dd = DeviceData()
    dd.components["cpu"] = 2
    service._device_data["dgx_device"] = dd

    assert service.expand_node_string("dgx[:]") == ["dgx.0", "dgx.1", "dgx.2"]
    assert service.expand_node_string("dgx[:-1]") == ["dgx.0", "dgx.1"]
    assert service.expand_node_string("dgx[1:]") == ["dgx.1", "dgx.2"]
    assert service.expand_node_string("dgx[::2]") == ["dgx.0", "dgx.2"]
    assert service.expand_node_string("dgx[-1]") == ["dgx.2"]


def test_negative_slice_without_known_count_raises(service):
    """dgx[:-1] with no instance/device data registered — count unknown"""
    from infragraph.infragraph_service import InfrastructureError

    with pytest.raises(InfrastructureError):
        service.expand_node_string("dgx[:-1]")


if __name__ == "__main__":
    pytest.main(["-s", __file__])
