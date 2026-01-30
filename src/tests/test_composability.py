from infragraph import *
from infragraph.blueprints.devices.nvidia.dgx import NvidiaDGX
from infragraph.blueprints.devices.nvidia.cx5 import Cx5
from infragraph.blueprints.devices.common.transceiver.qsfp import QSFP
from infragraph.infragraph_service import InfraGraphService
# pyright: reportArgumentType=false
from pyvis.network import Network



class CQSFP(Device):

    def __init__(self):

        super(Device, self).__init__()
        self.name = "qsfp"
        self.description = "QSFP28"

        # components
        electrical_port = self.components.add(
            name="electrical_port",
            description="electrical_port",
            count=1,
        )
        electrical_port.choice = Component.PORT

        optical_port = self.components.add(
            name="optical_port",
            description="optical_port",
            count=1,
        )
        optical_port.choice = Component.PORT

        # links
        internal_binding = self.links.add(name="internal_binding")

        # PORT to PORT
        edge = self.edges.add(scheme=DeviceEdge.ONE2ONE, link=internal_binding.name)
        edge.ep1.component = f"{electrical_port.name}"
        edge.ep2.component = f"{optical_port.name}"
        self.edges.append(edge)


class CCx5(Device):
    NETWORK_PORTS: int = 2

    def __init__(self):

        super(Device, self).__init__()
        self.name = "cx5"
        self.description = "Mellanox ConnectX-5"
        # components
        pcie_endpoint = self.components.add(
            name="pcie_endpoint",
            description="pcie endpoint",
            count=1,
        )
        pcie_endpoint.choice = Component.CUSTOM
        pcie_endpoint.custom.type = "pcie_endpoint"

        dpu = self.components.add(
            name="dpu",
            description="Offload network processor chip",
            count=1,
        )
        dpu.choice = Component.CPU

        switch = self.components.add(
            name="switch",
            description="Switch",
            count=1,
        )
        switch.choice = Component.SWITCH

        port = self.components.add(
            name="port",
            description="The network port on the ConnectX-5 card",
            count=2,
        )
        port.choice = Component.PORT

        qsfp = CQSFP()
        # adding device in device
        qsfp_comp = self.components.add(
            name=qsfp.name,
            description="qsfp connectors",
            count=2,
        )
        qsfp_comp.choice = Component.DEVICE
    
        # links
        pcie = self.links.add(name="pcie")
        dpu_to_switch = self.links.add(name="dpu_to_switch")
        switch_to_port = self.links.add(name="switch_to_port")
        ic = self.links.add(name="ic")

        # PCIE to DPU
        edge = self.edges.add(scheme=DeviceEdge.ONE2ONE, link=pcie.name)
        edge.ep1.component = f"{dpu.name}"
        edge.ep2.component = f"{pcie_endpoint.name}"
        self.edges.append(edge)

        # DPU to SWITCH
        edge = self.edges.add(scheme=DeviceEdge.ONE2ONE, link=dpu_to_switch.name)
        edge.ep1.component = f"{dpu.name}"
        edge.ep2.component = f"{switch.name}"
        self.edges.append(edge)

        # SWITCH to PORT
        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=switch_to_port.name)
        edge.ep1.component = f"{switch.name}"
        edge.ep2.component = f"{port.name}"
        self.edges.append(edge)

        
        # PORT to QSFP
        edge = self.edges.add(scheme=DeviceEdge.ONE2ONE, link=ic.name)
        edge.ep1.component = f"{port.name}[0]"
        edge.ep2.device = f"{qsfp.name}[0]"
        edge.ep2.component = f"electrical_port[0]"
        self.edges.append(edge)

        edge = self.edges.add(scheme=DeviceEdge.ONE2ONE, link=ic.name)
        edge.ep1.component = f"{port.name}[1]"
        edge.ep2.device = f"{qsfp.name}[1]"
        edge.ep2.component = f"electrical_port[0]"
        self.edges.append(edge)

