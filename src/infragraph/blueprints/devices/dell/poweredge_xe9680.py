from typing import Optional, Literal, Dict
from infragraph import *

XpuType = Literal["h100", "h200", "h20", "mi300x", "gaudi3"]

CpuType = Literal["5th gen", "4th gen"]

CPU_CATALOG: Dict[XpuType, dict] = {
    "5th gen": {
        "description": "Two 5th Generation Intel Xeon Scalable processors with up to 64 cores per processor"
    },
    "4th gen": {
        "description": "Two 4th Generation Intel Xeon Scalable processors with up to 56 cores per processor"
    },
}

XPU_CATALOG: Dict[XpuType, dict] = {
    "h100": {
        "description": "NVIDIA HGX H100 80GB SXM5",
        "count": 8,
        "interconnect": "nvlink"
    },
    "h200": {
        "description": "NVIDIA HGX H200 141GB SXM5",
        "count": 8,
        "interconnect": "nvlink"
    },
    # "h20": {
    #     "description": "NVIDIA HGX H20 96GB SXM5",
    #     "vendor": "nvidia",
    #     "interconnect": "nvlink",
    # },
    # "mi300x": {
    #     "description": "AMD Instinct MI300X 192GB OAM",
    #     "vendor": "amd",
    #     "interconnect": "infinity_fabric",
    # },
    "gaudi3": {
        "description": "Intel Gaudi 3 128GB OAM",
        "count": 8,
        "interconnect": "roce",
    },
}

