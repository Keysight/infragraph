// Navigation: breadcrumb trail, back button, drill-down

var navigationStack = [];    // [{file, label}]
var breadcrumb, btnBack, btnCompress;

// Compressed views: for fabrics with more than Visualizer.COMPRESS_MIN_HOSTS
// hosts the generator emits a ladder infrastructure_compressed_1.json ..
// infrastructure_compressed_<k>.json, each merging more equivalent nodes
// than the last (the final rung is one node per tier). The header toggle
// switches the infrastructure view to the ladder and the slider picks the
// rung; the breadcrumb is unchanged.
var INFRA_FILE = 'infrastructure.json';
var compressedMode = false;
var compressionLevel = null;      // current rung, initialised from the generator's default

function compressedFile(level) {
    return 'infrastructure_compressed_' + level + '.json';
}

// Available rungs, ascending.
function compressionLevels() {
    var levels = [];
    if (typeof GRAPH_DATA === 'undefined') return levels;
    for (var k = 1; GRAPH_DATA[compressedFile(k)]; k++) levels.push(k);
    return levels;
}

function compressedAvailable() {
    return compressionLevels().length > 0;
}

function defaultCompressionLevel() {
    var levels = compressionLevels();
    for (var i = 0; i < levels.length; i++) {
        if (GRAPH_DATA[compressedFile(levels[i])].default) return levels[i];
    }
    return levels.length ? levels[0] : null;
}

// Data file to load for a logical view: the infrastructure view resolves to
// the selected compressed rung while the toggle is on.
function resolveViewFile(file) {
    if (file === INFRA_FILE && compressedMode && compressedAvailable()) {
        if (compressionLevel === null) compressionLevel = defaultCompressionLevel();
        return compressedFile(compressionLevel);
    }
    return file;
}

function reloadInfrastructure() {
    if (navigationStack.length === 1) {
        navigationStack.pop();
        navigateTo(INFRA_FILE, 'Infrastructure');
    } else {
        updateCompressButton();
    }
}

function toggleCompressed() {
    if (!compressedAvailable()) return;
    compressedMode = !compressedMode;
    reloadInfrastructure();
}

function setCompressionLevel(level) {
    var levels = compressionLevels();
    if (levels.indexOf(level) === -1) return;
    compressionLevel = level;
    if (compressedMode) reloadInfrastructure();
    else updateCompressButton();
}

// Text for a rung: "×5.2 · 160 nodes"
function compressionRatioText(level) {
    var view = GRAPH_DATA[compressedFile(level)];
    if (!view) return '';
    var ratio = view.ratio || (GRAPH_DATA[INFRA_FILE].nodes.length / view.nodes.length);
    return '\u00d7' + Number(ratio).toFixed(1) + ' \u00b7 ' + view.nodes.length + ' nodes';
}

function updateCompressButton() {
    if (!btnCompress) return;
    var onInfra = navigationStack.length === 1;
    var available = compressedAvailable();
    btnCompress.disabled = !(available && onInfra);
    btnCompress.classList.toggle('active', compressedMode && available);

    var rack = document.getElementById('rackControls');
    if (rack) {
        var cur = navigationStack[navigationStack.length - 1];
        var inRack = !!(cur && isRackFile(cur.file));
        rack.style.display = inRack ? 'flex' : 'none';
        if (inRack) {
            document.getElementById('rackHops').value = rackHops;
            document.getElementById('rackHopsLabel').textContent =
                rackHops + (rackHops === 1 ? ' hop' : ' hops');
        }
    }

    var controls = document.getElementById('compressControls');
    if (!controls) return;
    var show = compressedMode && available && onInfra;
    controls.style.display = show ? 'flex' : 'none';
    if (show) {
        var levels = compressionLevels();
        if (compressionLevel === null) compressionLevel = defaultCompressionLevel();
        var hopSlider = document.getElementById('rackHops');
    if (hopSlider) {
        hopSlider.addEventListener('input', function () {
            document.getElementById('rackHopsLabel').textContent = this.value + (this.value === '1' ? ' hop' : ' hops');
        });
        hopSlider.addEventListener('change', function () { setRackHops(parseInt(this.value)); });
    }

    var slider = document.getElementById('compressSlider');
        slider.min = levels[0];
        slider.max = levels[levels.length - 1];
        slider.value = compressionLevel;
        document.getElementById('compressRatio').textContent = compressionRatioText(compressionLevel);
    }
}

