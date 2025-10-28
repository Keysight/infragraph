import pytest
from infragraph import *
from infragraph.blueprints.fabrics.closfabric import ClosFabric
from infragraph.infragraph_service import InfraGraphService


@pytest.mark.asyncio
async def test_rank_annotations():
    """Test adding a rank attribute to every npu node"""
    # create the graph
    service = InfraGraphService()
    service.set_graph(ClosFabric())

    # query the graph for host npus
    npu_request = QueryRequest()
    filter = npu_request.node_filters.add(name="npu filter")
    filter.choice = QueryNodeFilter.ID_FILTER
    filter.id_filter.operator = QueryNodeId.REGEX
    filter.id_filter.value = r"host\.\d+\.npu\.\d+"
    npu_response = service.query_graph(npu_request)

    # annotate the graph
    annotate_request = AnnotateRequest()
    for idx, match in enumerate(npu_response.node_matches):
        annotate_request.nodes.add(name=match.id, attribute="rank", value=str(idx))
    service.annotate_graph(annotate_request)

    # query the graph for rank attributes
    rank_request = QueryRequest()
    filter = rank_request.node_filters.add(name="rank filter")
    filter.choice = QueryNodeFilter.ATTRIBUTE_FILTER
    filter.attribute_filter.name = "rank"
    filter.attribute_filter.operator = QueryNodeId.REGEX
    filter.attribute_filter.value = r"\d+"
    rank_response = service.query_graph(rank_request)

    # validation
    assert len(npu_response.node_matches) > 0
    assert len(npu_response.node_matches) == len(annotate_request.nodes)
    assert len(annotate_request.nodes) == len(rank_response.node_matches)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
