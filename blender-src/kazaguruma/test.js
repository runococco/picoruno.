// node test.js <html> <outdir> [skill] — a real swipe, then a bot (skill 1 = tops up the slowest pinwheel to mid-green, holds off right before a gust)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(500);
  await pg.mouse.move(150, 250); await pg.mouse.down(); await pg.mouse.move(250, 350, { steps: 8 }); await pg.mouse.up(); await pg.waitForTimeout(300); await pg.screenshot({ path: out + '/c2-swipe.png' });
  await pg.evaluate((K) => { const T = __T, G = T.G; let cd = 0, lt = performance.now();
    (function bot(n) { const dt = Math.min(.05, (n - lt) / 1000) || .016; lt = n; cd -= dt; if (G.phase === 'play' && cd <= 0) {
      const ws = G.wheels.filter(w => w.on && w.down <= 0).sort((a, b) => a.s - b.s); const w = ws[0];
      const target = K >= .8 ? (G.gust && !G.gust.hit ? .5 : .78) : .78 + (Math.random() - .5) * (1 - K) * 1.2;
      if (w && w.s < target) { T.swipe(w.x - 30, w.y - 30, w.x + 30, w.y + 30); cd = .12 + (1 - K) * .35 } }
      requestAnimationFrame(bot) })(performance.now()) }, K);
  await pg.waitForFunction(() => __T.G.t > 32, null, { timeout: 60000 }).catch(() => {}); await pg.screenshot({ path: out + '/c3-five.png' });
  await pg.waitForFunction(() => __T.G.gust && __T.G.gust.t > .6, null, { timeout: 30000 }).catch(() => {}); await pg.screenshot({ path: out + '/c4-gust.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 60000 }).catch(() => {});
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c5-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: Math.floor(__T.G.score), all: __T.G.allT.toFixed(0), stop: __T.G.stopN, fly: __T.G.flyN, lives: __T.G.lives, t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
