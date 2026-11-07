// node test.js <html> <outdir> [skill] — real taps, then a bot (skill 1 = drops each piece flush into the leftmost gap it fits)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(700);
  await pg.screenshot({ path: out + '/c2-move.png' });
  await pg.mouse.click(200, 400); await pg.waitForTimeout(800); await pg.mouse.click(200, 400); await pg.waitForTimeout(500); await pg.screenshot({ path: out + '/c3-two.png' });
  await pg.evaluate((K) => { const T = __T, G = T.G; let tgt = null;
    (function bot() { if (G.phase === 'play' && G.state === 'move' && G.cur) { const c = G.cur;
      if (tgt === null) { const g = T.gaps().find(([a, b]) => b - a >= c.w - 2); tgt = g ? g[0] + c.w / 2 + (Math.random() * 2 - 1) * (1 - K) * 40 + (Math.random() * 2 - 1) * 3 : c.x; tgt = Math.max(T.L0 + c.w / 2 + 1, Math.min(T.L1 - c.w / 2 - 1, tgt)) }
      if (Math.abs(c.x - tgt) < 8 && G.stT > .2) { T.drop(); tgt = null } } else tgt = null;
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForFunction(() => __T.G.ln >= 2 && __T.G.hung.length >= 4, null, { timeout: 90000 }).catch(() => {}); await pg.screenshot({ path: out + '/c4-line3.png' });
  await pg.waitForFunction(() => __T.G.state === 'full', null, { timeout: 60000 }).catch(() => {}); await pg.waitForTimeout(300); await pg.screenshot({ path: out + '/c5-full.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 200000 }).catch(() => {});
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c6-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, ln: __T.G.ln, it: __T.G.itemN, fit: __T.G.fitN, fills: __T.G.fills.map(f => f.toFixed(2)), lives: __T.G.lives, t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
