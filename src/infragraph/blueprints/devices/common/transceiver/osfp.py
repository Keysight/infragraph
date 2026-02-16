from typing import Literal, Dict
from infragraph import *

OsfpVariant = Literal[
    "osfp_400g",
    "osfp_800g",
]

OSFP_VARIANT_CATALOG: Dict[OsfpVariant, dict] = {
    "osfp_400g": {
        "form_factor": "OSFP",
        "speed": "400Gbps",
        "lanes": 8,
    },
    "osfp_800g": {
        "form_factor": "OSFP",
        "speed": "800Gbps",
        "lanes": 8,
    },
}


class OSFP(Device):
    """
    InfraGraph model of an OSFP-family pluggable transceiver.

    This class represents OSFP 400G and 800G optical modules.
    All variants share the same internal topology:
    a one-to-one binding between an electrical host interface and
    an optical media interface.

    Variants are profile-locked via an authoritative catalog and
    differ only in bandwidth and signaling characteristics.
    """

    def __init__(self, variant: OsfpVariant = "osfp_800g"):
        """
        Initialize an OSFP transceiver model.

        Args:
            variant (OsfpVariant, optional):
                OSFP variant to instantiate. Determines total bandwidth
                and number of electrical lanes.
                Defaults to "osfp_800g".

        Raises:
            ValueError:
                If an unsupported OSFP variant is specified.
        """
        super(Device, self).__init__()

        self._validate_variant(variant)

        self.variant = variant
        self.cfg = OSFP_VARIANT_CATALOG[variant]

        self.name = self.cfg["form_factor"].lower()
        self.description = f"{self.cfg['form_factor']} {self.cfg['speed']} Transceiver"

        self.electrical_port = self._add_electrical_port()
        self.optical_port = self._add_optical_port()
        self.binding = self._add_links()

        self._wire_internal()

    def _validate_variant(self, variant: OsfpVariant):
        if variant not in OSFP_VARIANT_CATALOG:
            raise ValueError(f"Unsupported OSFP variant: {variant}")

    def _add_electrical_port(self):
        port = self.components.add(
            name="electrical_port",
            description=f"Electrical host interface ({self.cfg['lanes']} lanes)",
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
    print(OSFP("osfp_400g").serialize(encoding=Device.YAML))