// ---------------------------------------------------------------------------
// Rack views
//
// A group node in a compressed view stands for several real instances. Opening
// one used to jump straight into the shared device template, skipping the layer
// that answers "what is in this box and where does it plug in". A rack view is
// that missing layer: the group's actual members plus the switches they uplink
// to, taken from infrastructure.json and laid out fresh. Clicking a server
// inside it then drills into that device's internals as before.
//
// Views are built on demand and keyed by a synthetic file id so the breadcrumb,
// back button and the rest of navigateTo work unchanged.

var RACK_PREFIX = 'rack:';
var RACK_MAX_NODES = 250;         // above this a rack view is too slow to be worth opening
var rackHops = 1;                 // how many hops of surrounding fabric to include
var rackViews = {};               // synthetic file id -> { members, label, kind }
var rackBaseIndex = null;         // lazily built adjacency over infrastructure.json

function isRackFile(file) {
    return typeof file === 'string' && file.indexOf(RACK_PREFIX) === 0;
}

// Only bottom-tier groups open as racks. Switch groups keep the old behaviour of
// drilling into the shared device template, because every switch in a group is
// an instance of the same device and seeing 512 identical copies tells you
// nothing that the template does not.
function isRackGroup(node) {
    return !!(node && node.members && (node.kind === 'rack' || node.kind === 'pod'));
}

// Size of the one-hop view this group would produce: its members plus the
// switches they uplink to, both counted by the generator.
function rackViewSize(node) {
    return (node.members ? node.members.length : 0) + (node.rackCount || 0);
}

// At the highest compression rungs a single node stands for every server in the
// fabric, and expanding it would build thousands of nodes and take a minute or
// more to lay out. Those are left closed.
function canOpenRack(node) {
    return isRackGroup(node) && rackViewSize(node) <= RACK_MAX_NODES;
}

function rackTitle(node) {
    if (node.kind === 'rack') return 'Rack ' + node.label;
    if (node.kind === 'pod') return 'Pod ' + node.label;
    return node.label;
}

// Called when a group node is clicked. Registers the view, then navigates.
function openRack(node) {
    if (!isRackGroup(node) || !node.members.length) return;
    if (!canOpenRack(node)) {
        if (typeof showToast === 'function') {
            showToast(node.label + ' holds ' + node.members.length +
                      ' servers, too many to open. Lower the compression to open a smaller group.');
        }
        return;
    }
    var file = RACK_PREFIX + node.id;
    rackViews[file] = { members: node.members.slice(), label: node.label, kind: node.kind };
    navigateTo(file, rackTitle(node));
}

function rackIndex() {
    if (rackBaseIndex) return rackBaseIndex;
    var base = GRAPH_DATA[INFRA_FILE];
    var adj = new Map();
    base.edges.forEach(function (e) {
        if (!adj.has(e.from)) adj.set(e.from, []);
        if (!adj.has(e.to)) adj.set(e.to, []);
        adj.get(e.from).push(e.to);
        adj.get(e.to).push(e.from);
    });
    rackBaseIndex = { base: base, adj: adj };
    return rackBaseIndex;
}

