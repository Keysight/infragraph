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
    npu_request = Query()
    npu_request.filter.choice = "generic_filter"
    npu_request.filter.attribute_filter.attributes.add(attribute="type", value="xpu")
    npu_response = service.query_graph(npu_request)

    annotation = Annotation()
    for idx, match in enumerate(npu_response.nodes):
        annotation_node = annotation.nodes.add(
            name=match.name
        )
        annotation_node.attributes.add(attribute="rank", value=str(idx))
    service.annotate_graph(annotation)

    # query the graph for rank attributes
    rank_request = Query()
    rank_request.filter.choice = "generic_filter"
    rank_request.filter.attribute_filter.attributes.add(attribute="rank", value="")
    rank_response = service.query_graph(rank_request)

    # validation
    assert len(npu_response.nodes) > 0
    assert len(npu_response.nodes) == len(annotation.nodes)
    assert len(annotation.nodes) == len(rank_response.nodes)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
