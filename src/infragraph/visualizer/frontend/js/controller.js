// Controller panel: live sliders for font sizes, node size, layout spacing.

let controlleropen = false;

// Current layout knobs that the spacing/level sliders adjust.
// Initial values match the defaults in network.js.
let _spacingFactor = 1.2;
let _levelMultiplier = 1.0;

function toggleControllerPanel() {
  controlleropen = !controlleropen;
  document.getElementById('controlPanel').style.display = controlleropen ? 'flex' : 'none';
  document.getElementById('controlToggle').classList.toggle('active', controlleropen);
}

// Re-run the current view's layout with the current spacing knobs applied.
function rerunLayout() {
  if (!cy) return;
  const isInfra = navigationStack.length <= 1;
  const base = isInfra ? fabricLayout : internalLayout;

  //for level spacing 
   const wrappedTransform = function (node, pos) {
    const t = base.transform(node, pos);
    return isInfra
      ? { x: t.x, y: t.y * _levelMultiplier }
      : { x: t.x * _levelMultiplier, y: t.y };
  };

  cy.layout(Object.assign({}, base, {
    spacingFactor: _spacingFactor,
    transform: wrappedTransform,
    animate: true,
    animationDuration: 200,
  })).run();
}

document.getElementById('fontslider').addEventListener('input', function () {
  if (!cy) return;
  const size = parseInt(this.value);
  cy.nodes().style('font-size', size);
});

document.getElementById('edgefont').addEventListener('input', function () {
  if (!cy) return;
  const size = parseInt(this.value);
  cy.edges().style('font-size', size);
});

document.getElementById('nodeslider').addEventListener('input', function () {
  if (!cy) return;
  const size = parseInt(this.value);
  cy.nodes().style({ 'width': size, 'height': size });
});

document.getElementById('spaceslider').addEventListener('input', function () {
  // Slider range 100..500 → spacingFactor 0.6..2.5
  const v = parseInt(this.value);
  _spacingFactor = 0.6 + ((v - 100) / 400) * 1.9;
  rerunLayout();
});

document.getElementById('levelslider').addEventListener('input', function () {
  // Slider range 100..500 → multiplier 0.6..2.5
  const v = parseInt(this.value);
  _levelMultiplier = 0.6 + ((v - 100) / 400) * 1.9;
  rerunLayout();
});