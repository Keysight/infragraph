import pytest
from infragraph import *
from infragraph.blueprints.fabrics.closfabric import ClosFabric
from infragraph.infragraph_service import InfraGraphService


def _make_service():
    service = InfraGraphService()
    service.set_graph(ClosFabric())
    return service


def _annotate_graph(service, **kwargs):
    annotation = Annotation()
    for attr, value in kwargs.items():
        annotation.graph.add(attribute=attr, value=str(value))
    service.annotate_graph(annotation)


@pytest.mark.asyncio
async def test_graph_query_eq_match():
    """A graph filter with an eq operator returns the matching attribute."""
    service = _make_service()
    _annotate_graph(service, cluster="rack-a", region="us-east")

    request = QueryRequest()
    filter = request.graph_filters.add(name="cluster filter")
    filter.attribute_filter.name = "cluster"
    filter.attribute_filter.operator = QueryAttribute.EQ
    filter.attribute_filter.value = "rack-a"
    response = service.query_graph(request)

    assert len(response.graph_matches) == 1
    assert response.graph_matches[0].name == "cluster"
    assert response.graph_matches[0].value == "rack-a"


@pytest.mark.asyncio
async def test_graph_query_regex_no_match():
    """A graph filter that does not match any attribute returns an empty result."""
    service = _make_service()
    _annotate_graph(service, cluster="rack-a")

    request = QueryRequest()
    filter = request.graph_filters.add(name="missing filter")
    filter.attribute_filter.name = "cluster"
    filter.attribute_filter.operator = QueryAttribute.REGEX
    filter.attribute_filter.value = r"rack-b"
    response = service.query_graph(request)

    assert len(response.graph_matches) == 0


@pytest.mark.asyncio
async def test_graph_query_contains_match():
    """A graph filter with a contains operator returns the matching attribute."""
    service = _make_service()
    _annotate_graph(service, experiment="run-42")

    request = QueryRequest()
    filter = request.graph_filters.add(name="experiment filter")
    filter.attribute_filter.name = "experiment"
    filter.attribute_filter.operator = QueryAttribute.CONTAINS
    filter.attribute_filter.value = "run-"
    response = service.query_graph(request)

    assert len(response.graph_matches) == 1
    assert response.graph_matches[0].value == "run-42"


if __name__ == "__main__":
    pytest.main(["-s", __file__])
