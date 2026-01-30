from typing import Literal, Dict, Optional, Union
from infragraph import *

Cx5Variant = Literal[
    "cx5_25g_dual",
    "cx5_50g_dual",
    "cx5_100g_dual",
    "cx5_100g_single",
]

CX5_VARIANT_CATALOG: Dict[Cx5Variant, dict] = {
    "cx5_25g_dual": {
        "ports": 2,
        "speed": "25GbE",
        "pcie_gen": "gen3",
    },
    "cx5_50g_dual": {
        "ports": 2,
        "speed": "50GbE",
        "pcie_gen": "gen3",
    },
    "cx5_100g_dual": {
        "ports": 2,
        "speed": "100GbE",
        "pcie_gen": "gen3",
    },
    "cx5_100g_single": {
        "ports": 1,
        "speed": "100GbE",
        "pcie_gen": "gen3",
    },
}

class Cx5(Device):
    """
    InfraGraph model of a Mellanox ConnectX-5 NIC.

    Transceiver handling:
      - None   → no transceiver
      - str    → transceiver as a component (placeholder / connector)
      - Device → transceiver as a nested device
    """

    def __init__(
        self,
        variant: Cx5Variant = "cx5_100g_dual",
        transceiver: Optional[Union[str, Device]] = None,
    ):
        super(Device, self).__init__()

        self._validate_variant(variant)

        self.variant = variant
        self.cfg = CX5_VARIANT_CATALOG[variant]
        self.transceiver = transceiver

        self.name = f"cx5_{self.cfg['speed'].lower()}"
        self.description = f"Mellanox ConnectX-5 {self.cfg['speed']} NIC"

        # Core components
        self.pcie_endpoint = self._add_pcie_endpoint()
        self.asic = self._add_asic()
        self.port = self._add_ports()

        # Optional transceiver
        if isinstance(self.transceiver, Device):
            self.transceiver_component = self._add_transceiver_device(self.transceiver)
        elif isinstance(self.transceiver, str):
            self.transceiver_component = self._add_transceiver_component(self.transceiver)
        else:
            self.transceiver_component = None

        self._add_links()
        # Wiring
        self._wire_internal()

        if self.transceiver_component:
            self._wire_ports_to_transceiver()

    def _validate_variant(self, variant: Cx5Variant):
        if variant not in CX5_VARIANT_CATALOG:
            raise ValueError(f"Unsupported CX5 variant: {variant}")

    def _add_pcie_endpoint(self):
        pcie = self.components.add(
            name="pcie_endpoint",
            description=f"PCI Express {self.cfg['pcie_gen'].upper()} x16 endpoint",
            count=1,
        )
        pcie.choice = Component.CUSTOM
        pcie.custom.type = "pcie_endpoint"
        return pcie

    def _add_asic(self):
        asic = self.components.add(
            name="asic",
            description="ConnectX-5 network processing ASIC",
            count=1,
        )
        asic.choice = Component.CPU
        return asic

    def _add_ports(self):
        port = self.components.add(
            name="port",
            description=f"Ethernet port ({self.cfg['speed']})",
            count=self.cfg["ports"],
        )
        port.choice = Component.PORT
        return port

    def _add_transceiver_device(self, qsfp: Device):
        """
        Add transceiver as a nested device.
        """
        comp = self.components.add(
            name=qsfp.name,
            description="QSFP transceiver device",
            count=self.cfg["ports"],
        )
        comp.choice = Component.DEVICE
        return comp

    def _add_transceiver_component(self, name: str):
        """
        Add transceiver as a simple component (connector / placeholder).
        """
        comp = self.components.add(
            name=name,
            description="QSFP transceiver (abstract)",
            count=self.cfg["ports"],
        )
        comp.choice = Component.PORT
        return comp

    def _add_links(self):
        """
        Declare internal link types used by the CX-5 NIC.
        """

        # PCIe internal fabric (endpoint ↔ ASIC)
        self.links.add(
            name="pcie_internal",
            description=f"Internal PCIe {self.cfg['pcie_gen'].upper()} fabric",
        )

        # High-speed SerDes lanes (ASIC ↔ ports)
        self.links.add(
            name="serdes",
            description="High-speed SerDes lanes",
        )

        # Electrical interface (port ↔ transceiver)
        self.links.add(
            name="electrical",
            description="Electrical interface to transceiver",
        )

    def _wire_internal(self):
        """
        PCIe Endpoint → ASIC → Ports
        """

        # PCIe endpoint to ASIC
        edge = self.edges.add(
            scheme=DeviceEdge.ONE2ONE,
            link="pcie_internal",
        )
        edge.ep1.component = "pcie_endpoint"
        edge.ep2.component = "asic"

        # ASIC to ports
        edge = self.edges.add(
            scheme=DeviceEdge.MANY2MANY,
            link="serdes",
        )
        edge.ep1.component = "asic"
        edge.ep2.component = "port"

    def _wire_ports_to_transceiver(self):
        """
        Wire CX-5 ports to transceiver electrical interface.
        """

        for idx in range(self.cfg["ports"]):
            edge = self.edges.add(
                scheme=DeviceEdge.ONE2ONE,
                link="electrical",
            )
            edge.ep1.component = f"port[{idx}]"

            # Device-backed transceiver
            if isinstance(self.transceiver, Device):
                edge.ep2.device = f"{self.transceiver.name}[{idx}]"
                edge.ep2.component = "electrical_port[0]"

            # Component-only transceiver
            else:
                edge.ep2.component = f"{self.transceiver_component.name}[{idx}]"

            self.edges.append(edge)

if __name__ == "__main__":
    print(Cx5("cx5_100g_dual").serialize(encoding=Device.YAML))
