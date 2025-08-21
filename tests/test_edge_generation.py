import re
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "pattern",
    [
        "[dgxa100.32]",
        "{npu.0}(pcie){pcieswsw.0}",
        "{npu.0:1}(pcie){pcieswsw.0}",
        "[dgxa100.0][cx5.0]{dpu.0}(pcie)[dgxa100.0]{npu.0}",
    ],
)
async def test_edge_generation(pattern):
    """Test generation of edges based on patterns

    - {} component
    - [] device
    - () link
    - . index separator
        - followed by a zero based index or a range
        - : range separator must include start:stop
            - start
                The index to start the slice (inclusive).
                Defaults to 0 if omitted.
            - stop
                The index to end the slice (exclusive).
                The element at this index is not included in the result.
                Defaults to the end of the sequence if omitted.

    - final edge is of the form: [c.idx|d.idx c.idx|ddc, l, c|dc|ddc] where
        - d is device name
        - c is component name
        - l is link name
        - idx is index
    """

    print(f"pattern: {pattern}")
    edge = re.split(r"\(|\)", pattern)
    device_left = component_left = link = device_right = component_right = None
    component_left = re.findall(r"\{(.*?)\}", edge[0])
    device_left = re.findall(r"\[(.*?)\]", edge[0])
    if len(edge) > 1:
        link = edge[1]
    if len(edge) > 2:
        component_right = re.findall(r"\{(.*?)\}", edge[2])
        device_right = re.findall(r"\[(.*?)\]", edge[2])
    print(device_left, component_left, link, device_right, component_right)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
