// Data fetching and preparation for vis.js

function fetchGraphData(file) {
    if (typeof GRAPH_DATA !== 'undefined' && GRAPH_DATA[file]) {
        return Promise.resolve(GRAPH_DATA[file]);
    }
    return Promise.reject(new Error('Graph data not found: ' + file));
}

// Transforms raw JSON into vis.js-ready objects
// Adds deviceType/linkType fields that filters.js expects

function prepareData(rawData) {
    var isDark = document.documentElement.classList.contains('dark');
    var fontColor = isDark ? '#e6edf3' : '#1f2328';
    var strokeColor = isDark ? '#0e1621' : '#ffffff';

    var nodes = rawData.nodes.map(function (n) {
        return {
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
                strokeWidth: 3, strokeColor: strokeColor
            },
            borderWidth: n.drillable ? 2.5 : 1.5,
            shadow: n.drillable ? { enabled: true, color: 'rgba(74,144,217,0.5)', size: 12, x: 0, y: 0 } : undefined,
            deviceType: n.type || 'unknown',
            drillable: n.drillable,
            drillTarget: n.drillTarget,
            device: n.device
        };
    });

    var edges = rawData.edges.map(function (e, idx) {
        return {
            id: 'e_' + idx,
            from: e.from,
            to: e.to,
            label: e.label || undefined,
            title: e.title,
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
            smooth: { enabled: true, type: 'continuous', roundness: 0.15 },
            linkType: e.link || 'unknown'
        };
    });

    
    // Store raw data for re-rendering on theme change
    return { nodes: nodes, edges: edges, _rawData: rawData };
}