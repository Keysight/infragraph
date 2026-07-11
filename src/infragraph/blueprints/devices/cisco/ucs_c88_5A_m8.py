from infragraph.infragraph import *
from typing import Optional, Union

XpuType=Literal["hgx_h100","hgx_h200","mi300x","mi350x"]

class cisco_ucsc_885A_m8(Device):
    def __init__(self, xpu_type: XpuType= "hgx_h100", storage_count: int=16, ns_nic_count: int=2, ew_nic_count: int=2):
        super(Device, self).__init__()
        self.name = "ucsc_885A_m8"
        self.description = "Cisco UCS C885A M8 Rack Server"

        XPU_CATALOG = {
            "hgx_h100":{
                "description": "NVIDIA HGX H100 SXM",
                "fabric": "nvlink_4",
                "count": 8,
                "nvswitch_count": 4,
            },
            "hgx_h200": {
                "description": "NVIDIA HGX H200 SXM",
                "fabric": "nvlink_4",
                "count": 8,
                "nvswitch_count": 4,
            },
            "mi300x": {
                "description": "AMD MI300X OAM",
                "fabric": "Infinity_fabric",
                "count": 8,
                "nvswitch_count": 0,
            },
            "mi350x":{
                "description": "AMD MI350X OAM",
                "fabric": "Infinity_fabric",
                "count": 8,
                "nvswitch_count": 0,
            }
        }

        xpu_cfg= XPU_CATALOG[xpu_type]

        cpu = self.components.add(
            name="cpu",
            description="AMD EPYC 9554/9575F/9535 64 core",
            count=2,
        )
        cpu.choice = Component.CPU

        memory = self.components.add(
            name="memory",
            description="DDR5 RDIMM (24 slots, 64/96/128 GB, up to 6000 MT/s)",
            count=24,
        )
        memory.choice = Component.MEMORY

        xpu= self.components.add(
            name="xpu",
            description=xpu_cfg["description"],
            count=xpu_cfg["count"],
        )
        xpu.choice=Component.XPU

        nvswitch_count = xpu_cfg["nvswitch_count"]
        nvsw = None
        if nvswitch_count > 0:
            nvsw = self.components.add(
                name="nvsw",
                description="NVIDIA NVSwitch",
                count=nvswitch_count,
            )
            nvsw.choice = Component.SWITCH

        storage = self.components.add(
            name="storage",
            description="2.5” U.2 NVMe SSD",
            count=storage_count,
        )
        storage.choice = Component.CUSTOM

        ew_nic =self.components.add(
            name="east_west_nic",
            description="East-West NIC (ConnectX-7 1x400G, BlueField-3 B3140H SuperNIC, or AMD Pensando Pollara 400)",
            count=ew_nic_count,
        )
        ew_nic.choice = Component.NIC

        ns_nic =self.components.add(
            name="north_south_nic",
            description="North-South NIC (ConnectX-7 2x200G or BlueField-3 B3220/B3240)",
            count=ns_nic_count,
        )
        ns_nic.choice = Component.NIC

        ocp = self.components.add(
            name="ocp",
            description="OCP 3.0 Intel X710-T2L 2x10G RJ45 NIC",
            count=1,
        )
        ocp.choice = Component.NIC

        ns_pciesl = self.components.add(
            name="ns_pciesl",
            description="PCIe Gen5 x16 FHHL slots for North-South NIC",
            count=5,
        )
        ns_pciesl.choice = Component.CUSTOM
        ns_pciesl.custom.type = "pcie_slot"
 
        ew_pciesl = self.components.add(
            name="ew_pciesl",
            description="PCIe Gen5 x16 HHHL slots for East-West NIC (1 per GPU)",
            count=8,
        )
        ew_pciesl.choice = Component.CUSTOM
        ew_pciesl.custom.type = "pcie_slot"

        #links
        xgmi = self.links.add(name="infinity_fabric", description="AMD xGMI CPU fabric")
        xpu_fabric_name = xpu_cfg["fabric"]
        xpu_link = self.links.add(name=xpu_fabric_name, description=f"{xpu_fabric_name} XPU fabric")
        pci = self.links.add(name="pcie_gen5", description="PCI Express Gen 5.0 x16")
        ddr5 = self.links.add(name="ddr5", description="DDR5 up to 6000 MT/s")

        #CPU
        edge = self.edges.add(DeviceEdge.MANY2MANY, link=xgmi.name)
        edge.ep1.component = f"{cpu.name}"
        edge.ep2.component = f"{cpu.name}"
 
        #CPU to GPUs 
        gpus_per_cpu = xpu.count // cpu.count
        for cpu_index in range(cpu.count):
            e = self.edges.add(DeviceEdge.MANY2MANY, link=pci.name)
            e.ep1.component = f"{cpu.name}[{cpu_index}]"
            e.ep2.component = f"{xpu.name}[{cpu_index * gpus_per_cpu}:{cpu_index * gpus_per_cpu + gpus_per_cpu}]"
 
        #CPU to NS PCIe slots 
        cpu_to_ns_pciesl = {0: [0, 1, 2],
                            1: [3, 4]}
        for cpu_index, slots in cpu_to_ns_pciesl.items():
            e = self.edges.add(DeviceEdge.MANY2MANY, link=pci.name)
            e.ep1.component = f"{cpu.name}[{cpu_index}]"
            e.ep2.component = f"{ns_pciesl.name}[{slots[0]}:{slots[-1] + 1}]"
 
        #CPU to EW PCIe slots 
        ew_per_cpu = ew_pciesl.count // cpu.count
        for cpu_index in range(cpu.count):
            e = self.edges.add(DeviceEdge.MANY2MANY, link=pci.name)
            e.ep1.component = f"{cpu.name}[{cpu_index}]"
            e.ep2.component = f"{ew_pciesl.name}[{cpu_index * ew_per_cpu}:{cpu_index * ew_per_cpu + ew_per_cpu}]"
 
        #Storage:
        drives_per_cpu = storage.count // cpu.count
        for cpu_index in range(cpu.count):
            e = self.edges.add(DeviceEdge.MANY2MANY, link=pci.name)
            e.ep1.component = f"{cpu.name}[{cpu_index}]"
            e.ep2.component = f"{storage.name}[{cpu_index * drives_per_cpu}:{cpu_index * drives_per_cpu + drives_per_cpu}]"
  
        #XPU fabric
        if xpu_fabric_name == "nvlink_4":
            e = self.edges.add(DeviceEdge.MANY2MANY, link=xpu_link.name)
            e.ep1.component = f"{xpu.name}[0:{xpu.count}]"
            e.ep2.component = f"{nvsw.name}[0:{nvswitch_count}]"
        elif xpu_fabric_name == "infinity_fabric":
            e = self.edges.add(DeviceEdge.MANY2MANY, link=xpu_link.name)
            e.ep1.component = f"{xpu.name}[0:{xpu.count}]"
            e.ep2.component = f"{xpu.name}[0:{xpu.count}]"
 
        #Memory
        dimms_per_cpu = memory.count // cpu.count
        for cpu_index in range(cpu.count):
            start = cpu_index * dimms_per_cpu
            e = self.edges.add(DeviceEdge.MANY2MANY, link=ddr5.name)
            e.ep1.component = f"{cpu.name}[{cpu_index}]"
            e.ep2.component = f"{memory.name}[{start}:{start + dimms_per_cpu}]"
 
        #NIC - East-West NICs plug into EW slots (1:1)
        if ew_nic is not None:
            for nic_index in range(ew_nic.count):
                e = self.edges.add(DeviceEdge.ONE2ONE, link=pci.name)
                e.ep1.component = f"{ew_pciesl.name}[{nic_index}]"
                e.ep2.component = f"{ew_nic.name}[{nic_index}]"
 
        #NIC - North-South NICs plug into NS slots (1:1 starting at slot 0)
        for nic_index in range(ns_nic.count):
            e = self.edges.add(DeviceEdge.ONE2ONE, link=pci.name)
            e.ep1.component = f"{ns_pciesl.name}[{nic_index}]"
            e.ep2.component = f"{ns_nic.name}[{nic_index}]"
 
        #NIC - OCP
        e = self.edges.add(DeviceEdge.ONE2ONE, link=pci.name)
        e.ep1.component = f"{cpu.name}[0]"
        e.ep2.component = f"{ocp.name}[0]"

        


if __name__ == "__main__":
    device = cisco_ucsc_885A_m8()
    print(device.serialize(encoding=Device.YAML))