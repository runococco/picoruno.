// node test.js <html> <outdir> [err] [spam] — real taps, then a bot that jumps so its apex meets the rope (timing error ±err s), or a masher
const { chromium } = require('playwright');
(async () => {
  const [html, out, err, spam] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(300);
  await pg.evaluate(([E, SP]) => { const T = __T, G = T.G; let plan = null;
    (function bot() { if (G.phase === 'play') { if (SP) { if (Math.random() < .25) T.tap() } else { const tp = T.timeToPass(); if (tp > 0 && !plan && tp < .6) plan = G.t + tp - .2 + (Math.random() * 2 - 1) * E;
      if (plan && G.t >= plan) { T.tap(); plan = null; } if (tp > .6) plan = null } } requestAnimationFrame(bot) })() }, [+(err || .05), +(spam || 0)]);
  await pg.waitForTimeout(6000); await pg.screenshot({ path: out + '/c2-wave.png' });
  await pg.waitForFunction(() => __T.G.cats.length >= 2 && __T.G.cats[0].h > 50, null, { timeout: 60000 }).catch(() => {}); await pg.screenshot({ path: out + '/c3-friend.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 200000 }).catch(() => {});
  await pg.waitForTimeout(2600); await pg.screenshot({ path: out + '/c5-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, j: __T.G.jumps, p: __T.G.perfects, run: __T.G.maxRun, per: __T.G.period.toFixed(2), t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