// Members plus everything within `hops` hops of them, as a standalone view.
// Precomputed coordinates are stripped so vis lays the small graph out itself;
// the fabric-wide positions would scatter five servers across half a mile.
function buildRackView(file, hops) {
    var spec = rackViews[file];
    if (!spec) return null;
    var idx = rackIndex(), adj = idx.adj;

    var keep = new Set(spec.members);
    var frontier = spec.members.slice();
    var reachedHops = 0;
    for (var h = 0; h < hops; h++) {
        var next = new Set();
        frontier.forEach(function (id) {
            (adj.get(id) || []).forEach(function (m) { if (!keep.has(m)) next.add(m); });
        });
        if (!next.size) break;
        // Adding this ring would make the view too slow, so stop one ring short.
        if (keep.size + next.size > RACK_MAX_NODES) break;
        next.forEach(function (m) { keep.add(m); });
        frontier = Array.from(next);
        reachedHops = h + 1;
    }

    var inRack = new Set(spec.members);
    var nodes = idx.base.nodes.filter(function (n) { return keep.has(n.id); })
        .map(function (n) {
            var copy = {};
            for (var k in n) copy[k] = n[k];
            copy.inRack = inRack.has(n.id);
            return copy;
        });
    var edges = idx.base.edges.filter(function (e) { return keep.has(e.from) && keep.has(e.to); });

    // The fabric-wide coordinates would scatter these across half a mile, so
    // give the subgraph its own placement at a scale that suits it.
    layoutSubgraph(nodes, edges, 170);

    return {
        nodes: nodes, edges: edges, rackView: true,
        rackMemberCount: spec.members.length,
        rackHopsShown: reachedHops, rackHopsAsked: hops
    };
}

// Client-side twin of Visualizer._compute_layout in visualize.py. Rack views
// are assembled in the browser, so they need the same placement the generator
// gives the fabric: rows taken from each node's level, ordered by the mean
// position of their neighbours one level down, pushed apart to respect the
// spacing, then re-centred. vis's own hierarchical engine was tried here first
// and stretched larger views by more than an order of magnitude.
function layoutSubgraph(nodes, edges, spacing) {
    spacing = spacing || 170;
    var adj = new Map(), order = new Map();
    nodes.forEach(function (n, i) { adj.set(n.id, []); order.set(n.id, i); });
    edges.forEach(function (e) {
        if (adj.has(e.from) && adj.has(e.to)) {
            adj.get(e.from).push(e.to);
            adj.get(e.to).push(e.from);
        }
    });

    var levelOf = new Map(), byLevel = new Map();
    var minLevel = Infinity;
    nodes.forEach(function (n) { if (n.level < minLevel) minLevel = n.level; });
    nodes.forEach(function (n) {
        var lv = (n.level || 0) - minLevel;
        levelOf.set(n.id, lv);
        if (!byLevel.has(lv)) byLevel.set(lv, []);
        byLevel.get(lv).push(n);
    });

    var levels = Array.from(byLevel.keys()).sort(function (a, b) { return a - b; });
    var x = new Map();
    levels.forEach(function (lv, li) {
        var row = byLevel.get(lv), bary = new Map();
        if (li === 0) {
            row.sort(function (a, b) { return order.get(a.id) - order.get(b.id); });
            row.forEach(function (n, i) { bary.set(n.id, (i - (row.length - 1) / 2) * spacing); });
        } else {
            row.forEach(function (n) {
                var below = adj.get(n.id)
                    .filter(function (m) { return x.has(m); })
                    .map(function (m) { return x.get(m); });
                var mean = 0;
                below.forEach(function (v) { mean += v; });
                bary.set(n.id, below.length ? mean / below.length : 0);
            });
            row.sort(function (a, b) {
                return (bary.get(a.id) - bary.get(b.id)) || (order.get(a.id) - order.get(b.id));
            });
        }
        var pos = [];
        row.forEach(function (n) {
            var px = bary.get(n.id);
            if (pos.length && px < pos[pos.length - 1] + spacing) px = pos[pos.length - 1] + spacing;
            pos.push(px);
        });
        var sumB = 0, sumP = 0;
        row.forEach(function (n) { sumB += bary.get(n.id); });
        pos.forEach(function (p) { sumP += p; });
        var shift = (sumB - sumP) / row.length;
        row.forEach(function (n, i) { x.set(n.id, pos[i] + shift); });
    });

    var widest = 0;
    byLevel.forEach(function (row) { widest = Math.max(widest, row.length); });
    var gaps = Math.max(levels.length - 1, 1);
    var sep = Math.round(Math.min(Math.max((widest - 1) * spacing / (2 * gaps), 220), 4000));
    nodes.forEach(function (n) {
        n.x = Math.round(x.get(n.id));
        n.y = -levelOf.get(n.id) * sep;
    });
}

