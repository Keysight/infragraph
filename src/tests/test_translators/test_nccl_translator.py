import pytest
import os
import yaml

from infragraph.translators.nccl_translator import NcclParser

@pytest.mark.asyncio
async def test_dgx_a100_nccl():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    mock_file_path = os.path.abspath(
        os.path.join(current_dir, "mock_data", "dgx_a100_nccl_topo.xml")
    )

    nccl_parser = NcclParser(mock_file_path)
    infra_device = nccl_parser.parse(infra_type="infrastructure")
    infra_device_dict = yaml.safe_load(infra_device.serialize("yaml"))

    assert "devices" in infra_device_dict
    device = infra_device_dict["devices"][0]

    assert "components" in device
    assert "edges" in device
    assert "links" in device

    components = device["components"]
    assert len(components) == 6

    cpu = next((c for c in components if c["choice"] == "cpu"), None)
    assert cpu is not None, "No CPU component found"
    assert cpu["count"] == 6

    nvsw = next((c for c in components if c["name"] == "nvsw"), None)
    assert nvsw is not None, "No NVSW component found"
    assert nvsw["count"] == 6

    xpu = next((c for c in components if c["choice"] == "xpu"), None)
    assert xpu is not None, "No XPU component found"
    assert xpu["count"] == 8
    assert "A100" in xpu["description"]

    links = device["links"]
    assert len(links) == 3

    link_names = [link["name"] for link in links]
    assert "nvlink" in link_names
    assert "pci" in link_names