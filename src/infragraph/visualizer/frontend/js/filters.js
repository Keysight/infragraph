// Filter panel

let filterPanelOpen = false;

function toggleFilterPanel() {
  filterPanelOpen = !filterPanelOpen;
  document.getElementById('filterPanel').style.display = filterPanelOpen ? 'flex' : 'none';
  document.getElementById('filterToggle').classList.toggle('active', filterPanelOpen);
  if (!filterPanelOpen) closePickerDropdown();
}

// Rebuilds the node-type and edge-type checkbox lists from current graph data.
// Also resets search input and picked node state.
function populateFilters(data) {
  if (!data) return;

  function build(items, checkboxContainerId, countBadgeId) {
    const freq = new Map();
    items.forEach(function (t) { t = t || 'unknown'; freq.set(t, (freq.get(t) || 0) + 1); });
    const el = document.getElementById(checkboxContainerId);
    el.innerHTML = '';
    Array.from(freq.keys()).sort().forEach(function (t) {
      const lbl = document.createElement('label');
      lbl.innerHTML = '<input type="checkbox" checked value="' + t + '"> ' + t + ' (' + freq.get(t) + ')';
      el.appendChild(lbl);
    });
    document.getElementById(countBadgeId).textContent = '(' + freq.size + ')';
  }

  build(data.nodes.map(function (n) { return n.deviceType; }), 'nodeTypeFilters', 'nodeTypeCount');
  build(data.edges.map(function (e) { return e.linkType || e.title; }), 'edgeTypeFilters', 'edgeTypeCount');

  document.getElementById('nodeSearch').value = '';
  document.getElementById('nodeSearchResults').innerHTML = '';
  document.getElementById('connInfo').style.display = 'none';
  clearPickedNodes();
}

function toggleAllNodeTypes(checked) {
  document.querySelectorAll('#nodeTypeFilters input[type=checkbox]')
    .forEach(function (cb) { cb.checked = checked; });
}

function toggleAllEdgeTypes(checked) {
  document.querySelectorAll('#edgeTypeFilters input[type=checkbox]')
    .forEach(function (cb) { cb.checked = checked; });
}

// Re-renders the graph using only the checked node/edge types
function applyFilters() {
  if (!currentData) return;

  const selTypes = new Set(
    Array.from(document.querySelectorAll('#nodeTypeFilters input:checked')).map(function (cb) { return cb.value; })
  );
  const selLinks = new Set(
    Array.from(document.querySelectorAll('#edgeTypeFilters input:checked')).map(function (cb) { return cb.value; })
  );

  const fNodes = currentData.nodes.filter(function (n) { return selTypes.has(n.deviceType || 'unknown'); });
  const visIds = new Set(fNodes.map(function (n) { return n.id; }));
  const fEdges = currentData.edges.filter(function (e) {
    return visIds.has(e.from) && visIds.has(e.to) && selLinks.has(e.linkType || e.title || 'unknown');
  });

  const layout = navigationStack.length <= 1 ? fabricLayout : internalLayout;
  render({ nodes: fNodes, edges: fEdges, _rawData: currentData._rawData }, layout);
}

function resetFilters() {
  if (!currentData) return;
  populateFilters(currentData);
  const layout = navigationStack.length <= 1 ? fabricLayout : internalLayout;
  render(currentData, layout);
}