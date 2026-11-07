// node test.js <html> <outdir> [skill] — a real tap, then a bot that watches every cracker: presses puffs, flips in the gold band, collects (skill = reaction time + aim of the flip point)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(2500);
  await pg.mouse.click(195, 248); await pg.waitForTimeout(120); await pg.screenshot({ path: out + '/c2-flip.png' });
  await pg.evaluate((K) => { const T = __T, G = T.G; let next = 0; const aimAt = new Map();
    (function bot() { const now = performance.now(); if (G.phase === 'play' && now > next) {
      let act = -1, urg = -1;
      for (let i = 0; i < 6; i++) { const c = G.ck[i]; if (!c || c.st !== 'cook') continue; if (!aimAt.has(c)) aimAt.set(c, .85 + (Math.random() - .5) * .5 * (1 - K));
        const dn = c.lv[c.d], up = c.lv[1 - c.d], tgt = aimAt.get(c);
        if (c.puff && c.puff.p > .25 + (1 - K) * .4) { if (c.puff.p > urg) { urg = c.puff.p + 1; act = i } continue }
        if (dn >= tgt && dn - tgt + 1 > urg) { urg = dn - tgt + 1; act = i } }
      if (act >= 0) { T.tap(act); next = now + 120 + 600 * (1 - K) + Math.random() * 300 * (1 - K) } }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(30000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 120000 }).catch(() => {});
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, done: __T.G.doneN, perf: __T.G.perfN, burn: __T.G.burnN }))));
  console.log('errs', errs); await b.close();
})();
