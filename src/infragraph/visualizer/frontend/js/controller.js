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

document.getElementById('spaceslider').addEventListener('input', function () {
    var spacing = parseInt(this.value);

    net.setOptions({layout: {
        hierarchical: {
        enabled: true,}}})
        
        net.setOptions({
                physics: { enabled: true,
        hierarchicalRepulsion: {
        centralGravity: 0.0, springLength: 150, springConstant:0.02,
        nodeDistance: spacing, damping: 0.5
        },
        stabilization: { iterations: 150, fit: true }
        },
        interaction: { hover: true, dragNodes: true, dragView: true, zoomView: true }, }
    );

    net.setOptions({layout: {
        hierarchical: {
        enabled: true,}}})
        

        net.stabilize(1000);
        net.once('stabilizationIterationsDone', function () {
            net.setOptions({ physics: { enabled: false } });
            net.fit({ animation: { duration: 10, easingFunction: 'easeInOutQuart' } });
        });
    }),


document.getElementById('levelslider').addEventListener('input', function () {
    var spacing = parseInt(this.value);

    net.off('stabilizationIterationsDone');
    net.setOptions({layout: {
    hierarchical: {
      enabled: true, levelSeparation: spacing}}})

    net.setOptions({
            physics: { enabled: true,
    hierarchicalRepulsion: {
      centralGravity: 0.0, springLength: 150, springConstant:0.02,
      damping: 0.5
    },
        stabilization: { iterations: 150, fit: true }
        },
        interaction: { hover: true, dragNodes: true, dragView: true, zoomView: true }, }
            );

  net.stabilize(1000);
        net.once('stabilizationIterationsDone', function () {
            net.setOptions({ physics: { enabled: false } });
            net.fit({ animation: { duration: 10, easingFunction: 'easeInOutQuart' } });
        });
});