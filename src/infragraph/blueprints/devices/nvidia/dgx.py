from typing import Optional, Literal, Dict, Union
from infragraph import *

# ============================================================
# DGX Profiles (LOCKED combinations)
# ============================================================

DgxProfile = Literal[
    "dgx1",
    "dgx2",
    "dgx_a100",
    "dgx_h100",
    "dgx_gh200",
    "dgx_gb200",
]

# ============================================================
# Profile Catalog (authoritative)
# ============================================================

DGX_PROFILE_CATALOG: Dict[DgxProfile, dict] = {
    "dgx1": {
        "cpu": {
            "description": "2x Intel Xeon E5-2698 v4",
            "fabric": "qpi",
            "pcie_gen": "gen3",
            "count": 2,
        },
        "xpu": {
            "description": "NVIDIA Tesla V100 SXM2",
            "count": 8,
            "fabric": "nvlink",
            "nvlink_gen": "NVLink 2.0",
            "nvswitch_count": 0,
        },
    },
    "dgx2": {
        "cpu": {
            "description": "2x Intel Xeon Platinum 8168",
            "fabric": "upi",
            "pcie_gen": "gen3",
            "count": 2,
        },
        "xpu": {
            "description": "NVIDIA Tesla V100 SXM2",
            "count": 16,
            "fabric": "nvlink",
            "nvlink_gen": "NVLink 2.0",
            "nvswitch_count": 12,
        },
    },
    "dgx_a100": {
        "cpu": {
            "description": "2x AMD EPYC 7742 (64-core)",
            "fabric": "infinity_fabric",
            "pcie_gen": "gen4",
            "count": 2,
        },
        "xpu": {
            "description": "NVIDIA A100 80GB SXM4",
            "count": 8,
            "fabric": "nvlink",
            "nvlink_gen": "NVLink 3.0",
            "nvswitch_count": 6,
        },
    },
    "dgx_h100": {
        "cpu": {
            "description": "2x AMD EPYC 9654 (96-core)",
            "fabric": "infinity_fabric",
            "pcie_gen": "gen5",
            "count": 2,
        },
        "xpu": {
            "description": "NVIDIA H100 / H200 SXM5",
            "count": 8,
            "fabric": "nvlink",
            "nvlink_gen": "NVLink 4.0",
            "nvswitch_count": 4,
        },
    },
    "dgx_gh200": {
        "cpu": {
            "description": "2x NVIDIA Grace CPU",
            "fabric": "nvlink_c2c",
            "pcie_gen": None,
            "count": 2,
        },
        "xpu": {
            "description": "NVIDIA Grace Hopper Superchip",
            "count": 4,
            "fabric": "nvlink_c2c",
            "nvlink_gen": "NVLink-C2C",
            "nvswitch_count": 0,
        },
    },
    "dgx_gb200": {
        "cpu": {
            "description": "NVIDIA Grace Superchip",
            "fabric": "nvlink_c2c",
            "pcie_gen": None,
            "count": 1,
        },
        "xpu": {
            "description": "NVIDIA Grace Blackwell Superchip",
            "count": 4,
            "fabric": "nvlink_c2c",
            "nvlink_gen": "NVLink-C2C",
            "nvswitch_count": 0,
        },
    },
}

# ============================================================
# DGX Device (PROFILE-LOCKED)
# ============================================================

