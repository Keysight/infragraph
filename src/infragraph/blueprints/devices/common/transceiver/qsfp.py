from typing import Literal, Dict
from infragraph import *

QsfpVariant = Literal[
    "qsfp_plus_40g",
    "qsfp28_100g",
    "qsfp56_200g",
    "qsfp_dd_400g",
    "qsfp_dd_800g"
]

QSFP_VARIANT_CATALOG: Dict[QsfpVariant, dict] = {
    "qsfp_plus_40g": {
        "form_factor": "QSFP+",
        "speed": "40Gb",
        "lanes": 4,
    },
    "qsfp28_100g": {
        "form_factor": "QSFP28",
        "speed": "100Gb",
        "lanes": 4,
    },
    "qsfp56_200g": {
        "form_factor": "QSFP56",
        "speed": "200Gb",
        "lanes": 4,
    },
    "qsfp_dd_400g": {
        "form_factor": "QSFP-DD",
        "speed": "400Gb",
        "lanes": 8,
    },
    "qsfp_dd_800g": {
        "form_factor": "QSFP-DD",
        "speed": "800Gb",
        "lanes": 8,
    }
}

class QSFP(Device):
    """
    InfraGraph model of a QSFP-family pluggable transceiver.

    This class represents QSFP+, QSFP28, QSFP56, QSFP-DD, and OSFP
    optical modules. All variants share the same internal topology:
    a one-to-one binding between an electrical host interface and
    an optical media interface.

    Variants are profile-locked via an authoritative catalog and
    differ only in bandwidth, signaling lanes, and form factor.
    """

    def __init__(self, variant: QsfpVariant = "qsfp28_100g"):
        """
        Initialize a QSFP transceiver model.

        Args:
            variant (QsfpVariant, optional):
                QSFP variant to instantiate. Determines form factor,
                total bandwidth, and number of electrical lanes.
                Defaults to "qsfp28_100g".

        Raises:
            ValueError:
                If an unsupported QSFP variant is specified.
        """
        super(Device, self).__init__()

        self._validate_variant(variant)

        self.variant = variant
        self.cfg = QSFP_VARIANT_CATALOG[variant]

        self.name = self.cfg["form_factor"].lower().replace("-", "_")
        self.description = f"{self.cfg['form_factor']} {self.cfg['speed']} Transceiver"

        self.electrical_port = self._add_electrical_port()
        self.optical_port = self._add_optical_port()
        self.binding = self._add_links()

        self._wire_internal()

    def _validate_variant(self, variant: QsfpVariant):
        if variant not in QSFP_VARIANT_CATALOG:
            raise ValueError(f"Unsupported QSFP variant: {variant}")

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
    print(QSFP("qsfp_dd_400g").serialize(encoding=Device.YAML))
