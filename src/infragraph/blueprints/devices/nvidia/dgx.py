from typing import Optional, Literal, Dict, Union
from infragraph import *

DgxProfile = Literal[
    "dgx1",
    "dgx2",
    "dgx_a100",
    "dgx_h100",
    "dgx_gh200",
    "dgx_gb200",
]

NicSpec = Union[str, Device]

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
            "nvlink_gen": "NVLink 2.0",
            "nvswitch_count": 12,
        },
    },
    "dgx_a100": {
        "cpu": {
            "description": "2x AMD EPYC 7742",
            "fabric": "infinity_fabric",
            "pcie_gen": "gen4",
            "count": 2,
        },
        "xpu": {
            "description": "NVIDIA A100 80GB SXM4",
            "count": 8,
            "nvlink_gen": "NVLink 3.0",
            "nvswitch_count": 6,
        },
    },
    "dgx_h100": {
        "cpu": {
            "description": "2x AMD EPYC 9654",
            "fabric": "infinity_fabric",
            "pcie_gen": "gen5",
            "count": 2,
        },
        "xpu": {
            "description": "NVIDIA H100 / H200 SXM5",
            "count": 8,
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
            "nvlink_gen": "NVLink-C2C",
            "nvswitch_count": 0,
        },
    },
}

class NvidiaDGX(Device):
    """
    InfraGraph model of an NVIDIA DGX system.

    This class represents a *profile-locked* DGX platform (DGX-1 through
    DGX GB200) using an authoritative hardware catalog. Each profile defines
    a fixed topology for CPUs, XPUs (GPUs or superchips), NVLink fabric,
    optional NVSwitches, PCIe switches, slots, and network interfaces.

    The model supports both x86-based DGX systems and Grace / Grace-Hopper /
    Grace-Blackwell architectures, automatically adapting the fabric and
    PCIe topology based on the selected profile.

    Key features:
    - Profile-locked CPU/XPU/NVSwitch combinations
    - Explicit modeling of NVLink, NVLink-C2C, and PCIe fabrics
    - Optional PCIe topology for x86 DGX systems only
    - Flexible NIC modeling via Union[str, Device]
    - Modular internal construction for easy extension and validation

    This class is intended for architectural modeling, topology validation,
    and infrastructure visualization rather than runtime configuration.
    """
    def __init__(
        self,
        profile: DgxProfile = "dgx_h100",
        nic_device: Optional[NicSpec] = None,
    ):
        """
        Initialize an NVIDIA DGX system model.

        Args:
            profile (DgxProfile, optional):
                DGX system profile to instantiate. The profile fully determines
                the CPU, XPU, NVLink generation, NVSwitch count, and PCIe
                topology. Defaults to "dgx_h100".

            nic_device (Optional[Union[str, Device]], optional):
                Network interface specification for PCIe-attached NICs.

                Supported values:
                - None:
                    Adds generic NIC components, one per PCIe slot.
                - str:
                    Uses the provided string as a symbolic NIC description
                    (e.g. "ConnectX-7 400Gb"), applied to all NIC components.
                - Device:
                    Attaches a fully composed InfraGraph Device representing
                    a NIC or DPU, connected via its PCIe endpoint.

                Defaults to None.

        Raises:
            ValueError:
                If an unsupported DGX profile is specified.

            TypeError:
                If nic_device is not None, str, or Device.
        """
        super(Device, self).__init__()

        self._validate_profile(profile)

        self.profile = profile
        self.cfg = DGX_PROFILE_CATALOG[profile]

        self.name = f"NVIDIA_{profile.upper()}"
        self.description = "NVIDIA DGX System"

        self.cpu = self._add_cpu()
        self.xpu = self._add_xpu()
        self.nvsw = self._add_nvswitch()
        self.pciesw, self.pciesl = self._add_pcie_fabric()

        self._add_links()
        self._wire_cpu()
        self._wire_pcie()
        self._wire_xpu()
        self._add_nics(nic_device)

    # Validation
    def _validate_profile(self, profile: DgxProfile):
        if profile not in DGX_PROFILE_CATALOG:
            raise ValueError(f"Unsupported DGX profile: {profile}")

    # Component builders
    def _add_cpu(self):
        cfg = self.cfg["cpu"]
        cpu = self.components.add(
            name="cpu",
            description=cfg["description"],
            count=cfg["count"],
        )
        cpu.choice = Component.CPU
        return cpu

    def _add_xpu(self):
        cfg = self.cfg["xpu"]
        xpu = self.components.add(
            name="xpu",
            description=cfg["description"],
            count=cfg["count"],
        )
        xpu.choice = Component.XPU
        return xpu

    def _add_nvswitch(self):
        count = self.cfg["xpu"]["nvswitch_count"]
        if count <= 0:
            return None

        sw = self.components.add(
            name="nvlsw",
            description="NVIDIA NVSwitch",
            count=count,
        )
        sw.choice = Component.SWITCH
        return sw

    def _add_pcie_fabric(self):
        cfg = self.cfg["cpu"]

        if cfg["pcie_gen"] is None:
            return None, None

        sw = self.components.add(
            name="pciesw",
            description=f"PCIe {cfg['pcie_gen'].upper()} Switch",
            count=4,
        )
        sw.choice = Component.SWITCH

        sl = self.components.add(
            name="pciesl",
            description="PCIe x16 FHFL Slot",
            count=8,
        )
        sl.choice = Component.CUSTOM
        sl.custom.type = "pcie_slot"

        return sw, sl

    # Links
    def _add_links(self):
        cpu_cfg = self.cfg["cpu"]
        xpu_cfg = self.cfg["xpu"]

        self.cpu_fabric = self.links.add(
            name="cpu_fabric",
            description=cpu_cfg["fabric"],
        )

        self.xpu_fabric = self.links.add(
            name="xpu_fabric",
            description=xpu_cfg["nvlink_gen"],
        )

        if self.pciesw is not None:
            self.pcie = self.links.add(
                name="pcie",
                description=f"PCI Express {cpu_cfg['pcie_gen'].upper()} x16",
            )
        else:
            self.pcie = None

    # Wiring
    def _wire_cpu(self):
        edge = self.edges.add(DeviceEdge.MANY2MANY, self.cpu_fabric.name)
        edge.ep1.component = "cpu"
        edge.ep2.component = "cpu"

    def _wire_pcie(self):
        if not self.pciesw:
            return

        # CPU ↔ Switch
        for cpu_idx, sw_idxs in [(0, [0, 1]), (1, [2, 3])]:
            for sw in sw_idxs:
                edge = self.edges.add(DeviceEdge.MANY2MANY, self.pcie.name)
                edge.ep1.component = f"cpu[{cpu_idx}]"
                edge.ep2.component = f"pciesw[{sw}]"

        # Switch ↔ GPU
        for sw, gpu_range in zip(range(4), ["0:2", "2:4", "4:6", "6:8"]):
            edge = self.edges.add(DeviceEdge.MANY2MANY, self.pcie.name)
            edge.ep1.component = f"pciesw[{sw}]"
            edge.ep2.component = f"xpu[{gpu_range}]"

        # Switch ↔ Slot
        for sw, slot_range in zip(range(4), ["0:2", "2:4", "4:6", "6:8"]):
            edge = self.edges.add(DeviceEdge.MANY2MANY, self.pcie.name)
            edge.ep1.component = f"pciesw[{sw}]"
            edge.ep2.component = f"pciesl[{slot_range}]"

    def _wire_xpu(self):
        if self.nvsw:
            edge = self.edges.add(DeviceEdge.MANY2MANY, self.xpu_fabric.name)
            edge.ep1.component = "xpu"
            edge.ep2.component = "nvlsw"
        else:
            edge = self.edges.add(DeviceEdge.MANY2MANY, self.xpu_fabric.name)
            edge.ep1.component = "xpu"
            edge.ep2.component = "xpu"

    # NIC handling
    def _add_nics(self, nic_device: Optional[NicSpec]):
        if not self.pciesl:
            return

        if nic_device is None:
            self._add_generic_nics()
        elif isinstance(nic_device, str):
            self._add_symbolic_nics(nic_device)
        elif isinstance(nic_device, Device):
            self._add_device_nics(nic_device)
        else:
            raise TypeError("nic_device must be None, str, or Device")

    def _add_generic_nics(self):
        nic = self.components.add(
            name="nic",
            description="NVIDIA ConnectX / BlueField",
            count=self.pciesl.count,
        )
        nic.choice = Component.NIC

        self._wire_slots_to_nics("nic")

    def _add_symbolic_nics(self, desc: str):
        nic = self.components.add(
            name="desc",
            description=desc,
            count=self.pciesl.count,
        )
        nic.choice = Component.NIC

        self._wire_slots_to_nics("nic")

    def _add_device_nics(self, dev: Device):
        nic = self.components.add(
            name=dev.name,
            description=dev.description,
            count=self.pciesl.count,
        )
        nic.choice = Component.DEVICE

        edge = self.edges.add(DeviceEdge.ONE2ONE, self.pcie.name)
        edge.ep1.device = f"{nic.name}[0:{self.pciesl.count}]"
        edge.ep1.component = "pcie_endpoint[0]"
        edge.ep2.component = f"pciesl[0:{self.pciesl.count}]"

    def _wire_slots_to_nics(self, nic_name: str):
        for idx in range(self.pciesl.count):
            edge = self.edges.add(DeviceEdge.ONE2ONE, self.pcie.name)
            edge.ep1.component = f"pciesl[{idx}]"
            edge.ep2.component = f"{nic_name}[{idx}]"

if __name__ == "__main__":
    print(NvidiaDGX("dgx_h100").serialize(encoding=Device.YAML))