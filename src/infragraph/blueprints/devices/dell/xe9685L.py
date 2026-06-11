from infragraph.infragraph import *
from typing import Optional, Union

NicSpec = Union[str, Device]

class Dellxe9685L(Device):
    def __init__(self, nic_device: Optional[NicSpec] = None):
        super(Device, self).__init__()
        self.nic_device = nic_device
        self.name = "xe9685L"
        self.description = "Dell PowerEdge device 9685L"

        cpu = self.components.add(
            name="cpu",
            description="5th Generation AMD EPYC 9005 Series processors",
            count=2,
        )
        cpu.choice = Component.CPU

        xpu = self.components.add(
            name="xpu",
            description="NVIDIA HGX B200 180GB 1000W SXM6",
            count=8,
        )
        xpu.choice = Component.XPU

        nvswitch = self.components.add(
            name="nvsw",
            description="NV Link switches",
            count=4,
        )
        nvswitch.choice = Component.SWITCH

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
            description="DDR5 RDIMM (24 slots, up to 3TB, up to 6400 MT/s)",
            count=24,
        )
        memory.choice = Component.MEMORY

        storage = self.components.add(
            name="storage",
            description="Front bays: 8x U.2 NVMe direct from PSB (PCIe Gen5)",
            count=8,
        )
        storage.choice = Component.CUSTOM

        nic = self.components.add(
            name="lom",
            description="LOM 1GbE",
            count=2,
        )
        nic.choice = Component.NIC

        if self.nic_device is not None:
            ocp = self.components.add(
                name="ocp",
                description="OCP 3.0 NIC",
                count=1,
            )
            ocp.choice = Component.NIC

        gmi = self.links.add(name="gmi", description="Global memory link 16GT/s")
        nvlink = self.links.add(name="nvlink_4", description="NVLink 4.0 100GT/s")
        pci = self.links.add(name="pcie_gen5", description="PCI Express Gen 5.0 32GT/s")
        ddr5 = self.links.add(name="ddr5", description="DDR5 6400MT/s")

        #CPU
        edge = self.edges.add(DeviceEdge.MANY2MANY, link=gmi.name)
        edge.ep1.component = f"{cpu.name}"
        edge.ep2.component = f"{cpu.name}"

        #pcie connections
        pciesw_to_xpu_mapping = {
            0: [0, 1],
            1: [2, 3],
            2: [4, 5],
            3: [6, 7],
        }

        pciesw_to_pciesl_mapping = {
            0: [0, 1, 2],
            1: [3, 4, 5],
            2: [6, 7, 8],
            3: [9, 10, 11],
        }

        #PCIe switches to GPUs
        for sw, gpus in pciesw_to_xpu_mapping.items():
            e = self.edges.add(DeviceEdge.MANY2MANY, link=pci.name)
            e.ep1.component = f"{pcisw.name}[{sw}]"
            e.ep2.component = f"{xpu.name}[{gpus[0]}:{gpus[1] + 1}]"

        #PCIe switches to PCIe slots
        for sw, sl in pciesw_to_pciesl_mapping.items():
            e = self.edges.add(DeviceEdge.MANY2MANY, link=pci.name)
            e.ep1.component = f"{pcisw.name}[{sw}]"
            e.ep2.component = f"{pciesl.name}[{sl[0]}:{sl[-1] + 1}]"

        #PCIe switches to CPUs 
        for cpu_index in range(cpu.count):
            e = self.edges.add(DeviceEdge.ONE2ONE, link=pci.name)
            e.ep1.component = f"{pcisw.name}[{2 * cpu_index}]"
            e.ep2.component = f"{cpu.name}[{cpu_index}]"

            e = self.edges.add(DeviceEdge.ONE2ONE, link=pci.name)
            e.ep1.component = f"{pcisw.name}[{2 * cpu_index + 1}]"
            e.ep2.component = f"{cpu.name}[{cpu_index}]"

        #PCIe switches to storage 
        for sw in range(pcisw.count):
            e = self.edges.add(DeviceEdge.MANY2MANY, link=pci.name)
            e.ep1.component = f"{pcisw.name}[{sw}]"
            e.ep2.component = f"{storage.name}[{sw * 2}:{sw * 2 + 2}]"

        #GPUs 
        e = self.edges.add(DeviceEdge.MANY2MANY, link=nvlink.name)
        e.ep1.component = f"{xpu.name}[0:{xpu.count}]"
        e.ep2.component = f"{nvswitch.name}[0:{nvswitch.count}]"

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
        e.ep2.component = f"{nic.name}[0:2]"

        if self.nic_device is not None:
            e = self.edges.add(DeviceEdge.ONE2ONE, link=pci.name)
            e.ep1.component = f"{cpu.name}[0]"
            e.ep2.component = f"{ocp.name}[0]"


if __name__ == "__main__":
    device = Dellxe9685L()
    print(device.serialize(encoding=Device.YAML))