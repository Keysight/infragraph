// To run this test in chromium browser use the command: npx playwright test --headed --grep @sanity --project chromium 

import { test, expect } from '@playwright/test';

test('test @sanity', async ({ page }) => {
  await page.goto('http://localhost:3000/');
  await expect(page.getByRole('button', { name: '⚙ Filter' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Toggle theme' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Fit to view' })).toBeVisible();
  await expect(page.getByText('Infrastructure')).toBeVisible();
  await page.getByRole('button', { name: '⚙ Filter' }).click();
  await expect(page.locator('#filterPanel')).toMatchAriaSnapshot(`
    - heading "Node Types (1)" [level=5]
    - checkbox "host (1)" [checked]
    - text: host (1)
    - button "All"
    - button "None"
    `);
  await expect(page.locator('#filterPanel')).toMatchAriaSnapshot(`
    - heading "Link Types (0)" [level=5]
    - button "All"
    - button "None"
    `);
  await page.getByRole('button', { name: '✕' }).click();
  await page.getByRole('button', { name: 'Toggle theme' }).click();
  await expect(page.locator('body')).toHaveCSS('background-color', 'rgb(14, 22, 33)');
  await page.getByRole('button', { name: 'Toggle theme' }).click();
  await expect(page.locator('body')).toHaveCSS('background-color', 'rgb(255, 255, 255)');
  await page.locator('canvas').click({
    position: {
      x: 646,
      y: 333
    }
  });
  await expect(page.getByText('Infrastructure')).toBeVisible();
  await expect(page.getByText('dgx_a100[0]')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Back' })).toBeVisible();
  await page.getByRole('button', { name: '⚙ Filter' }).click();
  await expect(page.locator('#filterPanel')).toMatchAriaSnapshot(`
    - heading "Node Types (5)" [level=5]
    - checkbox "cpu (2)" [checked]
    - text: cpu (2)
    - checkbox "device (8)" [checked]
    - text: device (8)
    - checkbox "pcie_slot (8)" [checked]
    - text: pcie_slot (8)
    - checkbox /switch \\(\\d+\\)/ [checked]
    - text: /switch \\(\\d+\\)/
    - checkbox "xpu (8)" [checked]
    - text: xpu (8)
    - button "All"
    - button "None"
    `);
  await expect(page.locator('#filterPanel')).toMatchAriaSnapshot(`
    - heading "Link Types (3)" [level=5]
    - checkbox "cpu_fabric (1)" [checked]
    - text: cpu_fabric (1)
    - checkbox /pcie \\(\\d+\\)/ [checked]
    - text: /pcie \\(\\d+\\)/
    - checkbox /xpu_fabric \\(\\d+\\)/ [checked]
    - text: /xpu_fabric \\(\\d+\\)/
    - button "All"
    - button "None"
    `);
  await page.getByRole('textbox', { name: 'Search & pick nodes...' }).click();
  await page.getByRole('textbox', { name: 'Search & pick nodes...' }).fill('cx');
  await page.getByText('cx5_100gbe[0]').click();
  await page.getByRole('textbox', { name: 'Search & pick nodes...' }).click();
  await page.getByRole('textbox', { name: 'Search & pick nodes...' }).fill('pci');
  await page.getByText('pciesl[0]').click();
  await page.getByRole('button', { name: 'Show Connections' }).click();
  await expect(page.locator('#filterPanel')).toMatchAriaSnapshot(`
    - heading "Select Nodes (2 selected)" [level=5]
    - textbox "Search & pick nodes..."
    - text: cx5_100gbe[0] ✕ pciesl[0] ✕ 2 nodes, 1 direct edge(s) shown.
    - button "Show Connections"
    - button "Clear"
    `);
  await page.getByRole('button', { name: 'Clear' }).click();
  await page.getByRole('button', { name: 'Reset' }).click();
  await page.getByRole('button', { name: '✕' }).click();
  await page.locator('canvas').click({
    position: {
      x: 695,
      y: 334
    }
  });
  await page.getByRole('button', { name: '⚙ Filter' }).click();
  await expect(page.locator('#filterPanel')).toMatchAriaSnapshot(`
    - heading "Node Types (3)" [level=5]
    - checkbox "cpu (1)" [checked]
    - text: cpu (1)
    - checkbox "pcie_endpoint (1)" [checked]
    - text: pcie_endpoint (1)
    - checkbox "port (2)" [checked]
    - text: port (2)
    - button "All"
    - button "None"
    `);
  await expect(page.locator('#filterPanel')).toMatchAriaSnapshot(`
    - heading "Link Types (2)" [level=5]
    - checkbox "pcie_internal (1)" [checked]
    - text: pcie_internal (1)
    - checkbox "serdes (2)" [checked]
    - text: serdes (2)
    - button "All"
    - button "None"
    `);
  await page.getByRole('button', { name: '✕' }).click();
  await page.getByText('dgx_a100[0]').click();
  await page.getByRole('button', { name: '⚙ Filter' }).click();
  await expect(page.locator('#filterPanel')).toMatchAriaSnapshot(`
    - heading "Node Types (5)" [level=5]
    - checkbox "cpu (2)" [checked]
    - text: cpu (2)
    - checkbox "device (8)" [checked]
    - text: device (8)
    - checkbox "pcie_slot (8)" [checked]
    - text: pcie_slot (8)
    - checkbox /switch \\(\\d+\\)/ [checked]
    - text: /switch \\(\\d+\\)/
    - checkbox "xpu (8)" [checked]
    - text: xpu (8)
    - button "All"
    - button "None"
    `);
  await page.getByRole('button', { name: '✕' }).click();
  await page.getByRole('button', { name: 'Back' }).click();
  await page.getByRole('button', { name: '⚙ Filter' }).click();
  await expect(page.locator('#filterPanel')).toMatchAriaSnapshot(`
    - heading "Node Types (1)" [level=5]
    - checkbox "host (1)" [checked]
    - text: host (1)
    - button "All"
    - button "None"
    `);
  await page.getByRole('button', { name: '✕' }).click();
  await expect(page.getByRole('button', { name: '?' })).toBeVisible();
  await page.getByRole('button', { name: '?' }).click();
  await expect(page.locator('#legend')).toMatchAriaSnapshot(`
    - heading "Node Types" [level=4]
    - img
    - text: CPU
    - img
    - text: XPU
    - img
    - text: NIC
    - img
    - text: Switch
    - img
    - text: Port
    - img
    - text: Custom Device
    - img
    - text: Server
    - heading "Interactions" [level=4]
    - text: Click drillable node → explore internals Hover node/edge → view attributes Scroll → zoom in/out Hold a node → see connected nodes
    `);
});