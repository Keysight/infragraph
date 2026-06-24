from infragraph.blueprints.fabrics.hybrid_debruijn_fabric import HybridDeBruijnFabric
from infragraph.blueprints.fabrics.clos_fat_tree_fabric import ClosFatTreeFabric
from infragraph.infragraph_service import InfraGraphService
from infragraph.blueprints.devices.generic.generic_switch import Switch
from infragraph.blueprints.devices.generic.server import Server
from infragraph.blueprints.devices.nvidia.dgx import NvidiaDGX


def create_infragraph_topology():
    """creates the infragraph topology"""
    switch = Switch(port_count=16)
    server = Server()
    dgx = NvidiaDGX()
    #return HybridDeBruijnFabric(switch, server, 2)
    return ClosFatTreeFabric(switch, dgx, 2, [])
    

def generate_networkx_graph(infragraph_topology):
    """uses infragraph service to generate networkx graph"""

    service = InfraGraphService()
    service.set_graph(infragraph_topology)

    return service.get_networkx_graph()

def convert_graph_to_mininet_data(graph):
    """creates mininet data"""

    nodes = extract_nodes(graph)
    links = extract_links(graph, nodes)

    hosts = []
    switches = []

    for node in nodes.values():
        if node["type"] == "switch" :
            switches.append(node["mininet_component"])
        else:
            hosts.append(node["mininet_component"])
    
    return{
        "hosts" : sort_mininet_names(hosts),
        "switches" : sort_mininet_names(switches),
        "links" : links
    }

def sort_mininet_names(names):
    return sorted(names, key=lambda name: int(name[1:]))

def extract_nodes(graph):
    """extracts top level device from networkx graph, eg - host.0.nic.0 --- host.0  """

    nodes = {}
    host_number = 1
    switch_number = 1
    
    for graph_node in graph.nodes:
        graph_node = str(graph_node)
        device_id = get_device_id(graph_node)

        if device_id in nodes:
            continue

        node_type = detect_node_type(device_id)
        
        if node_type == "switch":
            mininet_component = mininet_component_name(node_type, switch_number)
            switch_number += 1
        else:
            mininet_component = mininet_component_name(node_type, host_number)
            host_number += 1

        nodes[device_id] = {
            "type": node_type,
            "mininet_component" : mininet_component
        }

    return nodes
    
def extract_links(graph, nodes):
    """extracts links between nodes"""

    links = []

    for endpoint1, endpoint2 in graph.edges:
        device1 = get_device_id(str(endpoint1))
        device2 = get_device_id(str(endpoint2))

        if device1 == device2: #for duplicate device
            continue 

        if device1 not in nodes or device2 not in nodes:
            continue

        mininet_node1 = nodes[device1]["mininet_component"]
        mininet_node2 = nodes[device2]["mininet_component"]

        link = (mininet_node1, mininet_node2)
        reverse_link = (mininet_node2, mininet_node1)

        if link in links or reverse_link in links :
            continue

        links.append(link)

    return links

def get_device_id(endpoint):

    parts = endpoint.split(".")

    if len(parts) < 2:
        return endpoint
    
    return f"{parts[0]}.{parts[1]}"

def detect_node_type(device_id):

    name = device_id.lower()

    if "switch" in name:
        return "switch"
    
    if "leafsw" in name:
        return "switch"
    
    if "spinesw" in name:
        return "switch"
    
    if "sw" in name:
        return "switch"
    
    if "tier" in name:
        return "switch"
    
    
    return "host"

def mininet_component_name(node_type, index):

    if node_type == "switch":
        return f"s{index}"
    
    return f"h{index}"


def print_mininet_data(mininet_data):
    "print mininet network - hosts, switches, links berfore starting mininet"

    print("Hosts: ")
    print(" ".join(mininet_data["hosts"]))

    print("Switches: ")
    print(" ".join(mininet_data["switches"]))

    print("Links:")
    links = [f"({node1},{node2})" for node1, node2 in mininet_data["links"]]
    print(" ".join(links))



def run_mininet(mininet_data):
    """creates the mininet network , starts pingall in the cli"""

    try:
        from mininet.cli import CLI
        from mininet.log import setLogLevel
        from mininet.net import Mininet
        from mininet.node import Controller, OVSSwitch
        from mininet.clean import cleanup
        from time import sleep

    except ImportError as error:
        raise RuntimeError("Mininet is not properly installed") from error
    
    cleanup()
    
    setLogLevel("info")
    net = Mininet(controller=None, switch=OVSSwitch, autoSetMacs=False)
    #net.addController("c0")

    for host in mininet_data["hosts"]:
        net.addHost(host)

    for switch in mininet_data["switches"]:
        net.addSwitch(switch, failMode="standalone", stp=True)

    for node1,node2 in mininet_data["links"]:
        net.addLink(node1, node2)

    try:
        net.start()

        print("waiting for STP ...")
        sleep(10)

        print("Running pingall...")
        net.pingAll()

        print("Opening Mininet CLI...")
        CLI(net)

    finally:
        net.stop()


def simulate_topology():

    infragraph_topology = create_infragraph_topology()
    graph = generate_networkx_graph(infragraph_topology)
    mininet_data = convert_graph_to_mininet_data(graph)
    print_mininet_data(mininet_data)
    run_mininet(mininet_data)

def main():
    
    simulate_topology()



if __name__ == "__main__" :
    main()