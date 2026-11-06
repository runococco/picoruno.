// node test.js <html> <outdir> [gain] [lag]  — a real drag, then a bot that moves the paw toward the swinging bead (gain 0 = hands off)
const { chromium } = require('playwright');
(async () => {
  const [html, out, gain, lag] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(600);
  await pg.mouse.move(200, 500); await pg.mouse.down(); await pg.mouse.move(260, 500, { steps: 8 }); await pg.mouse.up();
  console.log('real', await pg.evaluate(() => Math.round(__T.G.tx)));
  await pg.evaluate(([K, LAG]) => { const T = __T, G = T.G; const hist = [];
    (function bot() { if (G.phase === 'play' && K > 0) { const [bx] = T.bead(); hist.push([bx, G.om]); const [hb, ho] = hist.length > LAG ? hist[hist.length - 1 - LAG] : hist[0];
        if (hist.length > 60) hist.shift(); G.tx = Math.max(320, Math.min(650, G.hx + .6 * (hb - G.hx) + K * ho * 175 * .25 + .03 * (500 - G.hx))) } requestAnimationFrame(bot) })() }, [+(gain || 1), +(lag || 6)]);
  await pg.waitForFunction(() => __T.G.state === 'burn' && __T.G.ph >= 2, null, { timeout: 30000 }).catch(() => {}); await pg.waitForTimeout(600); await pg.screenshot({ path: out + '/c3-matsuba.png' });
  await pg.waitForFunction(() => __T.G.gust && __T.G.gust.t > .3, null, { timeout: 30000 }).catch(() => {}); await pg.screenshot({ path: out + '/c4-gust.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 150000 }).catch(() => {});
  await pg.waitForTimeout(2400);
  await pg.screenshot({ path: out + '/c5-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: Math.round(__T.G.score), st: __T.G.sticks.map(s => s.ph + ':' + s.t.toFixed(1)) }))));
  console.log('errs', errs); await b.close();
})();
