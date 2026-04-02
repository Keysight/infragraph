import pytest
import os
import json
from infragraph.blueprints.fabrics.clos_fat_tree_fabric import ClosFatTreeFabric
from infragraph.blueprints.devices.generic.server import Server
from infragraph.blueprints.devices.generic.generic_switch import Switch
from infragraph.visualizer.visualize import run_visualizer


def _load_graph_data(output_dir):
    """
    Load and parse graph_data.js content.
    """
    js_path = os.path.join(output_dir, "js", "graph_data.js")
    with open(js_path, "r") as f:
        content = f.read()
    json_str = content.split("const GRAPH_DATA = ")[1].split(";\n")[0]      #infrastructure.json { nodes: [...], edges: [...]}
    return json.loads(json_str)


@pytest.mark.asyncio
async def test_closfabric_3tier_4radix():
    """
    Generate two tier clos fabric with switch radix 16 and dgx hosts
    """
    server = Server()
    switch = Switch(port_count=4)
    clos_fat_tree = ClosFatTreeFabric(switch, server, 3, [])
    output_dir="./viz1"
    run_visualizer(infrastructure=clos_fat_tree,hosts="server", switches="switch",output=output_dir)
    assert os.path.exists(os.path.join(output_dir, "index.html")), "HTML file not copied"
    assert os.path.exists(os.path.join(output_dir, "js", "graph_data.js")), "graph_data.js not generated"
    assert os.path.exists(os.path.join(output_dir,"css","style.css")), "CSS file not copied"

    data = _load_graph_data(output_dir)
    infra_nodes = data["infrastructure.json"]["nodes"]
    infra_edges = data["infrastructure.json"]["edges"]
    assert len(infra_nodes) == 28 , "Infrastructure should have 28 total nodes"
    assert len(infra_edges) > 0, "Infrastructure should have edges"

@pytest.mark.asyncio
async def test_composed_devices():
    """
    Test dgx with cx5_100gbe 
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    mock_data_path = os.path.join(current_dir, "mock_data")
    infra_yaml_path = os.path.join(mock_data_path, "dgx_a100", "infra.yaml")
    output_dir="./viz2"
    run_visualizer(infra_yaml_path,hosts="dgx_a100,cx5_100gbe", output=output_dir)
    assert os.path.exists(os.path.join(output_dir, "index.html")), "HTML file not copied"
    assert os.path.exists(os.path.join(output_dir, "js", "graph_data.js")), "graph_data.js not generated"
    assert os.path.exists(os.path.join(output_dir,"css","style.css")), "CSS file not copied"

    data = _load_graph_data(output_dir)
    dgx_nodes = data["dgx_a100.json"]["nodes"]
    dgx_edges = data["dgx_a100.json"]["edges"]
    cx5_nodes=data["cx5_100gbe.json"]["nodes"]
    cx5_edges=data["cx5_100gbe.json"]["edges"]
    assert len(dgx_nodes) == 38, "DGX should have 38 component nodes"
    assert len(dgx_edges) > 0, "DGX should have internal edges"
    assert len(cx5_nodes) == 4 , "cx5_100gbe should have 4 nodes"
    assert len(cx5_edges) > 0, "cx5_100gbe should have edges"

@pytest.mark.asyncio
async def test_json_file():
    """
    Test dgx_a100 with json as input file"
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    mock_data_path = os.path.join(current_dir, "mock_data")
    json_path = os.path.join(mock_data_path, "SYS-221H-TNR.json")
    output_dir="./viz3"
    run_visualizer(json_path,hosts="SYS-221H-TNR",output=output_dir)
    assert os.path.exists(os.path.join(output_dir, "index.html")), "HTML file not copied"
    assert os.path.exists(os.path.join(output_dir, "js", "graph_data.js")), "graph_data.js not generated"
    assert os.path.exists(os.path.join(output_dir,"css","style.css")), "CSS file not copied"

    data = _load_graph_data(output_dir)
    assert len(data) > 1, "Should have infrastructure and at least one device view"



if __name__ == "__main__":
    pytest.main(["-s", __file__])
