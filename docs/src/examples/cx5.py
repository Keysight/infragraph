import sys
sys.path.append("../../../artifacts")

from infragraph import Infrastructure, Device, Component, Link, Annotation


class Cx5:
    def __init__(self, infra: Infrastructure, ports: int = 2):
        """Constructs an InfraGraph device based on a Mellanox CX5 network card
        and adds it the infrastructure devices property.

        """
        cx5 = infra.devices.add(name="cx5", connections=[])
        cx5.description = "Mellanox ConnectX-5 with 2 ports, 1 CX5 network processor chip, 1 pcie gen4 bus"
        asic = cx5.components.add(name="asic", type="cpu", description="Offload network processor chip")
        port = cx5.components.add(name="port", type="custom", external=True, description="The network ports on the ConnectX-5 card",)
        pcie = cx5.links.add(name="pcie")
        for port_idx in range(ports):
            cx5.connections.append(f"{asic.name}.0.{pcie.name}.{port.name}.{port_idx}")

if __name__ == "__main__":
    infra = Infrastructure(name="clos-fabric", description="2 Tier Clos Fabric")
    Cx5(infra)
    print(infra)