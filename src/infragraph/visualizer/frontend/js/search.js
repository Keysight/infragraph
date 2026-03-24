//Node search & picker 

let pickedNodeIds = new Set();

// Simple search
//  highlights matching nodes in the network
function onNodeSearch() {
  const query = document.getElementById('nodeSearch').value.trim().toLowerCase();
  const results = document.getElementById('nodeSearchResults');
  if (!query || !currentData) { results.innerHTML = ''; if (net) net.unselectAll(); return; } // if query is empty or no data loaded, clear results and unselect nodes

  const matches = currentData.nodes.filter(function (n) {
    return n.id.toLowerCase().includes(query) || (n.label && n.label.toLowerCase().includes(query)); // find nodes where ID or label includes the search query (case-insensitive)
  });

  if (!matches.length) {
    results.innerHTML = '<span style="color:#e74c3c">No matches</span>';
    if (net) net.unselectAll();
    return;
  }

  results.innerHTML = matches.slice(0, 12).map(function (m) {
    return '<div style="padding:2px 0;cursor:pointer;" onclick="focusNode(\'' + m.id.replace(/'/g, "\\'") + '\')">' +
      '<span style="color:#2c3e50">' + m.label + '</span></div>';
  }).join('') + (matches.length > 12
    ? '<div style="color:#95a5a6">... and ' + (matches.length - 12) + ' more</div>'
    : ''); // show up to 12 matches, and if more, indicate how many additional matches there are

  if (net) net.selectNodes(matches.map(function (m) { return m.id; }), false);
}

// focus on the node
function focusNode(nodeId) {
  if (net) {
    net.focus(nodeId, { scale: 1.5, animation: { duration: 400, easingFunction: 'easeInOutQuad' } }); 
    net.selectNodes([nodeId]);
  }
}

//  Node picker  

function onPickerSearch() {
  const query = document.getElementById('nodePicker').value.trim().toLowerCase();
  const dd = document.getElementById('pickerDropdown');
  if (!currentData) { dd.classList.remove('open'); return; }

  const matches = currentData.nodes.filter(function (n) {
    return !pickedNodeIds.has(n.id) &&
      (query === '' || n.id.toLowerCase().includes(query) || (n.label && n.label.toLowerCase().includes(query)));
  }); // find nodes that are not already picked and where ID or label includes the search query (case-insensitive)

  if (!matches.length) {
    dd.innerHTML = '<div style="padding:6px 10px;color:#95a5a6;font-size:12px;">No results</div>';
    dd.classList.add('open');
    return;
  }

  dd.innerHTML = matches.slice(0, 30).map(function (m) {
    return '<div class="node-dropdown-item" onmousedown="pickNode(\'' + m.id.replace(/'/g, "\\'") + '\')">' +
      '<span>' + (m.label || m.id) + '</span><span class="dtype">' + (m.id) + '</span></div>';
  }).join('') + (matches.length > 30
    ? '<div style="padding:4px 10px;color:#95a5a6;font-size:11px;">... ' + (matches.length - 30) + ' more - keep typing</div>'
    : '');

  dd.classList.add('open');
}

// Navigation & Breadcrumbs
function closePickerDropdown() {
  document.getElementById('pickerDropdown').classList.remove('open');
}


function pickNode(nodeId) {
  pickedNodeIds.add(nodeId);
  document.getElementById('nodePicker').value = '';// clear search input after picking a node
  closePickerDropdown();
  renderPickedTags();
  if (net) net.selectNodes(Array.from(pickedNodeIds), false); 
}

// Unpick a node from the selection, update the picked tags display, and unselect it in the network visualization. 
// If no nodes remain picked, unselect all in the network.
function unpickNode(nodeId) {
  pickedNodeIds.delete(nodeId);
  renderPickedTags();
  if (net) {
    if (pickedNodeIds.size > 0) net.selectNodes(Array.from(pickedNodeIds), false); 
    else net.unselectAll();
  }
}


function clearPickedNodes() {
  pickedNodeIds.clear();
  renderPickedTags();
  document.getElementById('connInfo').style.display = 'none'; // hide connection info when clearing selection
  if (net) net.unselectAll(); 
}


function renderPickedTags() {
  const container = document.getElementById('pickedNodes');
  const countEl = document.getElementById('pickedCount');
  if (!pickedNodeIds.size) { container.innerHTML = ''; countEl.textContent = ''; return; } 

  countEl.textContent = '(' + pickedNodeIds.size + ' selected)';
  container.innerHTML = Array.from(pickedNodeIds).map(function (id) {
    const node = currentData ? currentData.nodes.find(function (n) { return n.id === id; }) : null;
    return '<span class="picked-tag">' + (node ? node.label || id : id) +
      '<span class="remove-tag" onclick="unpickNode(\'' + id.replace(/'/g, "\\'") + '\')">&#10005;</span></span>';
  }).join('');
}

// shows edges between all currently picked nodes
function showSelectedConnections() {
  const info = document.getElementById('connInfo');
  if (!currentData || pickedNodeIds.size < 2) {
    info.style.display = 'block';
    info.textContent = pickedNodeIds.size < 2 ? 'Pick at least 2 nodes to see connections.' : 'No data loaded.';
    return;
  }

  const sel = new Set(pickedNodeIds);
  const fNodes = currentData.nodes.filter(function (n) { return sel.has(n.id); });
  const fEdges = currentData.edges.filter(function (e) { return sel.has(e.from) && sel.has(e.to); });

  // if edges exist, show count of nodes and edges; if no edges, show message but still display the selected nodes
  info.style.display = 'block';
  info.textContent = fEdges.length ? fNodes.length + ' nodes, ' + fEdges.length + ' direct edge(s) shown.' : 'No direct edges between selected nodes.';

  render({ nodes: fNodes, edges: fEdges }, {
    layout: { hierarchical: { enabled: false } },
    physics: {
      enabled: true,
      barnesHut: {
        gravitationalConstant: -3000, centralGravity: 0.3,
        springLength: 140, springConstant: 0.04, damping: 0.09
      },
      stabilization: { iterations: 200, fit: true }
    },
    interaction: { hover: true, dragNodes: true, dragView: true, zoomView: true },
    nodes: {
      borderWidth: 0, borderWidthSelected: 0,
      font: { size: 13, face: 'arial' },
      shapeProperties: { useBorderWithImage: false },
      fixed: { x: false, y: false }
    },
    edges: {
      smooth: { type: 'curvedCW', roundness: 0.15 },
      font: { size: 11, align: 'middle' }
    }
  });
}

//show connected nodes when clicked on one node

let focusModeActive = false;

function focusConnectedNodes(nodeId) {
  if (!net || !currentData) return; // if network or data is not available, do nothing

  // Find all nodes directly connected to the clicked node
  const connectedIds = new Set();
  connectedIds.add(nodeId);
  currentData.edges.forEach(function (e) {
    if (e.from === nodeId) connectedIds.add(e.to); // add target node of edge if clicked node is the source
    if (e.to === nodeId) connectedIds.add(e.from); // add source node of edge if clicked node is the target
  });

  // Hide nodes not in the connected set
  const updatedNodes = currentData.nodes.map(function (n) {
    return {
      id: n.id,
      hidden: !connectedIds.has(n.id) // hide node if it's not in the set of connected nodes
    };
  });

  // Hide edges not connected to clicked node
  const updatedEdges = currentData.edges.map(function (e) {
    return {
      id: e.id,
      hidden: e.from !== nodeId && e.to !== nodeId
    };
  });

  net.body.data.nodes.update(updatedNodes);
  net.body.data.edges.update(updatedEdges);
  focusModeActive = true;
  
}

