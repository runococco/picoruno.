// node test.js <html> <outdir>
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = [];
  pg.on('pageerror', e => errs.push('pageerror ' + e.message));
  pg.on('console', m => { if (m.type() === 'error') errs.push('console ' + m.text()) });
  await pg.goto('file://' + html);
  await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/t1-title.png' });
  // generator sanity: many seeds, all sizes, exact tiling
  const gen = await pg.evaluate(() => {
    const { generate, mulberry, STAGES, shapeOf, TYPES } = window.__T; let bad = 0, n = 0, pieces = [];
    for (let s = 0; s < 300; s++) for (const [W, H] of STAGES) {
      const sol = generate(W, H, mulberry(s * 13 + W * H)); n++;
      const g = Array.from({ length: H }, () => Array(W).fill(0));
      for (const p of sol) for (const [x, y] of shapeOf(p.type, p.rot).cells) { const X = p.gx + x, Y = p.gy + y; if (X < 0 || Y < 0 || X >= W || Y >= H) bad++; else g[Y][X]++ }
      if (!g.every(r => r.every(v => v === 1))) bad++;
      if (sol.every(p => p.type === 'karaage')) bad++;
      if (W === 5 && H === 5) pieces.push(sol.length);
    }
    return { n, bad, avg55: pieces.reduce((a, b) => a + b, 0) / pieces.length, max55: Math.max(...pieces) };
  });
  console.log('generator', JSON.stringify(gen));
  await pg.click('#dailyBtn');
  await pg.waitForTimeout(900);
  await pg.screenshot({ path: out + '/t2-stage1.png' });
  // real drag of the first tray piece onto its solution spot via mouse
  const info = await pg.evaluate(() => {
    const st = __T.G.stage; const p = st.pieces[0]; const r = document.getElementById('cv').getBoundingClientRect();
    return { r: { x: r.left, y: r.top }, p: { x: p.x, y: p.y, rot: p.rot, sol: p.sol, type: p.type } };
  });
  console.log('piece0', JSON.stringify(info.p));
  // tap to rotate until it matches the solution rotation
  for (let i = 0; i < 4; i++) {
    const rot = await pg.evaluate(() => __T.G.stage.pieces[0].rot);
    const T = await pg.evaluate(() => { const p = __T.G.stage.pieces[0]; return __T.TYPES[p.type].cells.length });
    if (rot === info.p.sol.rot || T === 1) break;
    const pos = await pg.evaluate(() => { const p = __T.G.stage.pieces[0]; return { x: p.x, y: p.y } });
    await pg.mouse.click(info.r.x + pos.x, info.r.y + pos.y); await pg.waitForTimeout(250);
  }
  const tgt = await pg.evaluate(() => {
    const p = __T.G.stage.pieces[0], sh = __T.shapeOf(p.type, p.rot); const L = { S: 0 };
    return { from: { x: p.x, y: p.y }, sh, sol: p.sol, rot: p.rot };
  });
  const L = await pg.evaluate(() => { const st = __T.G.stage; const p = st.pieces[0]; const sh = __T.shapeOf(p.type, p.rot);
    // compute screen centre of solution
    const cv = document.getElementById('cv'); return null });
  const dest = await pg.evaluate(() => { const p = __T.G.stage.pieces[0]; const sh = __T.shapeOf(p.type, p.sol.rot); return window.__T.dest ? null : null });
  await pg.mouse.move(info.r.x + tgt.from.x, info.r.y + tgt.from.y); await pg.mouse.down();
  const d2 = await pg.evaluate(() => { const p = __T.G.stage.pieces[0]; const sh = __T.shapeOf(p.type, p.rot); const l = __T.L; return { x: l.gx + (p.sol.gx + sh.w / 2) * l.S, y: l.gy + (p.sol.gy + sh.h / 2) * l.S, grabx: p.x, graby: p.y } });
  for (let i = 1; i <= 12; i++) { await pg.mouse.move(info.r.x + tgt.from.x + (d2.x - tgt.from.x) * i / 12, info.r.y + tgt.from.y + (d2.y - tgt.from.y) * i / 12); await pg.waitForTimeout(16) }
  await pg.screenshot({ path: out + '/t3-dragging.png' });
  await pg.mouse.up(); await pg.waitForTimeout(400);
  const placed = await pg.evaluate(() => { const p = __T.G.stage.pieces[0]; return { place: p.place, rot: p.rot, sol: p.sol } });
  console.log('after drag', JSON.stringify(placed));
  await pg.screenshot({ path: out + '/t4-placed.png' });
  // finish all five with solveAll + hint check on stage 2
  for (let i = 0; i < 5; i++) {
    if (i === 1) { await pg.click('#hintBtn'); await pg.waitForTimeout(300); await pg.screenshot({ path: out + '/t5-hint.png' }) }
    await pg.evaluate(() => __T.solveAll());
    await pg.waitForTimeout(i === 4 ? 900 : 700);
    if (i === 2) await pg.screenshot({ path: out + '/t6-stamp.png' });
    await pg.waitForTimeout(i === 2 ? 1100 : 1400);
    if (i === 2) await pg.screenshot({ path: out + '/t7-lid.png' });
    await pg.waitForTimeout(1200);
    const st = await pg.evaluate(() => ({ idx: __T.G.idx, phase: __T.G.phase }));
    console.log('stage', i, JSON.stringify(st));
    if (i === 3) await pg.screenshot({ path: out + '/t8-stage5.png' });
  }
  await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/t9-result.png' });
  console.log('errors', errs);
  await b.close();
})();
