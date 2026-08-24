// vis.js layout/physics options
// Top-level fabric view: vertical hierarchy , devices and switches
const fabricOptions = {
  layout: {
    hierarchical: {
      enabled: true, direction: 'DU', sortMethod: 'directed',
      nodeSpacing: 120, levelSeparation: 100
    }
  },
  physics: {
    enabled: true,
    hierarchicalRepulsion: {
      centralGravity: 0.0, springLength: 120, springConstant: 0.01,
      nodeDistance: 150, damping: 0.09
    },
    stabilization: { iterations: 150, fit: true }
  },
  interaction: { hover: true, tooltipDelay: 100, dragNodes: true, dragView: true, zoomView: true },
};

// Internal device view: horizontal hierarchy , components inside a device
const internalOptions = {
  layout: {
    hierarchical: {
      enabled: true, direction: 'LR', sortMethod: 'directed',
      nodeSpacing: 100, levelSeparation: 180
    }
  },
  physics: {
    enabled: true,
    hierarchicalRepulsion: {
      centralGravity: 0.0, springLength: 150, springConstant: 0.01,
      nodeDistance: 130, damping: 0.09
    },
    stabilization: { iterations: 150, fit: true }
  },
  interaction: { hover: true, dragNodes: true, dragView: true, zoomView: true },
};

// Hierarchical layout pins every node on the level axis (fixed.y for the UD/DU
// fabric view, fixed.x for the LR internal view), so drags along that axis are
// ignored. Freeze nodes at their current positions and clear `fixed` so they
// keep their layout spot with physics off but stay draggable in both axes.
function unpinNodes(network) {
  const pos = network.getPositions();
  const updates = network.body.data.nodes.get().map(function (node) {
    const p = pos[node.id];
    return p ? { id: node.id, x: p.x, y: p.y, fixed: false } : { id: node.id, fixed: false };
  });
  network.body.data.nodes.update(updates);
}

// Renders a vis.js network into #mynetwork.
// After stabilization, physics is disabled and nodes are pinned so
// users can drag freely without the layout re-simulating.
function renderNetwork(data, options, onNodeClick) {
  const network = new vis.Network(document.getElementById('mynetwork'), data, options);

  network.once('stabilizationIterationsDone', function () {
    network.setOptions({ physics: { enabled: false } });
    unpinNodes(network);
  });


  let clickTimer = null; //adding a timer to differentiate between click and hold

  network.on('hold', function (params) {
    if (params.nodes.length) {
      clearTimeout(clickTimer); 
      focusConnectedNodes(params.nodes[0]);
    }
  });

  network.on('click', function (params) {
    if (params.nodes.length && onNodeClick) {
      clickTimer = setTimeout(function () {
        onNodeClick(params.nodes[0]);
      }, 300); 
    }
  });

  return network;
}