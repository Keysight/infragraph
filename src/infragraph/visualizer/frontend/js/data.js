// Data fetching + preparation.

function fetchGraphData(file) {
    if (typeof GRAPH_DATA !== 'undefined' && GRAPH_DATA[file]) {
        return Promise.resolve(GRAPH_DATA[file]);
    }
    return Promise.reject(new Error('Graph data not found: ' + file));
}
function getNodeSize(n) {
    var sizes = { host: 30, switch: 25, cpu: 18, xpu: 20, nic: 16, port: 10, device: 22, custom: 14 };
    return sizes[n.type] || 16;
}

//nodes in light and dark theme
function prepareData(rawData) {
    var rs = getComputedStyle(document.documentElement);
    var fontColor = rs.getPropertyValue('--text-primary').trim();
    var edgeFontColor = rs.getPropertyValue('--text-secondary').trim();
    var strokeColor = rs.getPropertyValue('--canvas-stroke').trim();
    var highlightColor = rs.getPropertyValue('--text-primary').trim();

    var nodes = rawData.nodes.map(function (n) {
        var hasImage = !!n.image;
        return {
            // Functional fields (used by filters / search / navigation)
            id: n.id,
            label: n.label,
            title: n.title,
            deviceType: n.type || 'unknown',
            drillable: !!n.drillable,
            drillTarget: n.drillTarget,
            device: n.device,
            shape: hasImage ? 'rectangle' : 'ellipse',
            size: n.size || getNodeSize(n),
            image: hasImage ? n.image : undefined,
            fontColor: fontColor,
            strokeColor: strokeColor,
        };
    });

    var edges = rawData.edges.map(function (e, idx) {
        return {
            id: 'e_' + idx,
            from: e.from,
            to: e.to,
            label: e.label || '',
            title: e.title,
            linkType: e.link || 'unknown',
            color: e.color || '#555',
            highlightColor: highlightColor,
            width: e.width || 1,
            edgeFontColor: edgeFontColor,
            strokeColor: strokeColor,
        };
    });

    // Raw data kept for theme re-renders
    return { nodes: nodes, edges: edges, _rawData: rawData };
}

// Convert to Cytoscape elements ({data: {...}}).
function buildElements(data) {
    var nodeEls = data.nodes.map(function (n) {
        var d = {};
        for (var k in n) d[k] = n[k];
        return { data: d };
    });
    var edgeEls = data.edges.map(function (e) {
        return {
            data: {
                id: e.id,
                source: e.from,
                target: e.to,
                label: e.label,
                title: e.title,
                linkType: e.linkType,
                color: e.color,
                highlightColor: e.highlightColor,
                width: e.width,
                edgeFontColor: e.edgeFontColor,
                strokeColor: e.strokeColor,
            }
        };
    });
    return nodeEls.concat(edgeEls);
}