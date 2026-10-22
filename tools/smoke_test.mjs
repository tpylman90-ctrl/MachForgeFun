import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { chromium } from 'playwright';

const baseURL = 'http://127.0.0.1:4173/';
const outputDir = 'artifacts';
const browser = await chromium.launch({ headless: true });
const errors = [];

try {
  await mkdir(outputDir, { recursive: true });
  const desktop = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
  desktop.on('pageerror', error => errors.push(error.message));
  const response = await desktop.goto(baseURL, { waitUntil: 'networkidle' });
  assert.equal(response?.status(), 200, 'The app should load successfully');
  await desktop.getByRole('heading', { name: /projectile test range/i }).waitFor();
  await desktop.locator('#range').waitFor();
  await desktop.waitForFunction(() => {
    const image = document.querySelector('.scene canvas');
    return image?.width > 0 && image?.height > 0;
  });

  const scenePixels = await desktop.locator('#range').evaluate(canvas => {
    const context = canvas.getContext('2d');
    const { data } = context.getImageData(12, 12, canvas.width - 24, canvas.height - 24);
    let colors = new Set();
    for (let i = 0; i < data.length; i += 32) colors.add(`${data[i]},${data[i + 1]},${data[i + 2]}`);
    return colors.size;
  });
  assert.ok(scenePixels > 20, `The range should be visibly rendered (sampled ${scenePixels} colors)`);
  await desktop.screenshot({ path: `${outputDir}/machforgefun-smoke-desktop.png`, fullPage: true });

  await desktop.locator('[data-preset="organic"]').click();
  await desktop.locator('#elevation').evaluate(input => {
    input.value = '0';
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await desktop.locator('#velocity').evaluate(input => {
    input.value = '500';
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await desktop.locator('#fire').click();
  await desktop.getByText('ROUND IN FLIGHT').waitFor({ timeout: 5000 });
  await desktop.waitForFunction(
    () => /^\d+\.\d{2} <small>km<\/small>$/.test(document.querySelector('#impact-result')?.innerHTML ?? ''),
    null,
    { timeout: 5000 },
  );
  await desktop.getByText('TEST COMPLETE').waitFor({ timeout: 10000 });

  const mobile = await browser.newPage({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 1,
    isMobile: true,
    hasTouch: true,
  });
  mobile.on('pageerror', error => errors.push(error.message));
  await mobile.goto(baseURL, { waitUntil: 'networkidle' });
  await mobile.getByRole('button', { name: /fire test round/i }).waitFor();
  const hasHorizontalOverflow = await mobile.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  assert.equal(hasHorizontalOverflow, false, 'The mobile layout should not overflow horizontally');
  await mobile.screenshot({ path: `${outputDir}/machforgefun-smoke-mobile.png`, fullPage: true });

  assert.deepEqual(errors, [], `The browser reported JavaScript errors: ${errors.join('; ')}`);
  console.log('Browser smoke test passed: desktop render, projectile selection, firing telemetry, and mobile layout.');
} finally {
  await browser.close();
}
