from typing import Optional, Literal, Dict, Union
from infragraph import *

DgxProfile = Literal[
    "dgx1",
    "dgx2",
    "dgx_a100",
    "dgx_h100",
    # "dgx_gh200",
    "dgx_gb200",
]

NicSpec = Union[str, Device]

DGX_PROFILE_CATALOG: Dict[DgxProfile, dict] = {

    "dgx1": {
        "cpu": {
            "description": "Intel Xeon E5-2698 v4 (Broadwell-EP)",
            "fabric": "qpi",
            "count": 2,
        },
        "xpu": {
            "description": "NVIDIA Tesla P100 SXM2",
            "fabric": "nvlink_1",
            "count": 8,
            "nvswitch_count": 0,
        },
        "pciesw": {
            "description": "PLX PEX8796 PCIe Switch",
            "fabric": "pcie_gen3",
            "count": 4,   # one per GPU pair
        },
        "pciesl": {
            "description": "Internal PCIe x16 endpoints (GPU-attached)",
            "fabric": "pcie_gen3",
            "count": 4,
        }
    },

    "dgx2": {
        "cpu": {
            "description": "Intel Xeon Platinum 8168 (Skylake-SP)",
            "fabric": "upi",
            "count": 2,
        },
        "xpu": {
            "description": "NVIDIA Tesla V100 SXM2",
            "fabric": "nvlink_2",
            "count": 16,
            "nvswitch_count": 12,
        },
        "pciesw": {
            "description": "Broadcom / PLX PEX8796 PCIe Switch",
            "fabric": "pcie_gen3",
            "count": 8,
        },
        "pciesl": {
            "description": "Internal PCIe x16 endpoints (GPU + NVSwitch)",
            "fabric": "pcie_gen3",
            "count": 8,
        }
    },

    "dgx_a100": {
        "cpu": {
            "description": "AMD EPYC 7742 (Rome)",
            "fabric": "infinity_fabric",
            "count": 2,
        },
        "xpu": {
            "description": "NVIDIA A100 SXM4",
            "fabric": "nvlink_3",
            "count": 8,
            "nvswitch_count": 6,
        },
        "pciesw": {
            "description": "Broadcom / PLX PCIe Gen4 Switch",
            "fabric": "pcie_gen4",
            "count": 6,   # aligned with NVSwitch + NIC fanout
        },
        "pciesl": {
            "description": "PCIe Gen4 x16 slots (NIC / storage)",
            "fabric": "pcie_gen4",
            "count": 8,
        }
    },

    "dgx_h100": {
        "cpu": {
            "description": "AMD EPYC 9654 (Genoa)",
            "fabric": "infinity_fabric",
            "count": 2,
        },
        "xpu": {
            "description": "NVIDIA H100 / H200 SXM5",
            "fabric": "nvlink_4",
            "count": 8,
            "nvswitch_count": 4,
        },
        "pciesw": {
            "description": "Broadcom PCIe Gen5 Switch",
            "fabric": "pcie_gen5",
            "count": 4,
        },
        "pciesl": {
            "description": "PCIe Gen5 x16 slots (ConnectX / BlueField)",
            "fabric": "pcie_gen5",
            "count": 8,
        }
    },

    # "dgx_gh200": {
    #     "cpu": {
    #         "description": "NVIDIA Grace CPU",
    #         "fabric": "nvlink_c2c",
    #         "count": 2,
    #     },
    #     "xpu": {
    #         "description": "NVIDIA Grace Hopper Superchip",
    #         "fabric": "nvlink_c2c",
    #         "count": 4,
    #         "nvswitch_count": 0,
    #     },
    #     "pciesw": {
    #         "description": "No discrete PCIe switches (NVLink-C2C system)",
    #         "fabric": None,
    #         "count": 0,
    #     },
    #     "pciesl": {
    #         "description": "External PCIe via Grace IO die",
    #         "fabric": "pcie_gen5",
    #         "count": 4,
    #     }
    # },

    "dgx_gb200": {
        "cpu": {
            "description": "NVIDIA Grace CPU Superchip",
            "fabric": "nvlink_c2c",
            "count": 2,
        },
        "xpu": {
            "description": "NVIDIA Grace Blackwell Superchip",
            "fabric": "nvlink_c2c",
            "count": 4,
            "nvswitch_count": 18,
        },
        "pciesw": {
            "description": "",
            "fabric": "pcie_gen5",
            "count": 0,
        },
        "pciesl": {
            "description": "External PCIe Gen5 lanes from Grace",
            "fabric": "pcie_gen5",
            "count": 4,
        }
    },
}