class CDgx(Device):
    def __init__(self, nic_device: Device = None):
        """Adds an InfraGraph device to infrastructure based on the following components:
        - 2 cpus
        - 8 npus
        - 4 pcie switches
        - 8 nics
        - 1 nvlink switch
        """
        super(Device, self).__init__()
        self.name = "dgx"
        self.description = "Nvidia DGX System"

        cpu = self.components.add(
            name="cpu",
            description="AMD Epyc 7742 CPU",
            count=2,
        )
        cpu.choice = Component.CPU
        xpu = self.components.add(
            name="xpu",
            description="Nvidia A100 GPU",
            count=8,
        )
        xpu.choice = Component.XPU
        nvlsw = self.components.add(
            name="nvlsw",
            description="NVLink Switch",
            count=1,
        )
        nvlsw.choice = Component.SWITCH
        pciesw = self.components.add(
            name="pciesw",
            description="PCI Express Switch Gen 4",
            count=4,
        )
        pciesw.choice = Component.SWITCH

        pcie_slot = self.components.add(
            name="pcie_slot",
            description="PCI Express Slot",
            count=8,
        )
        pcie_slot.choice = Component.CUSTOM
        pcie_slot.custom.type = "pcie_slot"

        cpu_fabric = self.links.add(name="fabric", description="AMD Infinity Fabric")
        pcie = self.links.add(name="pcie")
        nvlink = self.links.add(name="nvlink")

        for  cpu_idx in range(cpu.count):
            for idx in range(0, 2):
                edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie.name)
                edge.ep1.component = f"{cpu.name}[{cpu_idx}]"
                edge.ep2.component = f"{pciesw.name}[{cpu_idx * 2 + idx}]"

        for  pciesw_idx in range(pciesw.count):
            for idx in range(0, 2):
                edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie.name)
                edge.ep1.component = f"{pciesw.name}[{pciesw_idx}]"
                edge.ep2.component = f"{pcie_slot.name}[{pciesw_idx * 2 + idx}]"
                
        if nic_device is None:
            nic = self.components.add(
                name="nic",
                description="Generic Nic",
                count=8,
            )
            nic.choice = Component.NIC

            for nic_idx, pciesl_idx in zip(["0:2", "2:4", "4:6", "6:8"], range(pcie_slot.count)):
                edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie.name)
                edge.ep1.component = f"{nic.name}[{nic_idx}]"
                edge.ep2.component = f"{pcie_slot.name}[{pciesl_idx}]"

        else:
            nic = self.components.add(
                name=nic_device.name,
                description=nic_device.description,
                count=8,
            )
            nic.choice = Component.DEVICE
            # get the PCIE_ENDPOINT component
            component_name = "pcie_endpoint"
            # for component in nic_device.components:
            #     if component.type == Component.PCIE_ENDPOINT:
            #         # GET THE COMPONENT

            edge = self.edges.add(scheme=DeviceEdge.ONE2ONE, link=pcie.name)
            edge.ep1.device = f"{nic.name}[0:8]"
            edge.ep1.component = f"{component_name}[0]"
            edge.ep2.component = f"{pcie_slot.name}[0:8]"

            # for  pciesl_idx in range(pcie_slot.count):
            #     edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie.name)
            #     edge.ep1.device = f"{nic.name}[{pciesl_idx}]"
            #     edge.ep1.component = f"{component_name}[0]"
            #     edge.ep2.component = f"{pcie_slot.name}[{pciesl_idx}]"

        

        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=cpu_fabric.name)
        edge.ep1.component = cpu.name
        edge.ep2.component = cpu.name

        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=nvlink.name)
        edge.ep1.component = xpu.name
        edge.ep2.component = nvlsw.name

        for npu_idx, pciesw_idx in zip(["0:2", "2:4", "4:6", "6:8"], range(pciesw.count)):
            edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie.name)
            edge.ep1.component = f"{xpu.name}[{npu_idx}]"
            edge.ep2.component = f"{pciesw.name}[{pciesw_idx}]"

        
def print_graph(graph):
    for node, attrs in graph.nodes(data=True):
        print(f"Node: {node}, Attributes: {attrs}")

    for u, v, attrs in graph.edges(data=True):
        print(f"Edge: ({u}, {v}), Attributes: {attrs}")

def dump_yaml(clos_fabric, filename):
    import yaml
    with open(filename + ".yaml", "w") as file:
        data = clos_fabric.serialize("dict")
        yaml.dump(data, file, default_flow_style=False, indent=4)
    pass

def test_composability():
    qsfp = CQSFP()
    cx5 = CCx5()
    device = CDgx(cx5)
    infrastructure = Api().infrastructure()
    infrastructure.devices.append(device).append(cx5).append(qsfp)
    infrastructure.instances.add(name=device.name, device=device.name, count=2)
    service = InfraGraphService()
    service.set_graph(infrastructure)
    g = service.get_networkx_graph()
    #hierarchical in pyvis
    net = Network(
        height="750px",
        width="100%",
        directed=False,
        select_menu=True,
        filter_menu=True 
    )

    
    net.from_nx(g)

    net.set_options("""
    {
    "layout": {
        "hierarchical": {
        "enabled": true,
        "direction": "UD",
        "sortMethod": "directed",
        "levelSeparation": 150,
        "nodeSpacing": 200
        }
    },
    "physics": {
        "enabled": false
    }
    }
    """)
    net.write_html("dgx_1.html")

    dump_yaml(infrastructure, "infrastructure_compose")
    # print_graph(g)


def test_dgx_composability():
    qsfp = QSFP("qsfp28_100g")
    cx5 = Cx5("cx5_100g_dual", qsfp)
    device = NvidiaDGX("dgx_h100", cx5)
    infrastructure = Api().infrastructure()
    infrastructure.devices.append(device).append(cx5).append(qsfp)
    infrastructure.instances.add(name=device.name, device=device.name, count=2)
    service = InfraGraphService()
    service.set_graph(infrastructure)
    g = service.get_networkx_graph()
    #hierarchical in pyvis
    net = Network(
        height="750px",
        width="100%",
        directed=False,
        select_menu=True,
        filter_menu=True 
    )

    
    net.from_nx(g)

    net.set_options("""
    {
    "layout": {
        "hierarchical": {
        "enabled": true,
        "direction": "UD",
        "sortMethod": "directed",
        "levelSeparation": 150,
        "nodeSpacing": 200
        }
    },
    "physics": {
        "enabled": false
    }
    }
    """)
    net.write_html("dgx_1.html")

    dump_yaml(infrastructure, "infrastructure_compose")
    print_graph(g)