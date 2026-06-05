import pytest
from infragraph.infragraph_service import InfraGraphService


@pytest.fixture
def service():
    return InfraGraphService()


def test_device_only(service):
    """device — no slice, single name returned as-is"""
    result = service._expand_node_string("dgx")
    assert result == ["dgx"]


def test_device_with_slice(service):
    """device[] — one level with slice"""
    result = service._expand_node_string("dgx[0:3]")
    assert result == ["dgx.0", "dgx.1", "dgx.2"]


def test_device_component_no_component_slice(service):
    """device[]component — device has slice, component has no slice"""
    result = service._expand_node_string("dgx[0:2]cpu")
    assert result == ["dgx.0.cpu", "dgx.1.cpu"]


def test_device_component_with_slices(service):
    """device[]component[] — both levels have slices"""
    result = service._expand_node_string("dgx[0:2]cpu[0:2]")
    assert result == [
        "dgx.0.cpu.0",
        "dgx.0.cpu.1",
        "dgx.1.cpu.0",
        "dgx.1.cpu.1",
    ]


def test_device_two_components_last_no_slice(service):
    """device[]component[]component — two components, last has no slice"""
    result = service._expand_node_string("dgx[0:2]cpu[0:2]port")
    assert result == [
        "dgx.0.cpu.0.port",
        "dgx.0.cpu.1.port",
        "dgx.1.cpu.0.port",
        "dgx.1.cpu.1.port",
    ]


def test_device_two_components_all_slices(service):
    """device[]component[]component[] — all three levels have slices"""
    result = service._expand_node_string("dgx[0:2]cpu[0:2]port[0:3]")
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
    result = service._expand_node_string("")
    assert result == []


if __name__ == "__main__":
    pytest.main(["-s", __file__])