class DellPowerEdgeXE9680(Device):
    def __init__(
        self,
        xpu_type: XpuType = "h100",
        cpu_type: CpuType = "4th gen",
        nic_device: Optional[Device] = None,
    ):
        super(Device, self).__init__()
        self.name = "Dell_Poweredge_XE9680"
        self.description = "Dell PowerEdge XE9680"

        # Add CPU
        if cpu_type not in CPU_CATALOG:
            raise ValueError(f"Unsupported XPU type: {xpu_type}")
        cpu = self.components.add(
            name="cpu",
            description=CPU_CATALOG[cpu_type]["description"],
            count=2,
        )
        cpu.choice = Component.CPU

        # add PCIESW
        pciesw = self.components.add(
            name="pciesw",
            description="PCIe Gen5 switch",
            count=4,
        )
        pciesw.choice = Component.SWITCH

        # add PCIE_SLOT
        pciesl = self.components.add(
            name="pciesl",
            description="PCIe Slot",
            count=10,
        )
        pciesl.choice = Component.CUSTOM

        # Create Links
        upi = self.links.add(
            name="upi",
            description="Intel Ultra-Path Interconnect 16 GT/s"
        )
        pcie_gen5 = self.links.add(
            name="pcie_gen5",
            description="PCI Express Gen 5.0 x16 32 GT/s"
        )

        # create GPU Connections:
        # add XPU
        if xpu_type not in XPU_CATALOG:
            raise ValueError(f"Unsupported XPU type: {xpu_type}")
        xpu_cfg = XPU_CATALOG[xpu_type]
        xpu = self.components.add(
            name="xpu",
            description=xpu_cfg["description"],
            count=xpu_cfg["count"],
        )
        xpu.choice = Component.XPU
        # add NVSWITCH for H100 and A100
        if xpu_type == "h100":
            nvsw = self.components.add(
                name="nvlsw",
                description="NVLink Switch",
                count=4,
            )
            nvsw.choice = Component.CUSTOM

            nvlink = self.links.add(
            name="nvlink",
            description="NVLink 4.0 (H100) 100 GT/s")

            # connect XPUs to nvswitch
            for xpu_index in range(xpu.count):
                for nvsw_index in range(nvsw.count):
                    edge = self.edges.add(
                        scheme=DeviceEdge.MANY2MANY,
                        link=nvlink.name
                    )
                    edge.ep1.component = f"{xpu.name}[{xpu_index}]"
                    edge.ep2.component = f"{nvsw.name}[{nvsw_index}]"

        # add NVSWITCH for A100
        elif xpu_type == "a100":
            nvsw = self.components.add(
                name="nvlsw",
                description="NVLink Switch",
                count=6,
            )
            nvsw.choice = Component.CUSTOM

            nvlink = self.links.add(
            name="nvlink",
            description="NVLink 3.0 (A100) 50 GT/s")

            # connect XPUs to nvswitch
            for xpu_index in range(xpu.count):
                for nvsw_index in range(nvsw.count):
                    edge = self.edges.add(
                        scheme=DeviceEdge.MANY2MANY,
                        link=nvlink.name
                    )
                    edge.ep1.component = f"{xpu.name}[{xpu_index}]"
                    edge.ep2.component = f"{nvsw.name}[{nvsw_index}]"
        
        elif xpu_type == "gaudi3":
            # -------------------------
            # Gaudi 3 Fabric Definition
            # -------------------------

            # RoCE fabric (accelerator-owned Ethernet)
            roce = self.links.add(
                name="roce",
                description="RoCE v2 Ethernet Fabric (Gaudi3)"
            )

            # OSFP ports exposed by Gaudi baseboard
            osfp = self.components.add(
                name="osfp",
                description="OSFP 800GbE Fabric Port",
                count=6,
            )
            osfp.choice = Component.CUSTOM

            # -------------------------
            # XPU <-> XPU (Ethernet)
            # Fully-connected fabric
            # -------------------------
            for i in range(xpu.count):
                for j in range(i + 1, xpu.count):
                    edge = self.edges.add(
                        scheme=DeviceEdge.MANY2MANY,
                        link=roce.name
                    )
                    edge.ep1.component = f"{xpu.name}[{i}]"
                    edge.ep2.component = f"{xpu.name}[{j}]"

            # -------------------------
            # XPU <-> OSFP (fabric exit)
            # -------------------------
            for xpu_index in range(xpu.count):
                for osfp_index in range(osfp.count):
                    edge = self.edges.add(
                        scheme=DeviceEdge.MANY2MANY,
                        link=roce.name
                    )
                    edge.ep1.component = f"{xpu.name}[{xpu_index}]"
                    edge.ep2.component = f"{osfp.name}[{osfp_index}]"

        # # TODO: add for infinity fabric and XPUs as well

        # Create Edges
        # CPU EDGE
        edge = self.edges.add(
            scheme=DeviceEdge.MANY2MANY,
            link=upi.name
        )
        edge.ep1.component = cpu.name
        edge.ep2.component = cpu.name

        # CPU TO PCIE SWITCH
        
        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie_gen5.name)
        edge.ep1.component = "cpu[0]"
        edge.ep2.component = "pciesw[0]"

        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie_gen5.name)
        edge.ep1.component = "cpu[0]"
        edge.ep2.component = "pciesw[1]"

        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie_gen5.name)
        edge.ep1.component = "cpu[1]"
        edge.ep2.component = "pciesw[2]"

        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie_gen5.name)
        edge.ep1.component = "cpu[1]"
        edge.ep2.component = "pciesw[3]"

       
        # XPU TO PCIE SWITCH
        for xpu_idx, pciesw_idx in zip(["0:2", "2:4", "4:6", "6:8"], range(pciesw.count)):
            edge = self.edges.add(
                scheme=DeviceEdge.MANY2MANY,
                link=pcie_gen5.name
            )
            edge.ep1.component = f"{xpu.name}[{xpu_idx}]"
            edge.ep2.component = f"{pciesw.name}[{pciesw_idx}]"

        # PCIE SLOT TO PCIE SWITCH
        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie_gen5.name)
        edge.ep1.component = "pcie_sl[0:3]"
        edge.ep2.component = "pciesw[0]"

        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie_gen5.name)
        edge.ep1.component = "pcie_sl[3:5]"
        edge.ep2.component = "pciesw[1]"

        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie_gen5.name)
        edge.ep1.component = "pcie_sl[5:7]"
        edge.ep2.component = "pciesw[2]"

        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie_gen5.name)
        edge.ep1.component = "pcie_sl[7:10]"
        edge.ep2.component = "pciesw[3]"

        # PCIE SWITCH to XPU
        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie_gen5.name)
        edge.ep1.component = "pciesw[0]"
        edge.ep2.component = "xpu[0:2]"

        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie_gen5.name)
        edge.ep1.component = "pciesw[1]"
        edge.ep2.component = "xpu[2:4]"

        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie_gen5.name)
        edge.ep1.component = "pciesw[2]"
        edge.ep2.component = "xpu[4:6]"

        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie_gen5.name)
        edge.ep1.component = "pciesw[3]"
        edge.ep2.component = "xpu[6:8]"


if __name__ == "__main__":
    device = DellPowerEdgeXE9680()
    print(device.serialize(encoding=Device.YAML))