function setRackHops(hops) {
    rackHops = hops;
    var cur = navigationStack[navigationStack.length - 1];
    if (cur && isRackFile(cur.file)) {          // rebuild the view we are looking at
        navigationStack.pop();
        navigateTo(cur.file, cur.label);
    }
}

function initNavigation() {
    breadcrumb = document.getElementById('breadcrumb');
    btnBack = document.getElementById('btn-back');
    btnBack.addEventListener('click', goBack);
    btnCompress = document.getElementById('btn-compress');
    if (btnCompress) btnCompress.addEventListener('click', toggleCompressed);

    var slider = document.getElementById('compressSlider');
    if (slider) {
        // live ratio preview while dragging, reload on release
        slider.addEventListener('input', function () {
            document.getElementById('compressRatio').textContent = compressionRatioText(parseInt(this.value));
        });
        slider.addEventListener('change', function () { setCompressionLevel(parseInt(this.value)); });
    }

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Backspace' && !e.target.matches('input, textarea')) {
            e.preventDefault();
            goBack();
        }
    });
}

function navigateTo(file, label) {
    showLoading();

    fetchGraphData(resolveViewFile(file)).then(function (data) {
        navigationStack.push({ file: file, label: label });
        updateBreadcrumb();
        updateBackButton();
        updateCompressButton();

        largeGraphOverride = null;   // each view decides its own render mode
        currentData = prepareData(data);
        render(currentData, optionsForData(currentData));

        if (data.rackView && data.rackHopsShown < data.rackHopsAsked && typeof showToast === 'function') {
            showToast('Showing ' + data.rackHopsShown + ' hop' + (data.rackHopsShown === 1 ? '' : 's') +
                      '; going further would make this view too large to draw quickly.');
        }

        if (typeof populateFilters === 'function') populateFilters(currentData);
        if (typeof syncLargeGraphToggle === 'function') syncLargeGraphToggle();

        hideLoading();
    }).catch(function (err) {
        console.error('Failed to load graph data:', err);
        alert('Failed to load: ' + file + '\n\n' + err.message);
        hideLoading();
    });
}

function goBack() {
    if (navigationStack.length <= 1) return;
    navigationStack.pop();
    var prev = navigationStack[navigationStack.length - 1];
    navigationStack.pop();
    navigateTo(prev.file, prev.label);
}

function updateBreadcrumb() {
    breadcrumb.innerHTML = '';
    navigationStack.forEach(function (item, idx) {
        if (idx > 0) {
            var sep = document.createElement('span');
            sep.className = 'crumb-sep';
            sep.textContent = '\u203A';
            breadcrumb.appendChild(sep);
        }
        var crumb = document.createElement('span');
        crumb.className = 'crumb';
        crumb.textContent = item.label;
        crumb.dataset.file = item.file;
        if (idx === navigationStack.length - 1) {
            crumb.classList.add('active');
            (function (f, l) {
                crumb.style.cursor = 'pointer'; 
                crumb.addEventListener('click', function () {
                    navigationStack.pop();
                    navigateTo(f, l);
                });
            })(item.file, item.label);
        } else {
            (function (i, f, l) {
                crumb.addEventListener('click', function () {
                    while (navigationStack.length > i) navigationStack.pop();
                    navigateTo(f, l);
                });
            })(idx, item.file, item.label);
        }
        breadcrumb.appendChild(crumb);
    });
}

function updateBackButton() {
    btnBack.disabled = navigationStack.length <= 1;
}