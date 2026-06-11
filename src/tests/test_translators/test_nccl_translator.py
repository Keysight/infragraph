import pytest
import os
import yaml

from infragraph import QueryRequest, QueryNodeFilter, QueryNodeId
from infragraph.translators.nccl_translator import NcclParser

DEVICE_NAME = "dgx_a100"


def _mock_file_path():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(
        os.path.join(current_dir, "mock_data", "dgx_a100_nccl_topo.xml")
    )


@pytest.mark.asyncio
async def test_dgx_a100_nccl():
    mock_file_path = _mock_file_path()

    nccl_parser = NcclParser(mock_file_path, device_name=DEVICE_NAME)
    infra_device = nccl_parser.parse(infra_type="infrastructure")
    infra_device_dict = yaml.safe_load(infra_device.serialize("yaml"))

    assert "devices" in infra_device_dict
    device = infra_device_dict["devices"][0]

    assert "components" in device
    assert "edges" in device
    assert "links" in device

    components = device["components"]
    assert len(components) == 6

    cpu = next((c for c in components if c["choice"] == "cpu"), None)
    assert cpu is not None, "No CPU component found"
    assert cpu["count"] == 6

    nvsw = next((c for c in components if c["name"] == "nvsw"), None)
    assert nvsw is not None, "No NVSW component found"
    assert nvsw["count"] == 6

    xpu = next((c for c in components if c["choice"] == "xpu"), None)
    assert xpu is not None, "No XPU component found"
    assert xpu["count"] == 8
    assert "A100" in xpu["description"]

    links = device["links"]
    assert len(links) == 3

    link_names = [link["name"] for link in links]
    assert "nvlink" in link_names
    assert "pci" in link_names


@pytest.mark.asyncio
async def test_dgx_a100_nccl_annotations():
    mock_file_path = _mock_file_path()

    nccl_parser = NcclParser(mock_file_path, device_name=DEVICE_NAME)
    nccl_parser.parse(infra_type="infrastructure")

    # Annotate the graph with the GPU/NIC metadata extracted from the NCCL XML.
    service = nccl_parser.get_annotations()

    # Query the graph for the annotated xpu nodes.
    xpu_request = QueryRequest()
    xpu_filter = xpu_request.node_filters.add(name="xpu filter")
    xpu_filter.choice = QueryNodeFilter.ID_FILTER
    xpu_filter.id_filter.operator = QueryNodeId.REGEX
    xpu_filter.id_filter.value = rf"{DEVICE_NAME}\.0\.xpu\.\d+"
    xpu_response = service.query_graph(xpu_request)

    # One annotated node per GPU.
    assert len(xpu_response.node_matches) == 8

    # Every GPU node carries the metadata pulled from the XML.
    attrs = {a.name: a.value for a in xpu_response.node_matches[0].attributes}
    for key in ("busid", "rank", "dev", "sm", "gdr", "cpu_affinity"):
        assert key in attrs, f"missing '{key}' annotation on xpu node"

    # Query the rank attribute and confirm it is present on every GPU node.
    rank_request = QueryRequest()
    rank_filter = rank_request.node_filters.add(name="rank filter")
    rank_filter.choice = QueryNodeFilter.ATTRIBUTE_FILTER
    rank_filter.attribute_filter.name = "rank"
    rank_filter.attribute_filter.operator = QueryNodeId.REGEX
    rank_filter.attribute_filter.value = r"\d+"
    rank_response = service.query_graph(rank_request)

    assert len(rank_response.node_matches) == 8

    ranks = sorted(
        int(a.value)
        for match in rank_response.node_matches
        for a in match.attributes
        if a.name == "rank"
    )
    assert ranks == list(range(8))