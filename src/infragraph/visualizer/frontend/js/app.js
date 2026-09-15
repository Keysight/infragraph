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
        if (currentData && currentData._rawData) rerenderCurrent();
    });

    // Large-graph mode override (auto by default)
    var largeToggle = document.getElementById('largeGraphToggle');
    if (largeToggle) {
        largeToggle.addEventListener('change', function () {
            largeGraphOverride = this.checked;
            if (currentData && currentData._rawData) rerenderCurrent();
        });
    }

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

// A rack or pod that is too large to expand is not clickable, so say so with the
// cursor rather than letting the click quietly do nothing.
function cursorFor(node) {
    if (typeof isRackGroup === 'function' && isRackGroup(node)) {
        return canOpenRack(node) ? 'pointer' : 'not-allowed';
    }
    return node.drillable ? 'pointer' : 'default';
}

// Brief message at the bottom of the canvas. Used for actions that are refused
// or silently adjusted, which would otherwise look like nothing happened.
var toastTimer = null;
function showToast(message) {
    var el = document.getElementById('toast');
    if (!el) return;
    el.textContent = message;
    el.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.classList.remove('show'); }, 3600);
}

// Re-prepares the current view from its raw data (theme or render-mode change)
// and redraws it with the full dataset.
function rerenderCurrent() {
    currentData = prepareData(currentData._rawData);
    render(currentData, optionsForData(currentData));
    if (typeof populateFilters === 'function') populateFilters(currentData);
    syncLargeGraphToggle();
}

function syncLargeGraphToggle() {
    var cb = document.getElementById('largeGraphToggle');
    if (cb && currentData) cb.checked = !!currentData.large;
}

// Render: creates vis.js network, binds click/hover events
function render(data, options) {
    if (net) { net.destroy(); net = null; }

    var container = document.getElementById('graph-container') || document.getElementById('mynetwork');
    if (!container) return;

    var nodeById = data.byId || new Map(data.nodes.map(function (n) { return [n.id, n]; }));

    net = new vis.Network(container, {
        nodes: new vis.DataSet(data.nodes),
        edges: new vis.DataSet(data.edges)
    }, options);

    if (options.physics && options.physics.enabled === false) {
        // Nothing to stabilize. A hierarchical layout still pins every node on
        // the level axis, so release them or they cannot be dragged freely.
        var h = options.layout && options.layout.hierarchical;
        if (h && h.enabled) unpinNodes(net);
        net.fit({ animation: false });
    } else {
        net.once('stabilizationIterationsDone', function () {
            net.setOptions({ physics: { enabled: false } });
            unpinNodes(net);
            net.fit({ animation: { duration: 400, easingFunction: 'easeInOutQuad' } });
        });
    }

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
                var nodeData = nodeById.get(nodeId);
                if (!nodeData) return;
                if (typeof isRackGroup === 'function' && isRackGroup(nodeData)) {
                    openRack(nodeData);            // rack or pod: show its servers in context
                } else if (nodeData.drillable && nodeData.drillTarget) {
                    navigateTo(nodeData.drillTarget, nodeData.label);
                }
            }, 300);
        }
    });

    net.on('hoverNode', function (params) {
        var nodeData = nodeById.get(params.node);
        if (nodeData) {
            container.style.cursor = cursorFor(nodeData);
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