class NvidiaDGX(Device):
    """
    InfraGraph model of an NVIDIA DGX system.

    This class represents a *profile-locked* DGX platform (DGX-1 through
    DGX GB200) using an authoritative hardware catalog. Each profile defines
    a fixed topology for CPUs, XPUs (GPUs or superchips), NVLink fabric,
    optional NVSwitches, PCIe switches, slots, and network interfacee.

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
                Network interface specification for PCIe-attached NICe.

                Supported values:
                - None:
                    Adds generic NIC components, one per PCIe slot.
                - str:
                    Uses the provided string as a symbolic NIC description
                    (e.g. "ConnectX-7 400Gb"), applied to all NIC component.
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

        if profile not in DGX_PROFILE_CATALOG:
            raise ValueError(f"Unsupported DGX profile: {profile}")

        self.profile = profile
        self.catalog = DGX_PROFILE_CATALOG[profile]

        self.name = profile
        self.description = "NVIDIA DGX System"

        self.cpu = self._add_cpu()
        self.xpu = self._add_xpu()
        self.nvsw = self._add_nvswitch()
        self.pciesw, self.pciesl = self._add_pcie_components()

        self._add_links()
        self._wire_cpu()
        self._wire_pcie()
        self._wire_xpu()
        self._add_nics(nic_device)

    # Components

    def _add_cpu(self):
        cfg = self.catalog["cpu"]
        cpu = self.components.add(
            name="cpu",
            description=cfg["description"],
            count=cfg["count"],
        )
        cpu.choice = Component.CPU
        return cpu

    def _add_xpu(self):
        cfg = self.catalog["xpu"]
        xpu = self.components.add(
            name="xpu",
            description=cfg["description"],
            count=cfg["count"],
        )
        xpu.choice = Component.XPU
        return xpu

    def _add_nvswitch(self):
        count = self.catalog["xpu"]["nvswitch_count"]
        if count <= 0:
            return None
        sw = self.components.add(
            name="nvlsw",
            description="NVIDIA NVSwitch",
            count=count,
        )
        sw.choice = Component.SWITCH
        return sw

    def _add_pcie_components(self):
        pciesw = self.catalog["pciesw"]
        pciesl = self.catalog["pciesl"]

        if pciesw["count"] > 0:
            sw = self.components.add(
                name="pciesw",
                description=pciesw["description"],
                count=pciesw["count"],
            )
            sw.choice = Component.SWITCH
        else:
            sw = None

        if pciesl["count"] > 0:
            sl = self.components.add(
                name="pciesl",
                description=pciesl["description"],
                count=pciesl["count"],
            )
            sl.choice = Component.CUSTOM
            sl.custom.type = "pcie_slot"
        else:
            sl = None

        return sw, sl

    # Links
    def _add_links(self):
        cpu_cfg = self.catalog["cpu"]
        xpu_cfg = self.catalog["xpu"]

        self.cpu_fabric = self.links.add(
            name="cpu_fabric",
            description=cpu_cfg["fabric"],
        )

        self.xpu_fabric = self.links.add(
            name="xpu_fabric",
            description=xpu_cfg["fabric"],
        )

        if self.catalog['pciesw']['fabric'] is not None:
            self.pcie = self.links.add(
                "pcie", f"PCI Express {self.catalog['pciesw']['fabric'].upper()} x16"
            )
        
        if self.profile == "dgx_gb200":
            self.c2c_fabric = self.links.add(
            name="c2c_link",
            description="",
            )


    # Wiring
    def _wire_cpu(self):
        edge = self.edges.add(DeviceEdge.MANY2MANY, self.cpu_fabric.name)
        edge.ep1.component = "cpu"
        edge.ep2.component = "cpu"

    def _wire_pcie(self):
        if self.profile == "dgx1":
            pciesw_to_xpu_mapping = {
                0: [0, 2],
                1: [1, 3],
                2: [4, 6],
                3: [5, 7],
            }
            for sw, gpus in pciesw_to_xpu_mapping.items():
                e = self.edges.add(DeviceEdge.MANY2MANY, self.pcie.name)
                e.ep1.component = f"{self.pciesw.name}[{sw}]"
                e.ep2.component = f"xpu[{gpus[0]}:{gpus[1]+1}:2]"

            for sw in range(0, self.pciesw.count):
                e = self.edges.add(DeviceEdge.ONE2ONE, self.pcie.name)
                e.ep1.component = f"{self.pciesw.name}[{sw}]"
                e.ep2.component = f"{self.pciesl.name}[{sw}]"
            
            for cpu_index in range(0, self.cpu.count):
                e = self.edges.add(DeviceEdge.ONE2ONE, self.pcie.name)
                e.ep1.component = f"{self.pciesw.name}[{ 2 * cpu_index }]"
                e.ep2.component = f"{self.cpu.name}[{cpu_index}]"

                e = self.edges.add(DeviceEdge.ONE2ONE, self.pcie.name)
                e.ep1.component = f"{self.pciesw.name}[{ 2  * cpu_index + 1}]"
                e.ep2.component = f"{self.cpu.name}[{cpu_index}]"
            return

        if self.profile == "dgx2":
            # connect pciesw to v100s
            for pciesw_index in range(0, 8):
                e = self.edges.add(DeviceEdge.MANY2MANY, self.pcie.name)
                e.ep1.component = f"{self.pciesw.name}[{pciesw_index}]"
                e.ep2.component = f"{self.xpu.name}[{2*pciesw_index}:{2*pciesw_index + 2}]"

            # connect slots to pciesw
            for pciesw_index in range(0, 8):
                e = self.edges.add(DeviceEdge.ONE2ONE, self.pcie.name)
                e.ep1.component = f"{self.pciesw.name}[{pciesw_index}]"
                e.ep2.component = f"{self.pciesl.name}[{pciesw_index}]"  
            
            # connect root pciesw to cpu
            pairs = [
                ("8:10", 0),
                ("10:12", 1),
            ]

            for sw_range, cpu_idx in pairs:
                e = self.edges.add(DeviceEdge.MANY2MANY, self.pcie.name)
                e.ep1.component = f"{self.pciesw.name}[{sw_range}]"
                e.ep2.component = f"{self.cpu.name}[{cpu_idx}]"

            pairs = [
                (8, "0:2"),
                (9, "2:4"),
                (10, "4:6"),
                (11, "6:8"),
            ]

            for root_pcie_sw_idx, pcie_idx in pairs:
                e = self.edges.add(DeviceEdge.MANY2MANY, self.pcie.name)
                e.ep1.component = f"{self.pciesw.name}[{root_pcie_sw_idx}]"
                e.ep2.component = f"{self.pciesw.name}[{pcie_idx}]"

            return

        if self.profile == "dgx_a100":
            # cpu to pciesw
            for cpu_idx, sw_idxs in [(0, [0, 1]), (1, [2, 3])]:
                for sw in sw_idxs:
                    e = self.edges.add(DeviceEdge.MANY2MANY, self.pcie.name)
                    e.ep1.component = f"{self.cpu.name}[{cpu_idx}]"
                    e.ep2.component = f"{self.pciesw.name}[{sw}]"
            
            # pciesw to pciesl and xpu
            for pciesw_index in range(0, 4):
                # pciesw to pciesl
                e = self.edges.add(DeviceEdge.MANY2MANY, self.pcie.name)
                e.ep1.component = f"{self.pciesw.name}[{pciesw_index}]"
                e.ep2.component = f"{self.pciesl.name}[{2 * pciesw_index}:{2 * pciesw_index + 2}]"

                # pciesw to xpu
                e = self.edges.add(DeviceEdge.MANY2MANY, self.pcie.name)
                e.ep1.component = f"{self.pciesw.name}[{pciesw_index}]"
                e.ep2.component = f"{self.xpu.name}[{2 * pciesw_index}:{2 * pciesw_index + 2}]"

            # nvsw to pciesw
            e = self.edges.add(DeviceEdge.MANY2MANY, self.pcie.name)
            e.ep1.component = f"{self.pciesw.name}[4]"
            e.ep2.component = f"{self.nvsw.name}[0:6]"   

            # pciesw  4 - 3
            e = self.edges.add(DeviceEdge.ONE2ONE, self.pcie.name)
            e.ep1.component = f"{self.pciesw.name}[4]"
            e.ep2.component = f"{self.pciesw.name}[3]"
            return

        if self.profile == "dgx_h100":
            for cpu_idx in range(0, 2):
                e = self.edges.add(DeviceEdge.MANY2MANY, self.pcie.name)
                e.ep1.component = f"{self.cpu.name}[{cpu_idx}]"
                e.ep2.component = f"{self.pciesl.name}[{cpu_idx*4}:{cpu_idx*4 + 3}]"
            
            for cpu_idx in range(0, 2):
                e = self.edges.add(DeviceEdge.ONE2ONE, self.pcie.name)
                e.ep1.component = f"{self.cpu.name}[{cpu_idx}]"
                e.ep2.component = f"{self.pciesw.name}[{cpu_idx}]"

            for pciesl_idx in range(0, self.pciesl.count):
                e = self.edges.add(DeviceEdge.ONE2ONE, self.pcie.name)
                e.ep1.component = f"{self.pciesl.name}[{pciesl_idx}]"
                e.ep2.component = f"{self.xpu.name}[{pciesl_idx}]"

            for nvsw_idx in range(0, self.nvsw.count):
                e = self.edges.add(DeviceEdge.MANY2MANY, self.pcie.name)
                e.ep1.component = f"{self.nvsw.name}[{nvsw_idx}]"
                e.ep2.component = f"{self.xpu.name}[0:8]"
            
            e = self.edges.add(DeviceEdge.MANY2MANY, self.pcie.name)
            e.ep1.component = f"{self.nvsw.name}[0:4]"
            e.ep2.component = f"{self.pciesw.name}[2]"

            e = self.edges.add(DeviceEdge.ONE2ONE, self.pcie.name)
            e.ep1.component = f"{self.cpu}[0]"
            e.ep2.component = f"{self.pciesw}[2]"
            return

        if self.profile == "dgx_gb200":
            # connect pcie and c2c
            for cpu_idx in range(0, 2):
                e = self.edges.add(DeviceEdge.MANY2MANY, self.pcie.name)
                e.ep1.component = f"{self.cpu.name}[{cpu_idx}]"
                e.ep2.component = f"{self.pciesl.name}[{2*cpu_idx}:{2*cpu_idx + 2}]"

            for cpu_idx in range(0, 2):
                e = self.edges.add(DeviceEdge.MANY2MANY, self.c2c_fabric.name)
                e.ep1.component = f"{self.cpu.name}[{cpu_idx}]"
                e.ep2.component = f"{self.xpu.name}[{2*cpu_idx}:{2*cpu_idx + 2}]"

    def _wire_xpu(self):
        if self.profile == "dgx1":
            # clique 0–3
            e1 = self.edges.add(DeviceEdge.MANY2MANY, self.xpu_fabric.name)
            e1.ep1.component = "xpu[0:4]"
            e1.ep2.component = "xpu[0:4]"

            # clique 4–7
            e2 = self.edges.add(DeviceEdge.MANY2MANY, self.xpu_fabric.name)
            e2.ep1.component = "xpu[4:8]"
            e2.ep2.component = "xpu[4:8]"

            # cross links
            pairs = [(0, 4), (1, 5), (2, 6), (3, 7)]
            for a, b in pairs:
                e = self.edges.add(DeviceEdge.ONE2ONE, self.xpu_fabric.name)
                e.ep1.component = f"xpu[{a}]"
                e.ep2.component = f"xpu[{b}]"
            return

        if self.profile == "dgx2":
            e1 = self.edges.add(DeviceEdge.MANY2MANY, self.xpu_fabric.name)
            e1.ep1.component = "xpu[0:8]"
            e1.ep2.component = "nvlsw[0:6]"

            e2 = self.edges.add(DeviceEdge.MANY2MANY, self.xpu_fabric.name)
            e2.ep1.component = "xpu[8:16]"
            e2.ep2.component = "nvlsw[6:12]"

            e3 = self.edges.add(DeviceEdge.MANY2MANY, self.xpu_fabric.name)
            e3.ep1.component = "nvlsw[0:6]"
            e3.ep2.component = "nvlsw[6:12]"
            return

        if self.profile == "dgx_gb200":
            # xpu to nvlink switch
            e = self.edges.add(DeviceEdge.MANY2MANY, self.xpu_fabric.name)
            e.ep1.component = f"{self.xpu.name}[0:4]"
            e.ep2.component = f"{self.nvsw.name}[0:19]"
            return
        
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
            name=desc,
            description=desc,
            count=self.pciesl.count,
        )
        nic.choice = Component.NIC

        self._wire_slots_to_nics(desc)

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
        edge.ep2.component = f"{self.pciesl.name}[0:{self.pciesl.count}]"

    def _wire_slots_to_nics(self, nic_name: str):
        for idx in range(self.pciesl.count):
            edge = self.edges.add(DeviceEdge.ONE2ONE, self.pcie.name)
            edge.ep1.component = f"{self.pciesl.name}[{idx}]"
            edge.ep2.component = f"{nic_name}[{idx}]"

if __name__ == "__main__":
    print(NvidiaDGX("dgx1").serialize(encoding=Device.YAML))
