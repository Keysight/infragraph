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
    npu_request.attribute_query.node_filters.add(name="xpu_filter").attribute_filters.attributes.add(attribute="type", value="xpu")
    npu_response = service.query_graph(npu_request).attribute_query
    npu_nodes = npu_response.nodes[0].nodes

    annotation = Annotation()
    for idx, match in enumerate(npu_nodes):
        annotation_node = annotation.nodes.add(
            name=match.name
        )
        annotation_node.attributes.add(attribute="rank", value=str(idx))
    service.annotate_graph(annotation)

    # query the graph for rank attributes
    rank_request = QueryRequest()
    rank_request.attribute_query.node_filters.add(name="rank_filter").attribute_filters.attributes.add(attribute="rank", value="")
    rank_response = service.query_graph(rank_request).attribute_query
    rank_nodes = rank_response.nodes[0].nodes

    # validation
    assert len(npu_nodes) > 0
    assert len(npu_nodes) == len(annotation.nodes)
    assert len(annotation.nodes) == len(rank_nodes)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
