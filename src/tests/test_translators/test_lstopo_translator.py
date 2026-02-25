import pytest
import os
import yaml

from infragraph.translators.lstopo_translator import LstopoParser

@pytest.mark.asyncio
async def test_supermicro_hyper_221H():
    current_dir = os.getcwd()
    mock_data_path = os.path.join(current_dir, "mock_data")
    mock_file_path = os.path.join(mock_data_path, "supermicro.xml")
    lstopo_parser = LstopoParser(mock_file_path)

    infra_device = lstopo_parser.parse()
    infra_device_serialized = infra_device.serialize("yaml")
    infra_device_dict = yaml.safe_load(infra_device_serialized)


    assert "components" in infra_device_dict
    assert "edges" in infra_device_dict
    assert "links" in infra_device_dict
    assert "name" in infra_device_dict

    assert infra_device_dict["name"] == "SYS-221H-TNR"

    components = infra_device_dict["components"]
    assert len(components) == 8

    cpu = next(c for c in components if c["choice"] == "cpu")
    assert cpu["count"] == 2

    root_bridge = next(c for c in components if c["name"] == "root_bridge")
    assert root_bridge["count"] == 4

    links = infra_device_dict["links"]
    assert len(links) == 2


@pytest.mark.asyncio
async def test_nvidia_dgx_2h():
    current_dir = os.getcwd()
    mock_data_path = os.path.join(current_dir, "mock_data")
    mock_file_path = os.path.join(mock_data_path, "NVIDIA-DGX2H-2pa24co+16nvml+1nvswitch+10ib.xml")
    lstopo_parser = LstopoParser(mock_file_path)

    infra_device = lstopo_parser.parse()
    infra_device_serialized = infra_device.serialize("yaml")
    infra_device_dict = yaml.safe_load(infra_device_serialized)


    assert "components" in infra_device_dict
    assert "edges" in infra_device_dict
    assert "links" in infra_device_dict
    assert "name" in infra_device_dict

    assert infra_device_dict["name"] == "NVIDIA DGX-2H"

    components = infra_device_dict["components"]
    assert len(components) == 8

    cpu = next(c for c in components if c["choice"] == "cpu")
    assert cpu["count"] == 2

    gpu = next(
        c for c in components
        if c["name"] == "Tesla V100-SXM3-32GB-H"
    )
    assert gpu["count"] == 16

    root_bridge = next(c for c in components if c["name"] == "root_bridge")
    assert root_bridge["count"] == 8

    links = infra_device_dict["links"]
    assert len(links) == 2


    

