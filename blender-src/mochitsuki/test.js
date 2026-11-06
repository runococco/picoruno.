const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch({args:['--autoplay-policy=no-user-gesture-required']});
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type()==='error') errs.push('c:'+m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1200);
  await pg.screenshot({ path: out + '/m1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(300);
  // autoplayer: tap each P note on time; tap once on the 5th H; skip the 10th P
  await pg.evaluate(() => { const N = __T.CHART.notes; let i = 0, pc = 0, hc = 0; window.__log = [];
    window.__ap = setInterval(() => { const t = __T.now(); while (i < N.length && N[i].t <= t + .004) { const n = N[i++];
      if (n.k === 'P') { pc++; if (pc !== 10) __T.tap() } else { hc++; if (hc === 5) __T.tap() } } }, 4) });
  let shots = [3, 8, 20, 40];
  const t0 = Date.now();
  while (Date.now() - t0 < 75000) {
    const s = await pg.evaluate(() => ({ ph: __T.G.phase, t: __T.now() }));
    if (shots.length && s.t > shots[0]) { await pg.screenshot({ path: out + `/m2-play-${shots[0]}.png` }); shots.shift() }
    if (s.ph !== 'play') break; await pg.waitForTimeout(100);
  }
  const G = await pg.evaluate(() => { const G = __T.G; return { ph: G.phase, score: G.score, g3: G.g3, g2: G.g2, g1: G.g1, miss: G.miss, ouch: G.ouch, max: G.maxCombo } });
  console.log(JSON.stringify(G));
  await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/m3-result.png' });
  console.log('errs', errs);
  await b.close();
})();
