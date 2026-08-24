let controlleropen= false;

function toggleControllerPanel() {
  controlleropen = !controlleropen;
  document.getElementById('controlPanel').style.display = controlleropen ? 'flex' : 'none'; 
  document.getElementById('controlToggle').classList.toggle('active', controlleropen); 
}

document.getElementById('fontslider').addEventListener('input', function () {
    var size = parseInt(this.value);
    var updates = net.body.data.nodes.get().map(function (n) {
        return { id: n.id, font: { size: size } };
    });
    net.body.data.nodes.update(updates);
});

document.getElementById('edgefont').addEventListener('input', function () {
    var size = parseInt(this.value);
    var updates = net.body.data.edges.get().map(function (e) {
        return { id: e.id, font: { size: size } };
    });
    net.body.data.edges.update(updates);
});

document.getElementById('nodeslider').addEventListener('input', function () {
    var size = parseInt(this.value);
    var updates = net.body.data.nodes.get().map(function (n) {
        return { id: n.id, size: size };
    });
    net.body.data.nodes.update(updates);
});

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

document.getElementById('spaceslider').addEventListener('input', function () {
    var spacing = parseInt(this.value);
    respaceLayout({}, { nodeDistance: spacing });
});

document.getElementById('levelslider').addEventListener('input', function () {
    var spacing = parseInt(this.value);
    respaceLayout({ levelSeparation: spacing }, {});
});