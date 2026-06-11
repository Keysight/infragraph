from infragraph.infragraph import *
from typing import Optional, Union, Literal

NicSpec = Union[str, Device]
XpuType = Literal["h200", "b200"]


class Dellxe9680L(Device):
    def __init__(
        self,
        nic_device: Optional[NicSpec] = None,
        xpu_type: XpuType = "h200",
    ):
        super(Device, self).__init__()
        self.nic_device = nic_device
        self.name = "xe9680L"
        self.description = "Dell PowerEdge XE9680L"

        XPU_CATALOG = {
            "h200": {
                "description": "NVIDIA HGX H200 141GB 700W SXM5",
                "fabric": "nvlink_4",
                "count": 8,
                "nvswitch_count": 4,
            },
            "b200": {
                "description": "NVIDIA HGX B200 180GB 1000W SXM6",
                "fabric": "nvlink_4",
                "count": 8,
                "nvswitch_count": 4,
            },
        }

        xpu_cfg = XPU_CATALOG[xpu_type]

        cpu = self.components.add(
            name="cpu",
            description="5th gen Intel Xeon Scalable",
            count=2,
        )
        cpu.choice = Component.CPU

        xpu = self.components.add(
            name="xpu",
            description=xpu_cfg["description"],
            count=xpu_cfg["count"],
        )
        xpu.choice = Component.XPU

        nvsw = self.components.add(
            name="nvsw",
            description="NVIDIA NVSwitch",
            count=xpu_cfg["nvswitch_count"],
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
            description="PCIe Gen5 x16 FHHL slots (10 general + 2 NIC/DPU dedicated)",
            count=12,
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
            description="Front bays: 8x U.2 NVMe direct from PSB (PCIe Gen5)",
            count=8,
        )
        storage.choice = Component.CUSTOM

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
        nvlink = self.links.add(name="nvlink_4", description="NVLink 4.0 XPU fabric")
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
                            1: [3, 4, 5], 
                            2: [6, 7, 8], 
                            3: [9, 10, 11]}
        for sw, sl in pciesw_to_pciesl.items():
            e = self.edges.add(DeviceEdge.MANY2MANY, link=pci.name)
            e.ep1.component = f"{pcisw.name}[{sw}]"
            e.ep2.component = f"{pciesl.name}[{sl[0]}:{sl[-1] + 1}]"

        #PCIe switches to storage 
        for sw in range(pcisw.count):
            e = self.edges.add(DeviceEdge.MANY2MANY, link=pci.name)
            e.ep1.component = f"{pcisw.name}[{sw}]"
            e.ep2.component = f"{storage.name}[{sw * 2}:{sw * 2 + 2}]"

        #GPU  
        e = self.edges.add(DeviceEdge.MANY2MANY, link=nvlink.name)
        e.ep1.component = f"{xpu.name}[0:{xpu.count}]"
        e.ep2.component = f"{nvsw.name}[0:{nvsw.count}]"

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
    device = Dellxe9680L(xpu_type="b200")
    print(device.serialize(encoding=Device.YAML))