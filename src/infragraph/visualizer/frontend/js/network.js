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

// Precomputed view: the generator already assigned x/y/level to every node
// (see Visualizer._compute_layout), so no layout engine or physics is needed.
// Nodes stay draggable because physics is simply off.
const precomputedOptions = {
  layout: { hierarchical: { enabled: false }, improvedLayout: false },
  physics: { enabled: false },
  interaction: { hover: true, tooltipDelay: 100, dragNodes: true, dragView: true, zoomView: true },
};

// Large-graph mode (see isLargeGraph in data.js): hover effects trigger a full
// redraw on every node enter/leave, so turn them off. Tooltips still work.
// (Image interpolation is deliberately left on: measured 3x faster redraws
// when zoomed out on 800+ image nodes.)
const largeGraphOverrides = {
  interaction: { hover: false, hoverConnectedEdges: false, selectConnectedEdges: false },
};

// Node/edge size thresholds above which a view switches to large-graph mode.
const LARGE_GRAPH_NODES = 300;
const LARGE_GRAPH_EDGES = 1000;

function hasPrecomputedLayout(data) {
  return data.nodes.length > 0 && data.nodes.every(function (n) {
    return typeof n.x === 'number' && typeof n.y === 'number';
  });
}

// vis options for a prepared dataset: precomputed positions if the generator
// supplied them, otherwise the hierarchical layout matching the current view
// depth (infrastructure vs. device internals). Returns a fresh copy so the
// shared option objects above are never mutated.
function optionsForData(data) {
  var base;
  if (hasPrecomputedLayout(data)) base = precomputedOptions;
  else base = (typeof navigationStack !== 'undefined' && navigationStack.length > 1) ? internalOptions : fabricOptions;
  var opts = JSON.parse(JSON.stringify(base));
  if (data.large) {
    opts.interaction = Object.assign({}, opts.interaction, largeGraphOverrides.interaction);
  }
  return opts;
}

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