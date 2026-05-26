// Cytoscape stylesheet + layout configs.
// Replaces vis-network's fabricOptions / internalOptions.

// Single stylesheet drives all appearance.
// Per-element styling (colors, shapes, sizes) is read from data() fields
// that prepareData() / buildElements() set on each node and edge.

const cytoscapeStyle = [
    {
        selector: 'node',
        style: {
            'shape': 'data(shape)',
            'width': 'data(size)',
            'height': 'data(size)',
            'label': 'data(label)',
            'font-family': "'JetBrains Mono', 'Fira Code', monospace",
            'font-size': 12,
            'color': 'data(fontColor)',
            'text-outline-color': 'data(strokeColor)',
            'text-outline-width': 2,
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 4,
        }
    },
    {
        // Image nodes (host/switch/etc SVGs): swap background for the image
        selector: 'node[image]',
        style: {
            'background-image': 'data(image)',
            'background-fit': 'contain',
            'background-color': 'transparent',
            'background-opacity': 0,
            'border-width': 0,
        }
    },
    {
        selector: 'node:selected',
        style: {
            'overlay-color': '#3498db',
            'overlay-opacity': 0.35,
            'overlay-padding': 8,
        }
    },
    {
        selector: 'edge',
        style: {
            'line-color': 'data(color)',
            'width': 'data(width)',
            'label': 'data(label)',
            'font-family': "'JetBrains Mono', monospace",
            'font-size': 10,
            'color': 'data(edgeFontColor)',
            'text-outline-color': 'data(strokeColor)',
            'text-outline-width': 2,
            'curve-style': 'bezier',
            'target-arrow-shape': 'none',
            'opacity': 0.75,
        }
    },
    {
        selector: 'edge:selected',
        style: {
            'line-color': 'data(highlightColor)',
            'opacity': 1,
        }
    },
    {
        // Used by focusConnectedNodes() to hide non-neighbours
        selector: '.hidden',
        style: { 'display': 'none',
                'opacity':0,
         }
    },
    {
    selector: 'core',
    style: {
        'active-bg-color': 'transparent',
        'active-bg-opacity': 0,
        'active-bg-size': 0,
        'selection-box-opacity': 0,
        'selection-box-border-width': 0,
        }
    },
];

// Top-level fabric view: vertical hierarchy, devices and switches.
const fabricLayout = {
    name: 'breadthfirst',
    directed: true,
    padding: 30,
    spacingFactor: 1.1,
    avoidOverlap: true,
    animate: false,
    fit: true,
    transform: function (node, pos) { return { x: pos.x, y: -pos.y }; }
};

// Internal device view: horizontal hierarchy, components inside a device.
const internalLayout = {
    name: 'breadthfirst',
    directed: true,
    padding: 30,
    spacingFactor: 1.3,
    avoidOverlap: true,
    animate: false,
    fit: true,
    transform: function (node, pos) { return { x: pos.y, y: pos.x }; }
};

