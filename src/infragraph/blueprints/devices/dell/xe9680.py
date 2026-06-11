from infragraph.infragraph import *
from typing import Optional, Union, Literal

NicSpec = Union[str, Device]
StorageType = Literal["e3.s", "u.2nvme", "u.2sas/sata"]
XpuType = Literal["h100", "h200", "h20", "a100", "mi300x", "gaudi3"]


class Dellxe9680(Device):
    def __init__(
        self,
        nic_device: Optional[NicSpec] = None,
        storage_type: StorageType = "u.2nvme",
        xpu_type: XpuType = "h200",
    ):
        super(Device, self).__init__()
        self.nic_device = nic_device
        self.name = "xe9680"
        self.description = "Dell PowerEdge XE9680"

        XPU_CATALOG = {
            "h100": {
                "description": "NVIDIA HGX H100 80GB 700W SXM5",
                "fabric": "nvlink_4",
                "count": 8,
                "nvswitch_count": 4,
            },
            "h200": {
                "description": "NVIDIA HGX H200 141GB 700W SXM5",
                "fabric": "nvlink_4",
                "count": 8,
                "nvswitch_count": 4,
            },
            "h20": {
                "description": "NVIDIA HGX H20 96GB 500W SXM5",
                "fabric": "nvlink_4",
                "count": 8,
                "nvswitch_count": 4,
            },
            "a100": {
                "description": "NVIDIA HGX A100 80GB 500W SXM4",
                "fabric": "nvlink_3",
                "count": 8,
                "nvswitch_count": 6,
            },
            "mi300x": {
                "description": "AMD INSTINCT MI300X 192GB 750W OAM",
                "fabric": "infinity_fabric",
                "count": 8,
                "nvswitch_count": 0,
            },
            "gaudi3": {
                "description": "Intel Gaudi3 128GB 900W OAM",
                "fabric": "osfp_link",
                "count": 8,
                "nvswitch_count": 0,
            },
        }

        STORAGE_CATALOG = {
            "e3.s": {
                "description": "Front bays: E3.S EDSFF (PCIe Gen5 x4 via PSB)",
                "count": 16,
                "drives_per_sw": 4,
            },
            "u.2nvme": {
                "description": "Front bays: U.2 NVMe (via PSB)",
                "count": 8,
                "drives_per_sw": 2,
            },
            "u.2sas/sata": {
                "description": "U.2 SAS/SATA (via fPERC)",
                "count": 8,
                "drives_per_sw": 0,
            },
        }

        xpu_cfg = XPU_CATALOG[xpu_type]
        storage_cfg = STORAGE_CATALOG[storage_type]

        cpu = self.components.add(
            name="cpu",
            description="4th or 5th gen Intel Xeon Scalable",
            count=2,
        )
        cpu.choice = Component.CPU

        xpu = self.components.add(
            name="xpu",
            description=xpu_cfg["description"],
            count=xpu_cfg["count"],
        )
        xpu.choice = Component.XPU

        nvswitch_count = xpu_cfg["nvswitch_count"]
        nvsw = None
        if nvswitch_count > 0:
            nvsw = self.components.add(
                name="nvsw",
                description="NVIDIA NVSwitch",
                count=nvswitch_count,
            )
            nvsw.choice = Component.SWITCH

        pcisw = self.components.add(
            name="pciesw",
            description="PCIe switches SW1-SW4",
            count=4,
        )
        pcisw.choice = Component.SWITCH

        pciesl = self.components.add(
            name="pciesl",
            description="PCIe Gen5 x16 FHHL slots (8 general + 2 smart NIC/DPU dedicated)",
            count=10,
        )
        pciesl.choice = Component.CUSTOM
        pciesl.custom.type = "pcie_slot"

        memory = self.components.add(
            name="memory",
            description="DDR5 RDIMM (32 slots, up to 4TB, up to 5600 MT/s)",
            count=32,
        )
        memory.choice = Component.MEMORY

        storage = self.components.add(
            name="storage",
            description=storage_cfg["description"],
            count=storage_cfg["count"],
        )
        storage.choice = Component.CUSTOM

        fperc = None
        if storage_type == "u.2sas/sata":
            fperc = self.components.add(
                name="fperc",
                description="fPERC H965i SAS/SATA RAID controller",
                count=1,
            )
            fperc.choice = Component.CUSTOM

        lom = self.components.add(
            name="lom",
            description="LOM 1GbE x2",
            count=2,
        )
        lom.choice = Component.NIC

        if self.nic_device is not None:
            ocp = self.components.add(
                name="ocp",
                description="OCP 3.0 NIC",
                count=1,
            )
            ocp.choice = Component.NIC

        #Links 
        upi = self.links.add(name="upi", description="Intel UPI inter-CPU fabric")
        xpu_fabric_name = xpu_cfg["fabric"]
        xpu_link = self.links.add(name=xpu_fabric_name, description=f"{xpu_fabric_name} XPU fabric")
        pci = self.links.add(name="pcie_gen5", description="PCI Express Gen 5.0 x16")
        ddr5 = self.links.add(name="ddr5", description="DDR5 up to 5600 MT/s")

        #CPU  
        edge = self.edges.add(DeviceEdge.MANY2MANY, link=upi.name)
        edge.ep1.component = f"{cpu.name}"
        edge.ep2.component = f"{cpu.name}"

        #PCIe switches to CPUs 
        for cpu_index in range(cpu.count):
            e = self.edges.add(DeviceEdge.ONE2ONE, link=pci.name)
            e.ep1.component = f"{pcisw.name}[{2 * cpu_index}]"
            e.ep2.component = f"{cpu.name}[{cpu_index}]"

            e = self.edges.add(DeviceEdge.ONE2ONE, link=pci.name)
            e.ep1.component = f"{pcisw.name}[{2 * cpu_index + 1}]"
            e.ep2.component = f"{cpu.name}[{cpu_index}]"
        
        #PCIe switches to GPUs 
        pciesw_to_xpu = {0: [0, 1],
                        1: [2, 3],
                        2: [4, 5],
                        3: [6, 7]}
        for sw, gpus in pciesw_to_xpu.items():
            e = self.edges.add(DeviceEdge.MANY2MANY, link=pci.name)
            e.ep1.component = f"{pcisw.name}[{sw}]"
            e.ep2.component = f"{xpu.name}[{gpus[0]}:{gpus[1] + 1}]"


        #PCIe switches to PCIe slots 
        pciesw_to_pciesl = {0: [0, 1, 2], 
                            1: [3, 4], 
                            2: [5, 6], 
                            3: [7, 8, 9]}
        for sw, sl in pciesw_to_pciesl.items():
            e = self.edges.add(DeviceEdge.MANY2MANY, link=pci.name)
            e.ep1.component = f"{pcisw.name}[{sw}]"
            e.ep2.component = f"{pciesl.name}[{sl[0]}:{sl[-1] + 1}]"

        #Storage  
        if storage_type in ("e3.s", "u.2nvme"):
            drives_per_sw = storage_cfg["drives_per_sw"]
            for sw in range(pcisw.count):
                e = self.edges.add(DeviceEdge.MANY2MANY, link=pci.name)
                e.ep1.component = f"{pcisw.name}[{sw}]"
                e.ep2.component = f"{storage.name}[{sw * drives_per_sw}:{sw * drives_per_sw + drives_per_sw}]"
        elif storage_type == "u.2sas/sata":
            for cpu_index in range(cpu.count):
                e = self.edges.add(DeviceEdge.ONE2ONE, link=pci.name)
                e.ep1.component = f"{cpu.name}[{cpu_index}]"
                e.ep2.component = f"{fperc.name}[0]"
            e = self.edges.add(DeviceEdge.MANY2MANY, link=pci.name)
            e.ep1.component = f"{fperc.name}[0]"
            e.ep2.component = f"{storage.name}[0:{storage.count}]"

        #XPU fabric 
        if xpu_fabric_name in ("nvlink_3", "nvlink_4"):
            e = self.edges.add(DeviceEdge.MANY2MANY, link=xpu_link.name)
            e.ep1.component = f"{xpu.name}[0:{xpu.count}]"
            e.ep2.component = f"{nvsw.name}[0:{nvswitch_count}]"
        elif xpu_fabric_name in ("infinity_fabric", "osfp_link"):
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

        #NIC 
        e = self.edges.add(DeviceEdge.MANY2MANY, link=pci.name)
        e.ep1.component = f"{cpu.name}[0]"
        e.ep2.component = f"{lom.name}[0:2]"

        if self.nic_device is not None:
            e = self.edges.add(DeviceEdge.ONE2ONE, link=pci.name)
            e.ep1.component = f"{cpu.name}[0]"
            e.ep2.component = f"{ocp.name}[0]"


if __name__ == "__main__":
    device = Dellxe9680(xpu_type="h200", storage_type="u.2nvme")
    print(device.serialize(encoding=Device.YAML))