class NvidiaDGX(Device):
    def __init__(
        self,
        profile: DgxProfile = "dgx_h100",
        nic_device: Optional[Device] = None,
    ):
        super(Device, self).__init__()

        if profile not in DGX_PROFILE_CATALOG:
            raise ValueError(f"Unsupported DGX profile: {profile}")

        self.name = f"NVIDIA_{profile.upper()}"
        self.description = "NVIDIA DGX System"

        cfg = DGX_PROFILE_CATALOG[profile]
        cpu_cfg = cfg["cpu"]
        xpu_cfg = cfg["xpu"]

        # ----------------------------------------------------
        # CPU
        # ----------------------------------------------------
        cpu = self.components.add(
            name="cpu",
            description=cpu_cfg["description"],
            count=cpu_cfg["count"],
        )
        cpu.choice = Component.CPU

        # ----------------------------------------------------
        # XPU
        # ----------------------------------------------------
        xpu = self.components.add(
            name="xpu",
            description=xpu_cfg["description"],
            count=xpu_cfg["count"],
        )
        xpu.choice = Component.XPU

        # ----------------------------------------------------
        # NVSwitch (only if present)
        # ----------------------------------------------------
        if xpu_cfg["nvswitch_count"] > 0:
            nvsw = self.components.add(
                name="nvlsw",
                description="NVIDIA NVSwitch",
                count=xpu_cfg["nvswitch_count"],
            )
            nvsw.choice = Component.CUSTOM
        else:
            nvsw = None

        # ----------------------------------------------------
        # PCIe Fabric (x86 DGX only)
        # ----------------------------------------------------
        if cpu_cfg["pcie_gen"] is not None:
            pciesw = self.components.add(
                name="pciesw",
                description=f"PCIe {cpu_cfg['pcie_gen'].upper()} Switch",
                count=4,
            )
            pciesw.choice = Component.SWITCH

            pciesl = self.components.add(
                name="pciesl",
                description="PCIe x16 FHFL Slot",
                count=8,
            )
            pciesl.choice = Component.CUSTOM
        else:
            pciesw = None
            pciesl = None

        # ----------------------------------------------------
        # NIC (x86 DGX only)
        # ----------------------------------------------------
        if pciesl is not None:
            nic = self.components.add(
                name="nic",
                description="NVIDIA ConnectX / BlueField",
                count=pciesl.count,
            )
            nic.choice = Component.NIC

        # ====================================================
        # Links
        # ====================================================
        cpu_fabric = self.links.add(
            name="cpu_fabric",
            description=cpu_cfg["fabric"],
        )

        xpu_fabric = self.links.add(
            name="xpu_fabric",
            description=xpu_cfg["nvlink_gen"],
        )

        if pciesw is not None:
            pcie = self.links.add(
                name="pcie",
                description=f"PCI Express {cpu_cfg['pcie_gen'].upper()} x16",
            )

        # ====================================================
        # CPU ↔ CPU
        # ====================================================
        edge = self.edges.add(DeviceEdge.MANY2MANY, cpu_fabric.name)
        edge.ep1.component = cpu.name
        edge.ep2.component = cpu.name

        # ====================================================
        # CPU ↔ PCIe Switch
        # ====================================================
        if pciesw is not None:
            edge = self.edges.add(DeviceEdge.MANY2MANY, pcie.name)
            edge.ep1.component = "cpu[0]"
            edge.ep2.component = "pciesw[0]"

            edge = self.edges.add(DeviceEdge.MANY2MANY, pcie.name)
            edge.ep1.component = "cpu[0]"
            edge.ep2.component = "pciesw[1]"

            edge = self.edges.add(DeviceEdge.MANY2MANY, pcie.name)
            edge.ep1.component = "cpu[1]"
            edge.ep2.component = "pciesw[2]"

            edge = self.edges.add(DeviceEdge.MANY2MANY, pcie.name)
            edge.ep1.component = "cpu[1]"
            edge.ep2.component = "pciesw[3]"

        # ====================================================
        # PCIe Switch ↔ XPU
        # ====================================================
        if pciesw is not None:
            for sw, gpu_range in zip(
                range(4),
                ["0:2", "2:4", "4:6", "6:8"],
            ):
                edge = self.edges.add(DeviceEdge.MANY2MANY, pcie.name)
                edge.ep1.component = f"pciesw[{sw}]"
                edge.ep2.component = f"xpu[{gpu_range}]"

        # ====================================================
        # PCIe Switch ↔ Slots
        # ====================================================
        if pciesl is not None:
            for sw, slot_range in zip(
                range(4),
                ["0:2", "2:4", "4:6", "6:8"],
            ):
                edge = self.edges.add(DeviceEdge.MANY2MANY, pcie.name)
                edge.ep1.component = f"pciesw[{sw}]"
                edge.ep2.component = f"pciesl[{slot_range}]"

        # ====================================================
        # Slot ↔ NIC
        # ====================================================
        if pciesl is not None:
            for idx in range(pciesl.count):
                edge = self.edges.add(DeviceEdge.ONE2ONE, pcie.name)
                edge.ep1.component = f"pciesl[{idx}]"
                edge.ep2.component = f"nic[{idx}]"

        # ====================================================
        # XPU Fabric
        # ====================================================
        if nvsw is not None:
            edge = self.edges.add(DeviceEdge.MANY2MANY, xpu_fabric.name)
            edge.ep1.component = "xpu"
            edge.ep2.component = "nvlsw"
        else:
            edge = self.edges.add(DeviceEdge.MANY2MANY, xpu_fabric.name)
            edge.ep1.component = "xpu"
            edge.ep2.component = "xpu"


# ============================================================
# Example
# ============================================================

if __name__ == "__main__":
    device = NvidiaDGX(profile="dgx_h100")
    print(device.serialize(encoding=Device.YAML))
