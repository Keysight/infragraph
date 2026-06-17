// Color helpers for vis.js node/edge styling

function hexToRgb(hex) {
    var m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return m ? { r: parseInt(m[1], 16), g: parseInt(m[2], 16), b: parseInt(m[3], 16) } : null;
}

function rgbToHex(r, g, b) {
    return '#' + [r, g, b].map(function (x) { return x.toString(16).padStart(2, '0'); }).join('');
}

function lightenColor(hex, amount) { 
    amount = amount || 0.25;
    var rgb = hexToRgb(hex);
    if (!rgb) return hex;
    return rgbToHex(
        Math.min(255, Math.round(rgb.r + (255 - rgb.r) * amount)),
        Math.min(255, Math.round(rgb.g + (255 - rgb.g) * amount)),
        Math.min(255, Math.round(rgb.b + (255 - rgb.b) * amount))
    );
}


function darkenColor(hex, amount) {
    amount = amount || 0.3;
    var rgb = hexToRgb(hex);
    if (!rgb) return hex;
    return rgbToHex(
        Math.round(rgb.r * (1 - amount)),
        Math.round(rgb.g * (1 - amount)),
        Math.round(rgb.b * (1 - amount))
    );
}

// Build vis.js color object for a node based on its type and drillable status
function buildNodeColor(n) {
    var bg = n.color || '#888'; 
    return {
        background: bg,
        border: n.drillable ? '#FFFFFF' : darkenColor(bg),
        highlight: { background: lightenColor(bg), border: '#FFFFFF' },
        hover: { background: lightenColor(bg), border: n.drillable ? '#FFFFFF' : lightenColor(bg) }
    };
}

function getNodeSize(n) {
    var sizes = { host: 30, switch: 25, cpu: 18, xpu: 20, nic: 16, port: 10, device: 22, custom: 14 };
    return sizes[n.type] || 16;
}