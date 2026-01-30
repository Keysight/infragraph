from typing import Literal, Dict
from infragraph import *

SfpVariant = Literal[
    "sfp_1g",
    "sfp_plus_10g",
    "sfp28_25g",
    "sfp56_50g",
]

SFP_VARIANT_CATALOG: Dict[SfpVariant, dict] = {
    "sfp_1g": {
        "form_factor": "SFP",
        "speed": "1Gb",
        "lanes": 1,
    },
    "sfp_plus_10g": {
        "form_factor": "SFP+",
        "speed": "10Gb",
        "lanes": 1,
    },
    "sfp28_25g": {
        "form_factor": "SFP28",
        "speed": "25Gb",
        "lanes": 1,
    },
    "sfp56_50g": {
        "form_factor": "SFP56",
        "speed": "50Gb",
        "lanes": 1,
    },
}


class SFP(Device):
    """
    InfraGraph model of an SFP-family pluggable transceiver.

    This class represents SFP, SFP+, SFP28, and SFP56 optical modules.
    All variants share the same internal topology:
    a one-to-one binding between an electrical host interface and
    an optical media interface.

    Variants are profile-locked via an authoritative catalog and
    differ only in bandwidth and signaling characteristics.
    """

    def __init__(self, variant: SfpVariant = "sfp28_25g"):
        """
        Initialize an SFP transceiver model.

        Args:
            variant (SfpVariant, optional):
                SFP variant to instantiate. Determines bandwidth
                and electrical lane count.
                Defaults to "sfp28_25g".

        Raises:
            ValueError:
                If an unsupported SFP variant is specified.
        """
        super(Device, self).__init__()

        self._validate_variant(variant)

        self.variant = variant
        self.cfg = SFP_VARIANT_CATALOG[variant]

        self.name = self.cfg["form_factor"].lower().replace("+", "_plus")
        self.description = f"{self.cfg['form_factor']} {self.cfg['speed']} Transceiver"

        self.electrical_port = self._add_electrical_port()
        self.optical_port = self._add_optical_port()
        self.binding = self._add_links()

        self._wire_internal()

    def _validate_variant(self, variant: SfpVariant):
        if variant not in SFP_VARIANT_CATALOG:
            raise ValueError(f"Unsupported SFP variant: {variant}")

    def _add_electrical_port(self):
        port = self.components.add(
            name="electrical_port",
            description=f"Electrical host interface ({self.cfg['lanes']} lane)",
            count=1,
        )
        port.choice = Component.PORT
        return port

    def _add_optical_port(self):
        port = self.components.add(
            name="optical_port",
            description=f"Optical media interface ({self.cfg['speed']})",
            count=1,
        )
        port.choice = Component.PORT
        return port

    def _add_links(self):
        return self.links.add(
            name="internal_binding",
            description="Electrical-to-optical signal binding",
        )

    def _wire_internal(self):
        edge = self.edges.add(
            scheme=DeviceEdge.ONE2ONE,
            link=self.binding.name,
        )
        edge.ep1.component = "electrical_port"
        edge.ep2.component = "optical_port"


if __name__ == "__main__":
    print(SFP("sfp_plus_10g").serialize(encoding=Device.YAML))
