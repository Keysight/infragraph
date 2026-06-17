import pytest
import os
import json
import yaml
from infragraph.blueprints.fabrics.clos_fat_tree_fabric import ClosFatTreeFabric
from infragraph.blueprints.devices.generic.server import Server
from infragraph.blueprints.devices.generic.generic_switch import Switch
from infragraph.blueprints.devices.nvidia.dgx import NvidiaDGX
from infragraph.blueprints.devices.nvidia.cx5 import Cx5
from infragraph.blueprints.devices.common.transceiver.qsfp import QSFP
from infragraph.infragraph_service import InfraGraphService
from infragraph.infragraph import *
from infragraph.visualizer.visualize import run_visualizer


def _load_graph_data(output_dir):
    """
    Helper function to assert if the generated graph_data.js has correct number of nodes and edges.
    - Splits the generated json into
        nodes and edges of instances and components
    """
    js_path = os.path.join(output_dir, "js", "graph_data.js")
    with open(js_path, "r") as f:
        content = f.read()
    json_str = content.split("const GRAPH_DATA = ")[1].split(";\n")[0]
    return json.loads(json_str)


@pytest.mark.asyncio
async def test_visualizer_closfabric(tmp_path):
    """
    Test visualizer with a clos fabric infrastructure object directly.
    """
    server = Server()
    switch = Switch(port_count=4)
    clos_fat_tree = ClosFatTreeFabric(switch, server, 3, [])

    output_dir = str(tmp_path / "viz1")
    run_visualizer(infrastructure=clos_fat_tree, hosts="server", switches="switch", output=output_dir)

    assert os.path.exists(os.path.join(output_dir, "index.html")), "HTML file not copied"
    assert os.path.exists(os.path.join(output_dir, "js", "graph_data.js")), "graph_data.js not generated"
    assert os.path.exists(os.path.join(output_dir, "css", "style.css")), "CSS file not copied"

    data = _load_graph_data(output_dir)
    infra_nodes = data["infrastructure.json"]["nodes"]
    infra_edges = data["infrastructure.json"]["edges"]
    assert len(infra_nodes) == 28, "Infrastructure should have 28 total nodes"
    assert len(infra_edges) > 0, "Infrastructure should have edges"


@pytest.mark.asyncio
async def test_composed_devices(tmp_path):
    """
    Test visualizer with composed devices (DGX + CX5) via YAML input.
    """
    cx5 = Cx5(variant="cx5_100g_dual")
    device = NvidiaDGX("dgx_a100", cx5)
    infrastructure = Api().infrastructure()
    infrastructure.devices.append(device).append(cx5)
    infrastructure.instances.add(name=device.name, device=device.name, count=1)

    # dump to yaml
    yaml_path = str(tmp_path / "composed_devices.yaml")
    data = infrastructure.serialize("dict")
    with open(yaml_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, indent=4)

    output_dir = str(tmp_path / "viz2")
    run_visualizer(input_file=yaml_path, hosts="dgx_a100, cx5_100gbe", switches="", output=output_dir)

    assert os.path.exists(os.path.join(output_dir, "index.html")), "HTML file not copied"
    assert os.path.exists(os.path.join(output_dir, "js", "graph_data.js")), "graph_data.js not generated"
    assert os.path.exists(os.path.join(output_dir, "css", "style.css")), "CSS file not copied"

    data = _load_graph_data(output_dir)
    dgx_nodes = data["dgx_a100.json"]["nodes"]
    dgx_edges = data["dgx_a100.json"]["edges"]
    cx5_nodes = data["cx5_100gbe.json"]["nodes"]
    cx5_edges = data["cx5_100gbe.json"]["edges"]
    assert len(dgx_nodes) == 37, "DGX should have 37 component nodes"
    assert len(dgx_edges) > 0, "DGX should have internal edges"
    assert len(cx5_nodes) == 4, "cx5_100gbe should have 4 nodes"
    assert len(cx5_edges) > 0, "cx5_100gbe should have edges"


@pytest.mark.asyncio
async def test_json_file(tmp_path):
    """
    Test visualizer with DGX + CX5 + QSFP via JSON input.
    """
    qsfp = QSFP("qsfp_dd_400g")
    cx5 = Cx5(variant="cx5_100g_dual", transceiver=qsfp)
    device = NvidiaDGX("dgx_a100", cx5)
    infrastructure = Api().infrastructure()
    infrastructure.devices.append(device).append(cx5).append(qsfp)
    infrastructure.instances.add(name=device.name, device=device.name, count=1)

    service = InfraGraphService()
    service.set_graph(infrastructure)
    service.get_networkx_graph()

    #dump to json
    json_path = str(tmp_path / "infra.json")
    data = infrastructure.serialize("dict")
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)

    output_dir = str(tmp_path / "viz3")
    run_visualizer(input_file=json_path, hosts="dgx_a100, cx5_100g_dual, qsfp_dd_400g", switches="", output=output_dir)

    assert os.path.exists(os.path.join(output_dir, "index.html")), "HTML file not copied"
    assert os.path.exists(os.path.join(output_dir, "js", "graph_data.js")), "graph_data.js not generated"
    assert os.path.exists(os.path.join(output_dir, "css", "style.css")), "CSS file not copied"

    data = _load_graph_data(output_dir)
    assert len(data) > 1, "Should have infrastructure and at least one device view"


if __name__ == "__main__":
    pytest.main(["-s", __file__])