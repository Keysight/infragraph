// Data fetching and preparation for vis.js

function fetchGraphData(file) {
    // Rack views are synthesised from infrastructure.json on demand rather than
    // shipped, so there is one entry per rack without growing graph_data.js.
    if (typeof isRackFile === 'function' && isRackFile(file)) {
        var view = buildRackView(file, rackHops);
        return view ? Promise.resolve(view)
                    : Promise.reject(new Error('Rack view unavailable: ' + file));
    }
    if (typeof GRAPH_DATA !== 'undefined' && GRAPH_DATA[file]) {
        return Promise.resolve(GRAPH_DATA[file]);
    }
    return Promise.reject(new Error('Graph data not found: ' + file));
}

// Large graphs get a simplified rendering: canvas shadows, stroked text and
// bezier edges are the slowest primitives and are redrawn on every pan/zoom.
// null = decide from size, true/false = user override from the controls panel.
var largeGraphOverride = null;

function isLargeGraph(rawData) {
    if (largeGraphOverride !== null) return largeGraphOverride;
    return rawData.nodes.length >= LARGE_GRAPH_NODES || rawData.edges.length >= LARGE_GRAPH_EDGES;
}

// Transforms raw JSON into vis.js-ready objects
// Adds deviceType/linkType fields that filters.js expects

function prepareData(rawData) {
    var isDark = document.documentElement.classList.contains('dark');
    var fontColor = isDark ? '#e6edf3' : '#1f2328';
    var strokeColor = isDark ? '#0e1621' : '#ffffff';
    var large = isLargeGraph(rawData);

    var nodes = rawData.nodes.map(function (n) {
        var node = {
            id: n.id,
            label: n.label,
            title: n.title,
            shape: n.shape || 'box',
            image: n.image || undefined,
            size: n.size || getNodeSize(n),
            color: buildNodeColor(n),
            font: {
                color: fontColor, size: 12,
                face: "'JetBrains Mono', 'Fira Code', monospace",
                strokeWidth: large ? 0 : 3, strokeColor: strokeColor
            },
            borderWidth: n.drillable ? 2.5 : 1.5,
            shadow: (n.drillable && !large) ? { enabled: true, color: 'rgba(74,144,217,0.5)', size: 12, x: 0, y: 0 } : undefined,
            deviceType: n.type || 'unknown',
            drillable: n.drillable,
            drillTarget: n.drillTarget,
            device: n.device
        };
        // Group nodes of the compressed view: dashed accent border, member list
        // kept for search/tooltips.
        if (n.members) {
            node.members = n.members;
            node.kind = n.kind || 'group';
            node.rackCount = n.rackCount || 0;
            if (typeof canOpenRack === 'function' && isRackGroup(node) && !canOpenRack(node)) {
                node.title += '\n\nToo large to open. Lower the compression to reach a smaller group.';
            }
            node.borderWidth = 3;
            node.shapeProperties = { useBorderWithImage: true, borderDashes: [6, 4] };
            node.color = Object.assign({}, node.color, {
                border: '#4a90d9',
                highlight: Object.assign({}, node.color.highlight, { border: '#e67e22' }),
                hover: Object.assign({}, node.color.hover, { border: '#6aa8e8' })
            });
        }
        // Rack view context: the switches a rack uplinks to are shown faded so
        // the rack's own members read as the subject of the view.
        if (typeof n.inRack === 'boolean') node.inRack = n.inRack;
        if (n.inRack === false) {
            node.opacity = 0.5;
            node.font = Object.assign({}, node.font, { color: isDark ? '#8b949e' : '#8c959f' });
        }
        // Positions precomputed by the generator (infrastructure view). The
        // originals are kept so the spacing sliders can rescale them cheaply.
        if (typeof n.x === 'number' && typeof n.y === 'number') {
            node.x = n.x; node.y = n.y; node.level = n.level;
            node.baseX = n.x; node.baseY = n.y;
        }
        return node;
    });

    var edges = rawData.edges.map(function (e, idx) {
        var title = e.title;
        // Edge labels are dropped in large mode; keep the ×N info in the tooltip.
        if (large && e.label && e.label !== e.link) title = e.label + '\n' + title;
        return {
            id: 'e_' + idx,
            from: e.from,
            to: e.to,
            label: large ? undefined : (e.label || undefined),
            title: title,
            color: {
                color: e.color || '#555',
                highlight: isDark ? '#e6edf3' : '#1f2328',
                hover: lightenColor(e.color || '#555'),
                opacity: 0.7
            },
            width: e.width || 1,
            font: {
                color: isDark ? '#8b949e' : '#656d76', size: 10,
                face: "'JetBrains Mono', monospace",
                strokeWidth: 2, strokeColor: strokeColor, align: 'middle'
            },
            smooth: large ? { enabled: false } : { enabled: true, type: 'continuous', roundness: 0.15 },
            linkType: e.link || 'unknown',
            count: e.count || 1
        };
    });

    var byId = new Map();
    nodes.forEach(function (n) { byId.set(n.id, n); });

    // Store raw data for re-rendering on theme change
    return {
        nodes: nodes, edges: edges, byId: byId, large: large,
        rackView: !!rawData.rackView, _rawData: rawData
    };
}