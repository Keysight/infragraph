import pytest
from infragraph import Infrastructure


@pytest.fixture
def infra() -> Infrastructure:
    return Infrastructure()


@pytest.fixture
def closfabric() -> Infrastructure:
    infra = Infrastructure(name="clos-fabric", description="2 Tier Clos Fabric")
    return infra
