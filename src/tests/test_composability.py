from infragraph import *
from infragraph.blueprints.devices.nvidia.dgx import NvidiaDGX
from infragraph.blueprints.devices.nvidia.cx5 import Cx5
from infragraph.blueprints.devices.common.transceiver.qsfp import QSFP
from infragraph.infragraph_service import InfraGraphService
import networkx
# pyright: reportArgumentType=false
import pytest

# Only DGX 
DGX_PROFILES = [
    "dgx1",
    "dgx2",
    "dgx_a100",
    "dgx_h100",
    # "dgx_gh200",
    "dgx_gb200",
]

CX5_VARIANTS = [
    "cx5_25g_dual",
    "cx5_50g_dual",
    "cx5_100g_dual",
    "cx5_100g_single",
]

QSFP_VARIANTS = [
    "qsfp_plus_40g",
    "qsfp28_100g",
    "qsfp56_200g",
    "qsfp_dd_400g",
    "qsfp_dd_800g",
]
@pytest.mark.parametrize("dgx_profile", DGX_PROFILES)
def test_dgx(dgx_profile):
    device = NvidiaDGX(dgx_profile)
    infrastructure = Api().infrastructure()
    infrastructure.devices.append(device)
    infrastructure.instances.add(name=device.name, device=device.name, count=1)
    service = InfraGraphService()
    service.set_graph(infrastructure)
    g = service.get_networkx_graph()
    for node, attrs in g.nodes(data=True):
        assert attrs, f"Node {node} has empty attributes"

    for u, v, attrs in g.edges(data=True):
        assert attrs, f"Edge ({u}, {v}) has empty attributes"
    # print(f"\nInfrastructure is a {g}")
    # print(networkx.write_network_text(g, vertical_chains=True))

@pytest.mark.parametrize("dgx_profile", DGX_PROFILES)
@pytest.mark.parametrize("cx5_variant", CX5_VARIANTS)
def test_dgx_with_cx5_str(dgx_profile, cx5_variant):
    device = NvidiaDGX(dgx_profile, cx5_variant)
    infrastructure = Api().infrastructure()
    infrastructure.devices.append(device)
    infrastructure.instances.add(name=device.name, device=device.name, count=1)
    service = InfraGraphService()
    service.set_graph(infrastructure)
    g = service.get_networkx_graph()
    for node, attrs in g.nodes(data=True):
        assert attrs, f"Node {node} has empty attributes"

    for u, v, attrs in g.edges(data=True):
        assert attrs, f"Edge ({u}, {v}) has empty attributes"
    # print(f"\nInfrastructure is a {g}")
    # print(networkx.write_network_text(g, vertical_chains=True))

@pytest.mark.parametrize("dgx_profile", DGX_PROFILES)
@pytest.mark.parametrize("cx5_variant", CX5_VARIANTS)
def test_dgx_with_cx5_obj(dgx_profile, cx5_variant):
    cx5 = Cx5(variant=cx5_variant)
    device = NvidiaDGX(dgx_profile, cx5)
    infrastructure = Api().infrastructure()
    infrastructure.devices.append(device).append(cx5)
    infrastructure.instances.add(name=device.name, device=device.name, count=1)
    service = InfraGraphService()
    service.set_graph(infrastructure)
    g = service.get_networkx_graph()
    for node, attrs in g.nodes(data=True):
        assert attrs, f"Node {node} has empty attributes"

    for u, v, attrs in g.edges(data=True):
        assert attrs, f"Edge ({u}, {v}) has empty attributes"
    # print(f"\nInfrastructure is a {g}")
    # print(networkx.write_network_text(g, vertical_chains=True))

@pytest.mark.parametrize("dgx_profile", DGX_PROFILES)
@pytest.mark.parametrize("cx5_variant", CX5_VARIANTS)
@pytest.mark.parametrize("qsfp_variant", QSFP_VARIANTS)
def test_dgx_with_cx5_obj_qsfp_str(dgx_profile, cx5_variant, qsfp_variant):
    cx5 = Cx5(variant=cx5_variant, transceiver=qsfp_variant)
    device = NvidiaDGX(dgx_profile, cx5)
    infrastructure = Api().infrastructure()
    infrastructure.devices.append(device).append(cx5)
    infrastructure.instances.add(name=device.name, device=device.name, count=1)
    service = InfraGraphService()
    service.set_graph(infrastructure)
    g = service.get_networkx_graph()
    for node, attrs in g.nodes(data=True):
        assert attrs, f"Node {node} has empty attributes"

    for u, v, attrs in g.edges(data=True):
        assert attrs, f"Edge ({u}, {v}) has empty attributes"
    # print(f"\nInfrastructure is a {g}")
    # print(networkx.write_network_text(g, vertical_chains=True))

@pytest.mark.parametrize("dgx_profile", DGX_PROFILES)
@pytest.mark.parametrize("cx5_variant", CX5_VARIANTS)
@pytest.mark.parametrize("qsfp_variant", QSFP_VARIANTS)
def test_dgx_with_cx5_obj_qsfp_obj(dgx_profile, cx5_variant, qsfp_variant):
    qsfp = QSFP(qsfp_variant)
    cx5 = Cx5(variant=cx5_variant, transceiver=qsfp)
    device = NvidiaDGX(dgx_profile, cx5)
    infrastructure = Api().infrastructure()
    infrastructure.devices.append(device).append(cx5).append(qsfp)
    infrastructure.instances.add(name=device.name, device=device.name, count=1)
    service = InfraGraphService()
    service.set_graph(infrastructure)
    g = service.get_networkx_graph()
    for node, attrs in g.nodes(data=True):
        assert attrs, f"Node {node} has empty attributes"

    for u, v, attrs in g.edges(data=True):
        assert attrs, f"Edge ({u}, {v}) has empty attributes"
    # print(f"\nInfrastructure is a {g}")
    # print(networkx.write_network_text(g, vertical_chains=True))
