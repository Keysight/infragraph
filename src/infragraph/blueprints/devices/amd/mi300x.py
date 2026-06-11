"""
This device is designed from figure 2(page 8) of BCM957608 application note available at https://docs.broadcom.com/doc/957608-AN2XX
"""

from infragraph.infragraph import *

class MI300X(Device):

    """
    This blueprint returns a topology for typical NIC, GPU, and PCIe Switch configuration inside a AI/ML host
    """

    def __init__(self):
        super(Device, self).__init__()
        self.name = "mi300x"
        self.description = "NIC, GPU, and PCIe Switch Configuration Inside a AI/ML Host"

        cpu = self.components.add(
            name="cpu",
            description="Host CPU",
            count=2,
        )
        cpu.choice = Component.CPU

        xpu = self.components.add(
            name="xpu",
            description="AMD INSTINCT MI300X OAM",
            count=8,
        )
        xpu.choice = Component.XPU

        pcisw = self.components.add(
            name="pciesw",
            description="Broadcom Atlas2 PCIe switches",
            count=4,
        )
        pcisw.choice = Component.SWITCH

        nic = self.components.add(
            name="nic",
            description="Broadcom Thor2 400G NIC",
            count=8,
        )
        nic.choice = Component.NIC

        fnt_nic = self.components.add(
            name="frontend_nic",
            description="Front-end NIC (400G/100G/25G frontend network)",
            count=2,
        )
        fnt_nic.choice = Component.CUSTOM
        fnt_nic.custom.type= "front_end_nic"

        storage = self.components.add(
            name="storage",
            description="NVMe SSD",
            count=8,
        )
        storage.choice = Component.CUSTOM
        storage.custom.type = "nvme"

        lom = self.components.add(
            name="lom",
            description="LOM 1GbE management NIC",
            count=1,
        )
        lom.choice = Component.CUSTOM
        lom.custom.type= "lom_nic"

        bmc = self.components.add(
            name="bmc",
            description="Baseboard Management Controller",
            count=1,
        )
        bmc.choice = Component.CUSTOM
        bmc.custom.type = "bmc_nic"

        #Links
        qpi = self.links.add(name="qpi", description="QPI CPU fabric")
        xpu_link = self.links.add(name="infinity_fabric", description="AMD Infinity Fabric (xGMI point-to-point mesh)")
        pci = self.links.add(name="pcie", description="Host PCIe interconnect")

        #CPU
        edge = self.edges.add(DeviceEdge.MANY2MANY, link=qpi.name)
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
            e.ep2.component = f"{xpu.name}[{gpus[0]}:{gpus[-1] + 1}]"

        #PCIe switches to NICs 
        pciesw_to_nic = {0: [0, 1],
                            1: [2, 3],
                            2: [4, 5],
                            3: [6, 7]}
        for sw, nics in pciesw_to_nic.items():
            e = self.edges.add(DeviceEdge.MANY2MANY, link=pci.name)
            e.ep1.component = f"{pcisw.name}[{sw}]"
            e.ep2.component = f"{nic.name}[{nics[0]}:{nics[-1] + 1}]"

        #PCIe switches to NVMe 
        pciesw_to_storage = {0: [0, 1],
                             1: [2, 3],
                             2: [4, 5],
                             3: [6, 7]}
        for sw, drives in pciesw_to_storage.items():
            e = self.edges.add(DeviceEdge.MANY2MANY, link=pci.name)
            e.ep1.component = f"{pcisw.name}[{sw}]"
            e.ep2.component = f"{storage.name}[{drives[0]}:{drives[-1] + 1}]"

        #XPU fabric 
        e = self.edges.add(DeviceEdge.MANY2MANY, link=xpu_link.name)
        e.ep1.component = f"{xpu.name}[0:{xpu.count}]"
        e.ep2.component = f"{xpu.name}[0:{xpu.count}]"

        #NIC - Front-end 
        for nic_index in range(fnt_nic.count):
            e = self.edges.add(DeviceEdge.ONE2ONE, link=pci.name)
            e.ep1.component = f"{cpu.name}[{nic_index}]"
            e.ep2.component = f"{fnt_nic.name}[{nic_index}]"

        #LOM and BMC 
        e = self.edges.add(DeviceEdge.ONE2ONE, link=pci.name)
        e.ep1.component = f"{cpu.name}[0]"
        e.ep2.component = f"{lom.name}[0]"

        e = self.edges.add(DeviceEdge.ONE2ONE, link=pci.name)
        e.ep1.component = f"{cpu.name}[0]"
        e.ep2.component = f"{bmc.name}[0]"


if __name__ == "__main__":
    device = MI300X()
    print(device.serialize(encoding=Device.YAML))