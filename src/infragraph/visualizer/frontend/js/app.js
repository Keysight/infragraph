// app.js: Global state, render function, and boot
//
// Globals exposed for other modules:
//   currentData, cy : used by filters.js, search.js, controller.js
//   render()        : used by filters.js, search.js
//   navigateTo()    : used by node click handler

var currentData = null;
var cy = null;           // Cytoscape instance 
var loadingEl;
var tooltipEl;

function initApp() {
    loadingEl = document.getElementById('loading');
    tooltipEl = ensureTooltipEl();

    document.getElementById('btn-fit').addEventListener('click', function () {
        if (cy) cy.animate({ fit: { padding: 30 } }, { duration: 400 });
    });

    // Theme toggle: rebuild data so font/stroke colors update everywhere
    document.getElementById('btn-theme').addEventListener('click', function () {
        document.documentElement.classList.toggle('dark');
        if (currentData && currentData._rawData) {
            var isInfra = navigationStack.length === 1;
            currentData = prepareData(currentData._rawData);
            render(currentData, isInfra ? fabricLayout : internalLayout);
        }
    });

    initNavigation();
    navigateTo('infrastructure.json', 'Infrastructure');

    // Legend toggle
    document.getElementById('btn-hint').addEventListener('click', function () {
        var legend = document.getElementById('legend');
        var isVisible = legend.style.display !== 'none';
        legend.style.display = isVisible ? 'none' : 'block';
        this.textContent = isVisible ? '?' : 'x';
    });
}

// Custom hover tooltip 
function ensureTooltipEl() {
    var t = document.getElementById('cy-tooltip');
    if (t) return t;
    t = document.createElement('div');
    t.id = 'cy-tooltip';
    t.className = 'cy-tooltip';
    t.style.display = 'none';
    document.body.appendChild(t);
    return t;
}

function showTooltip(text, evt) {
    if (!text) return;
    tooltipEl.textContent = text;
    tooltipEl.style.display = 'block';
    moveTooltip(evt);
}

function moveTooltip(evt) {
    var x = evt.originalEvent ? evt.originalEvent.clientX : 0;
    var y = evt.originalEvent ? evt.originalEvent.clientY : 0;
    tooltipEl.style.left = (x + 14) + 'px';
    tooltipEl.style.top = (y + 14) + 'px';
}

function hideTooltip() {
    tooltipEl.style.display = 'none';
}

// Render: creates a Cytoscape instance, binds tap/hover events
function render(data, layout) {
    if (cy) { cy.destroy(); cy = null; }
    hideTooltip();

    var container = document.getElementById('graph-container') || document.getElementById('mynetwork');
    if (!container) return;

    cy = cytoscape({
        container: container,
        elements: buildElements(data),
        style: cytoscapeStyle,
        layout: layout,
        webgl: true,
        wheelSensitivity: 0.2,
        minZoom: 0.1,
        maxZoom: 4,
    });

    bindEvents(data);
}

function bindEvents(data) {
    var container = cy.container();
    var clickTimer = null;

    // Hover: tooltip + cursor
    cy.on('mouseover', 'node', function (evt) {
        var n = evt.target;
        container.style.cursor = n.data('drillable') ? 'pointer' : 'default';
        showTooltip(n.data('title') || n.data('label'), evt);
    });
    cy.on('mouseover', 'edge', function (evt) {
        showTooltip(evt.target.data('title') || evt.target.data('label'), evt);
    });
    cy.on('mousemove', 'node, edge', moveTooltip);
    cy.on('mouseout', 'node, edge', function () {
        container.style.cursor = 'default';
        hideTooltip();
    });

    // Long press → focus connected 
    cy.on('taphold', 'node', function (evt) {
        clearTimeout(clickTimer);
        if (typeof focusConnectedNodes === 'function') {
            focusConnectedNodes(evt.target.id());
        }
    });

    // Tap → drill down, with same 300ms debounce as before so it doesn't
    // fire when the user is starting a long press
    cy.on('tap', 'node', function (evt) {
        var node = evt.target;
        clickTimer = setTimeout(function () {
            if (node.data('drillable') && node.data('drillTarget')) {
                navigateTo(node.data('drillTarget'), node.data('label'));
            }
        }, 300);
    });

    // Tap on background → clear selection
    cy.on('tap', function (evt) {
        if (evt.target === cy) cy.elements().unselect();
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