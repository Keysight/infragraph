// Node search & picker

let pickedNodeIds = new Set();

// Simple search: highlights matching nodes
function onNodeSearch() {
  const query = document.getElementById('nodeSearch').value.trim().toLowerCase();
  const results = document.getElementById('nodeSearchResults');
  if (!query || !currentData) {
    results.innerHTML = '';
    if (cy) cy.elements().unselect();
    return;
  }

  const matches = currentData.nodes.filter(function (n) {
    return n.id.toLowerCase().includes(query) || (n.label && n.label.toLowerCase().includes(query));
  });

  if (!matches.length) {
    results.innerHTML = '<span style="color:#e74c3c">No matches</span>';
    if (cy) cy.elements().unselect();
    return;
  }

  results.innerHTML = matches.slice(0, 12).map(function (m) {
    return '<div style="padding:2px 0;cursor:pointer;" onclick="focusNode(\'' + m.id.replace(/'/g, "\\'") + '\')">' +
      '<span style="color:#2c3e50">' + m.label + '</span></div>';
  }).join('') + (matches.length > 12
    ? '<div style="color:#95a5a6">... and ' + (matches.length - 12) + ' more</div>'
    : '');

  if (cy) {
    cy.elements().unselect();
    matches.forEach(function (m) { cy.$id(m.id).select(); });
  }
}

// Focus on a node (center + zoom + select)
function focusNode(nodeId) {
  if (!cy) return;
  const node = cy.$id(nodeId);
  if (!node || node.empty()) return;
  cy.elements().unselect();
  node.select();
  cy.animate({
    center: { eles: node },
    zoom: 1.5,
  }, { duration: 400, easing: 'ease-in-out' });
}

// Node picker
function onPickerSearch() {
  const query = document.getElementById('nodePicker').value.trim().toLowerCase();
  const dd = document.getElementById('pickerDropdown');
  if (!currentData) { dd.classList.remove('open'); return; }

  const matches = currentData.nodes.filter(function (n) {
    return !pickedNodeIds.has(n.id) &&
      (query === '' || n.id.toLowerCase().includes(query) || (n.label && n.label.toLowerCase().includes(query)));
  });

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

function closePickerDropdown() {
  document.getElementById('pickerDropdown').classList.remove('open');
}

function selectPickedInCy() {
  if (!cy) return;
  cy.elements().unselect();
  pickedNodeIds.forEach(function (id) { cy.$id(id).select(); });
}

function pickNode(nodeId) {
  pickedNodeIds.add(nodeId);
  document.getElementById('nodePicker').value = '';
  closePickerDropdown();
  renderPickedTags();
  selectPickedInCy();
}

function unpickNode(nodeId) {
  pickedNodeIds.delete(nodeId);
  renderPickedTags();
  selectPickedInCy();
}

function clearPickedNodes() {
  pickedNodeIds.clear();
  renderPickedTags();
  document.getElementById('connInfo').style.display = 'none';
  if (cy) cy.elements().unselect();
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

// Show edges between all currently picked nodes
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

  info.style.display = 'block';
  info.textContent = fEdges.length
    ? fNodes.length + ' nodes, ' + fEdges.length + ' direct edge(s) shown.'
    : 'No direct edges between selected nodes.';

  // Render the sub-graph using a force-directed layout (Cytoscape's 'cose')
  // since there's no natural hierarchy in an arbitrary node subset.
  render({ nodes: fNodes, edges: fEdges, _rawData: currentData._rawData }, {
    name: 'cose',
    padding: 30,
    animate: false,
    fit: true,
    idealEdgeLength: 140,
    nodeRepulsion: 4000,
    gravity: 0.3,
  });
}

// Show connected nodes when long-pressing a node
let focusModeActive = false;

function focusConnectedNodes(nodeId) {
  if (!cy || !currentData) return;

  const connectedIds = new Set();
  connectedIds.add(nodeId);
  currentData.edges.forEach(function (e) {
    if (e.from === nodeId) connectedIds.add(e.to);
    if (e.to === nodeId) connectedIds.add(e.from);
  });

  // Hide nodes not in the connected set
  cy.nodes().forEach(function (n) {
    if (connectedIds.has(n.id())) n.removeClass('hidden');
    else n.addClass('hidden');
  });

  // Hide edges not touching the focal node
  cy.edges().forEach(function (e) {
    const touchesFocal = e.source().id() === nodeId || e.target().id() === nodeId;
    if (touchesFocal) e.removeClass('hidden');
    else e.addClass('hidden');
  });

  focusModeActive = true;
}