import json
import pytest
import yaml
import uuid
import networkx
from infragraph import *
from datetime import datetime
from infragraph.blueprints.fabrics.clos_fat_tree_fabric import ClosFatTreeFabric
from infragraph.blueprints.fabrics.single_tier_fabric import SingleTierFabric
from infragraph.blueprints.devices.nvidia.dgx import NvidiaDGX
from infragraph.blueprints.devices.generic.generic_switch import Switch
from infragraph.blueprints.fabrics.closfabric import ClosFabric
from infragraph.infragraph_service import InfraGraphService
from infragraph.visualizer.visualize import run_visualizer

def print_graph(service):
    g = service.get_networkx_graph()
    # validations

    print("\nAnnotated node attributes:")
    for node, data in g.nodes(data=True):
        print(f"  {node}: {data}")

    print("\nAnnotated edge attributes:")
    for u, v, data in g.edges(data=True):
        print(f"  {u} -- {v}: {data}")

    print("\nAnnotated graph attributes:")
    print(f"  {g.graph}")
    
def visualize_dgx(infrastructure, annotation, output=None):
    """Build the annotated DGX infrastructure and launch the visualizer on it.

    A fresh output folder is generated on every call so repeated runs never
    clobber a prior visualization.
    """
    if output is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"./viz_dgx_{stamp}_{uuid.uuid4().hex[:6]}"

    run_visualizer(infrastructure=infrastructure, annotations=annotation, output=output)

def _annotate_graph(service, **kwargs):
    annotation = Annotation()
    for attr, value in kwargs.items():
        annotation.graph.add(attribute=attr, value=str(value))
    service.annotate_graph(annotation)
    return annotation

def _annotate_node(service, node_name, **kwargs):
    annotation = Annotation()
    node_annotation = annotation.nodes.add(name=node_name)
    for attr, value in kwargs.items():
        node_annotation.attributes.add(attribute=attr, value=str(value))
    service.annotate_graph(annotation)
    return annotation

def _annotate_edge(service, ep1, ep2, **kwargs):
    annotation = Annotation()
    edge_annotation = annotation.edges.add(ep1=ep1, ep2=ep2)
    for attr, value in kwargs.items():
        edge_annotation.attributes.add(attribute=attr, value=str(value))
    service.annotate_graph(annotation)
    return annotation

def _annotate_topology(service):
    _annotate_graph(service, fabric="Single Tier Topology", hosts=["dgx_h100[0]", "dgx_h100[1]"], region="us-east")
    # annotate nodes here - the devices
    _annotate_node(service, node_name="dgx_h100[0]", location="rack 0")
    _annotate_node(service, node_name="dgx_h100[1]", location="rack 8")
    # switch asic name
    _annotate_node(service, node_name="switch[0]asic[0]", vendor="intel tofino")

    # add device type?
    _annotate_node(service, node_name="switch", device_type="switch")
    _annotate_node(service, node_name="dgx_h100", device_type="host")

    # set ranks?
    for i in range(0, 16):
        dev_index = 0 if i < 8 else 1
        comp_index = i % 8
        _annotate_node(service, node_name=f"dgx_h100[{str(dev_index)}]xpu[{str(comp_index)}]", rank=str(i))
    
    # set dgx 0 cx7 annotation to smart cx7
    _annotate_node(service, node_name="dgx_h100[0]cx7", cx7_type="smart cx7")

    # set dgx 1 cpu annotation to hyperthreaded
    _annotate_node(service, node_name="dgx_h100[1]cpu", cpu_type="hyper threaded RISC")

    # add annotation of nvlink to both edges
    _annotate_edge(service, ep1="dgx_h100[0]xpu", ep2="dgx_h100[0]nvsw", latency="0.01", link_type="nvlink", error_rate="6")

    _annotate_edge(service, ep1="dgx_h100[1]xpu", ep2="dgx_h100[1]nvsw", latency="0.08", link_type="nvlink", error_rate="20")

@pytest.fixture
def service():
    dgx = NvidiaDGX()
    clos_fat_tree = SingleTierFabric(dgx, 2)
    svc = InfraGraphService()
    svc.set_graph(clos_fat_tree)
    _annotate_topology(svc)
    return svc

def test_node_filter_attribute_query(service):
    query = QueryRequest()
    query.filters.node_filters.attribute_filters.attributes.add(attribute="cpu_type", value="hyper threaded")
    query_response = service.query_graph(query)
    assert len(query_response.nodes) == 2
    assert "dgx_h100.1.cpu." in query_response.nodes[0].name
    assert len(query_response.edges) == 0
    assert len(query_response.graph) == 0

def test_query_node_attribute(service):
    # get all smart nics
    query = QueryRequest()
    query.filters.node_filters.node_identifier = ["dgx_h100"]
    query.filters.node_filters.attribute_filters.attributes.add(attribute="cx7_type", value="smart")
    query_response = service.query_graph(query)
    assert len(query_response.nodes) == 8
    assert "dgx_h100" in query_response.nodes[0].name
    assert len(query_response.edges) == 0
    assert len(query_response.graph) == 0


def test_query_rank_node_attribute(service):
    # get all smart nics
    query = QueryRequest()
    query.filters.node_filters.attribute_filters.attributes.add(attribute="rank", value="")
    query_response = service.query_graph(query)
    assert len(query_response.nodes) == 16
    assert "xpu" in query_response.nodes[0].name
    assert len(query_response.edges) == 0
    assert len(query_response.graph) == 0
    # print_graph(service)
    # visualize_dgx(service.infrastructure, None, "clos_visual")

def test_query_nic_node_attribute(service):
    # get all smart nics
    query = QueryRequest()
    query.filters.node_filters.attribute_filters.attributes.add(attribute="type", value="nic")
    query_response = service.query_graph(query)
    assert len(query_response.nodes) == 16
    assert "cx7" in query_response.nodes[0].name
    assert len(query_response.edges) == 0
    assert len(query_response.graph) == 0

    # get specific smart nics
    query = QueryRequest()
    query.filters.node_filters.node_identifier = ["dgx_h100[1]"]
    query.filters.node_filters.attribute_filters.attributes.add(attribute="type", value="nic")
    query_response = service.query_graph(query)
    assert len(query_response.nodes) == 8
    assert "cx7" in query_response.nodes[0].name
    assert len(query_response.edges) == 0
    assert len(query_response.graph) == 0
    # print_graph(service)
    # visualize_dgx(service.infrastructure, None, "clos_visual")

def test_query_graph_attribute(service):
    # get all smart nics
    query = QueryRequest()
    query.filters.graph_filter.attributes.add(attribute="region", value="us-east")
    query_response = service.query_graph(query)
    assert len(query_response.graph) > 0
    assert len(query_response.edges) == 0
    assert len(query_response.nodes) == 0


if __name__ == "__main__":
    pytest.main(["-s", __file__])
