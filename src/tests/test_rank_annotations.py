import pytest
from infragraph import *
from infragraph.blueprints.fabrics.closfabric import ClosFabric
from infragraph.infragraph_service import InfraGraphService


@pytest.mark.asyncio
async def test_rank_annotations():
    """Test adding a rank attribute to every xpu node"""
    # create the graph
    service = InfraGraphService()
    service.set_graph(ClosFabric())

    # query the graph for host npus
    npu_request = QueryRequest()
    filter = npu_request.node_filters.add(name="xpu filter")
    filter.choice = QueryNodeFilter.ID_FILTER
    filter.id_filter.operator = QueryNodeId.REGEX
    filter.id_filter.value = r"host\.\d+\.xpu\.\d+"
    npu_response = service.query_graph(npu_request)

    annotation = Annotation()
    for idx, match in enumerate(npu_response.node_matches):
        annotation_node = annotation.nodes.add(
            name=match.id
        )
        annotation_node.attributes.add(attribute="rank", value=str(idx))
    service.annotate_graph(annotation.serialize())

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
    assert len(npu_response.node_matches) == len(annotation.nodes)
    assert len(annotation.nodes) == len(rank_response.node_matches)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
