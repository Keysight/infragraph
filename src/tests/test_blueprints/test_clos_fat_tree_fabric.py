import pytest
import networkx
from infragraph.infragraph_service import InfraGraphService
from infragraph.blueprints.fabrics.clos_fat_tree_fabric import ClosFatTreeFabric
from infragraph.blueprints.devices.nvidia.dgx import Dgx
from infragraph.blueprints.devices.generic.server import Server
from infragraph.blueprints.devices.generic.generic_switch import Switch

def print_graph(graph):
    for node, attrs in graph.nodes(data=True):
        print(f"Node: {node}, Attributes: {attrs}")

    for u, v, attrs in graph.edges(data=True):
        print(f"Edge: ({u}, {v}), Attributes: {attrs}")

def dump_yaml(clos_fabric, filename):
    # import yaml
    # with open(filename + ".yaml", "w") as file:
    #     data = clos_fabric.serialize("dict")
    #     yaml.dump(data, file, default_flow_style=False, indent=4)
    pass

@pytest.mark.asyncio
async def test_2_tier_16_radix_with_dgx():
    """
    Generate two tier clos fabric with switch radix 16 and dgx hosts
    """
    dgx = Dgx()
    switch = Switch(port_count=16)
    clos_fat_tree = ClosFatTreeFabric(switch, dgx, 2, [])
    # create the graph
    assert len(clos_fat_tree.instances) == 3
    for instance in clos_fat_tree.instances:
        if instance.name == "tier_0":
            assert instance.count == 16
        elif instance.name == "tier_1":
            assert instance.count == 8
    service = InfraGraphService()
    service.set_graph(clos_fat_tree)

    # validations
    g = service.get_networkx_graph()
    print(networkx.write_network_text(g, vertical_chains=True))
    print_graph(g)

@pytest.mark.asyncio
async def test_2_tier_8_radix_with_server():
    """
    Generate two tier clos fabric with generic server as hosts
    """
    server = Server()
    switch = Switch(port_count=8)
    clos_fat_tree = ClosFatTreeFabric(switch, server, 2, [])

    assert len(clos_fat_tree.instances) == 3
    for instance in clos_fat_tree.instances:
        if instance.name == "tier_0":
            assert instance.count == 8
        elif instance.name == "tier_1":
            assert instance.count == 4
    dump_yaml(clos_fat_tree, "test_2_tier_8_radix_with_server")
    # create the graph
    service = InfraGraphService()
    service.set_graph(clos_fat_tree)

    # validations
    g = service.get_networkx_graph()
    print(networkx.write_network_text(g, vertical_chains=True))
    print_graph(g)

@pytest.mark.asyncio
async def test_3_tier_4_radix_with_server():
    """
    Generate three tier clos fabric with generic server as hosts
    """
    server = Server()
    switch = Switch(port_count=4)
    clos_fat_tree = ClosFatTreeFabric(switch, server, 3, [])

    assert len(clos_fat_tree.instances) == 4
    for instance in clos_fat_tree.instances:
        if instance.name == "tier_0":
            assert instance.count == 8
        elif instance.name == "tier_1":
            assert instance.count == 8
        elif instance.name == "tier_2":
            assert instance.count == 4

    dump_yaml(clos_fat_tree, "test_3_tier_4_radix_with_server")
    # create the graph    
    service = InfraGraphService()
    service.set_graph(clos_fat_tree)

    # validations
    g = service.get_networkx_graph()
    print(networkx.write_network_text(g, vertical_chains=True))
    print_graph(g)

@pytest.mark.asyncio
async def test_3_tier_no_oversub_4_radix_with_server():
    """
    Generate a 3 tier fabric with server as host
    """
    server = Server()
    switch = Switch(port_count=4)
    clos_fat_tree = ClosFatTreeFabric(switch, server, 3, [100, 100, 100])
    
    assert len(clos_fat_tree.instances) == 4
    for instance in clos_fat_tree.instances:
        if instance.name == "tier_0":
            assert instance.count == 8
        elif instance.name == "tier_1":
            assert instance.count == 8
        elif instance.name == "tier_2":
            assert instance.count == 4

    dump_yaml(clos_fat_tree, "test_3_tier_no_oversub_4_radix_with_server")
    # create the graph
    service = InfraGraphService()
    service.set_graph(clos_fat_tree)

    # validations
    g = service.get_networkx_graph()
    print(networkx.write_network_text(g, vertical_chains=True))
    print_graph(g)

@pytest.mark.asyncio
async def test_3_tier_no_oversub_8_radix_with_server():
    """
    Generate a 3 tier fabric switch radix 8 and server as host
    """
    server = Server()
    switch = Switch(port_count=8)
    clos_fat_tree = ClosFatTreeFabric(switch, server, 3, [100, 100, 100])
    assert len(clos_fat_tree.instances) == 4
    for instance in clos_fat_tree.instances:
        if instance.name == "tier_0":
            assert instance.count == 32
        elif instance.name == "tier_1":
            assert instance.count == 32
        elif instance.name == "tier_2":
            assert instance.count == 16
        elif instance.name == "dgx":
            assert instance.count == 64

    dump_yaml(clos_fat_tree, "test_3_tier_no_oversub_8_radix_with_server")
    # create the graph
    service = InfraGraphService()
    service.set_graph(clos_fat_tree)

    # validations
    g = service.get_networkx_graph()
    print(networkx.write_network_text(g, vertical_chains=True))
    print_graph(g)


@pytest.mark.asyncio
async def test_2_tier_32_radix_with_dgx():
    """
    Generate a 2 tier fabric with dgx hosts and switch radix as 32
    """
    dgx = Dgx()
    switch = Switch(port_count=32)
    clos_fat_tree = ClosFatTreeFabric(switch, dgx, 2, [])
    assert len(clos_fat_tree.instances) == 3
    for instance in clos_fat_tree.instances:
        if instance.name == "tier_0":
            assert instance.count == 32
        elif instance.name == "tier_1":
            assert instance.count == 16
        elif instance.name == "dgx":
            assert instance.count == 64

    dump_yaml(clos_fat_tree, "test_2_tier_32_radix_with_dgx")
    # create the graph
    service = InfraGraphService()
    service.set_graph(clos_fat_tree)

    # validations
    g = service.get_networkx_graph()
    print(networkx.write_network_text(g, vertical_chains=True))
    print_graph(g)

@pytest.mark.asyncio
async def test_3_tier_32_radix_with_dgx():
    """
    Generate a 2 tier fabric with dgx hosts and switch radix as 32
    """
    dgx = Dgx()
    switch = Switch(port_count=32)
    clos_fat_tree = ClosFatTreeFabric(switch, dgx, 3, [])
    assert len(clos_fat_tree.instances) == 4
    for instance in clos_fat_tree.instances:
        if instance.name == "tier_0":
            assert instance.count == 512
        elif instance.name == "tier_1":
            assert instance.count == 512
        elif instance.name == "tier_2":
            assert instance.count == 256
        elif instance.name == "dgx":
            assert instance.count == 1024

    dump_yaml(clos_fat_tree, "test_3_tier_32_radix_with_dgx")
    # create the graph
    service = InfraGraphService()
    service.set_graph(clos_fat_tree)

    # validations
    g = service.get_networkx_graph()
    print(networkx.write_network_text(g, vertical_chains=True))
    print_graph(g)

if __name__ == "__main__":
    pytest.main(["-s", __file__])
