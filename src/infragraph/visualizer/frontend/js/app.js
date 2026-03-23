// app.js: Global state, render function, and boot
//
// Globals exposed for other modules:
//   currentData, net : used by filters.js, search.js
//   render()         : used by filters.js, search.js
//   navigateTo()     : used by render click handler

var currentData = null; 
var net = null; //vis-network instance
var loadingEl;

function initApp() {
    loadingEl = document.getElementById('loading');

    document.getElementById('btn-fit').addEventListener('click', function () {
        if (net) net.fit({ animation: { duration: 400, easingFunction: 'easeInOutQuad' } });
    });

    // Theme toggle
    document.getElementById('btn-theme').addEventListener('click', function () {
        document.documentElement.classList.toggle('dark');
        // Re-render graph with updated font colors
        if (currentData && currentData._rawData) {
            var isInfra = navigationStack.length === 1;
            currentData = prepareData(currentData._rawData);
            render(currentData, isInfra ? fabricOptions : internalOptions);
        }
    });

    initNavigation();
    navigateTo('infrastructure.json', 'Infrastructure');
    
    //legend button for hint
    document.getElementById('btn-hint').addEventListener('click', function () {
    var legend = document.getElementById('legend');
    var isVisible = legend.style.display !== 'none';
    legend.style.display = isVisible ? 'none' : 'block';
    this.textContent = isVisible ? '?' : 'x';
});
}

// Render: creates vis.js network, binds click/hover events
function render(data, options) {
    if (net) { net.destroy(); net = null; }

    var container = document.getElementById('graph-container') || document.getElementById('mynetwork');
    if (!container) return;

    net = new vis.Network(container, {
        nodes: new vis.DataSet(data.nodes),
        edges: new vis.DataSet(data.edges)
    }, options);

    net.once('stabilizationIterationsDone', function () {
        net.setOptions({ physics: { enabled: false } });
        var pos = net.getPositions();
        net.body.data.nodes.forEach(function (node) {
            var p = pos[node.id];
            if (p) net.body.data.nodes.update({ id: node.id, x: p.x, y: p.y, fixed: false });
        });
        net.fit({ animation: { duration: 400, easingFunction: 'easeInOutQuad' } });
    });

    var clickTimer = null;

    net.on('hold', function (params) {
        if (params.nodes.length) {
            clearTimeout(clickTimer);
            if (typeof focusConnectedNodes === 'function') focusConnectedNodes(params.nodes[0]);
        }
    });

    net.on('click', function (params) {
        if (params.nodes.length) {
            clickTimer = setTimeout(function () {
                var nodeId = params.nodes[0];
                var nodeData = data.nodes.find(function (n) { return n.id === nodeId; });
                if (nodeData && nodeData.drillable && nodeData.drillTarget) {
                    navigateTo(nodeData.drillTarget, nodeData.label);
                }
            }, 300);
        }
    });

    net.on('hoverNode', function (params) {
        var nodeData = data.nodes.find(function (n) { return n.id === params.node; });
        if (nodeData) {
            container.style.cursor = nodeData.drillable ? 'pointer' : 'default';
        }
    });

    net.on('blurNode', function () {
        container.style.cursor = 'default';
    });
}

function showLoading() { loadingEl.classList.remove('hidden'); }
function hideLoading() { loadingEl.classList.add('hidden'); }

// Boot
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}