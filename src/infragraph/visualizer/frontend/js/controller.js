let controlleropen= false;

function toggleControllerPanel() {
  controlleropen = !controlleropen;
  document.getElementById('controlPanel').style.display = controlleropen ? 'flex' : 'none'; 
  document.getElementById('controlToggle').classList.toggle('active', controlleropen); 
}

// Slider "input" fires on every pixel of movement; each handler below rewrites
// every node or edge, so coalesce bursts into one update.
function debounce(fn, wait) {
    var timer = null;
    return function () {
        var ctx = this, args = arguments;
        clearTimeout(timer);
        timer = setTimeout(function () { fn.apply(ctx, args); }, wait);
    };
}
var SLIDER_DEBOUNCE_MS = 120;

document.getElementById('fontslider').addEventListener('input', debounce(function () {
    if (!net) return;
    var size = parseInt(this.value);
    var updates = net.body.data.nodes.get().map(function (n) {
        return { id: n.id, font: { size: size } };
    });
    net.body.data.nodes.update(updates);
}, SLIDER_DEBOUNCE_MS));

document.getElementById('edgefont').addEventListener('input', debounce(function () {
    if (!net) return;
    var size = parseInt(this.value);
    var updates = net.body.data.edges.get().map(function (e) {
        return { id: e.id, font: { size: size } };
    });
    net.body.data.edges.update(updates);
}, SLIDER_DEBOUNCE_MS));

document.getElementById('nodeslider').addEventListener('input', debounce(function () {
    if (!net) return;
    var size = parseInt(this.value);
    var updates = net.body.data.nodes.get().map(function (n) {
        return { id: n.id, size: size };
    });
    net.body.data.nodes.update(updates);
}, SLIDER_DEBOUNCE_MS));

// Views with generator-supplied positions have no layout engine to re-run:
// the spacing sliders just scale the stored base positions, which is instant.
function isPrecomputedView() {
    return net && typeof currentData !== 'undefined' && currentData && hasPrecomputedLayout(currentData);
}

function rescalePrecomputed() {
    var sx = parseInt(document.getElementById('spaceslider').value) / SPACE_SLIDER_DEFAULT;
    var sy = parseInt(document.getElementById('levelslider').value) / LEVEL_SLIDER_DEFAULT;
    var updates = net.body.data.nodes.get().map(function (n) {
        return { id: n.id, x: n.baseX * sx, y: n.baseY * sy };
    });
    net.body.data.nodes.update(updates);
    net.fit({ animation: false });
}
var SPACE_SLIDER_DEFAULT = parseInt(document.getElementById('spaceslider').value);
var LEVEL_SLIDER_DEFAULT = parseInt(document.getElementById('levelslider').value);

// Re-runs the hierarchical layout with new spacing, then hands the graph back
// to the user: physics off, and nodes unpinned so they stay draggable on both
// axes (the layout engine re-fixes them on the level axis every time it runs).
function respaceLayout(hierarchical, repulsion) {
    net.off('stabilizationIterationsDone');

    net.setOptions({
        layout: { hierarchical: Object.assign({ enabled: true }, hierarchical) },
        physics: {
            enabled: true,
            hierarchicalRepulsion: Object.assign({
                centralGravity: 0.0, springLength: 150, springConstant: 0.02, damping: 0.5
            }, repulsion),
            stabilization: { iterations: 150, fit: true }
        },
        interaction: { hover: true, dragNodes: true, dragView: true, zoomView: true }
    });

    net.stabilize(1000);
    net.once('stabilizationIterationsDone', function () {
        net.setOptions({ physics: { enabled: false } });
        unpinNodes(net);
        net.fit({ animation: { duration: 10, easingFunction: 'easeInOutQuart' } });
    });
}

// Re-running the vis layout is expensive, so for hierarchical views it happens
// on release ("change") only; precomputed views rescale live while dragging.
var rescaleLive = debounce(function () { if (isPrecomputedView()) rescalePrecomputed(); }, 40);

document.getElementById('spaceslider').addEventListener('input', rescaleLive);
document.getElementById('levelslider').addEventListener('input', rescaleLive);

document.getElementById('spaceslider').addEventListener('change', function () {
    if (!net || isPrecomputedView()) return;
    respaceLayout({}, { nodeDistance: parseInt(this.value) });
});

document.getElementById('levelslider').addEventListener('change', function () {
    if (!net || isPrecomputedView()) return;
    respaceLayout({ levelSeparation: parseInt(this.value) }, {});
});