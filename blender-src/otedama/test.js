// node test.js <html> <outdir> [err]  — real taps, then a bot that taps the landing side with a timing error of +-err seconds
const { chromium } = require('playwright');
(async () => {
  const [html, out, err] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(400);
  for (let k = 0; k < 40; k++) { const s = await pg.evaluate(() => { const G = __T.G; const b = G.bags.find(b => b.state === 'air' && Math.abs(b.tLand - G.t) < .06); return b ? b.to : -1 }); if (s >= 0) { await pg.mouse.click(s ? 300 : 90, 600); await pg.waitForTimeout(120) } else await pg.waitForTimeout(25) }
  console.log('real taps', await pg.evaluate(() => [__T.G.catches, __T.G.lives]));
  await pg.screenshot({ path: out + '/c2-play.png' });
  await pg.evaluate((E) => { const T = __T, G = T.G; const plan = new Map();
    (function bot() { if (G.phase === 'play') { for (const b of G.bags) { if (b.state !== 'air') continue; const key = b.id + ':' + b.tLand; if (!plan.has(key)) plan.set(key, b.tLand + (Math.random() * 2 - 1) * E);
        if (G.t >= plan.get(key) && !b.done2) { b.done2 = 1; T.tap(b.to) } } for (const b of G.bags) if (b.state === 'held') b.done2 = 0 } requestAnimationFrame(bot) })() }, +(err || .1));
  await pg.waitForFunction(() => __T.G.want >= 4, null, { timeout: 90000 }).catch(() => {}); await pg.screenshot({ path: out + '/c3-four.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 120000 }).catch(() => {});
  await pg.waitForTimeout(2600);
  await pg.screenshot({ path: out + '/c5-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, c: __T.G.catches, mc: __T.G.maxCombo, mb: __T.G.maxBags, p: __T.G.perfects, t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
