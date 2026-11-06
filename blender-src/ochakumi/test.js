// node test.js <html> <outdir>   — a bot that does round-robin pours
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error') errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1200);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(600);
  const T = await pg.evaluate(() => __T.toFrame());
  const scr = (x, y) => [T.OX + x * T.S, T.OY + y * T.S];
  for (let round = 0; round < 3; round++) {
    let k = 0, dir = 1, shot = 0;
    for (let guard = 0; guard < 80; guard++) {
      const st = await pg.evaluate(() => ({ ph: __T.G.phase, pot: __T.G.pot, n: __T.G.cups.length, rims: __T.G.cups.map(q => __T.rim(q).x) }));
      if (st.ph !== 'play') break;
      const x = st.rims[k];
      let [a, c] = scr(x, 900); await pg.mouse.move(a, c); await pg.mouse.down();
      await pg.waitForTimeout(260);
      await pg.mouse.move(a + 1, c);
      await pg.waitForTimeout(240);
      if (round === 2 && shot === 0 && guard > 4) { await pg.screenshot({ path: out + '/c2-pour.png' }); shot = 1 }
      await pg.mouse.up(); await pg.waitForTimeout(300);
      k += dir; if (k >= st.n) { k = st.n - 1; dir = -1 } else if (k < 0) { k = 0; dir = 1 }
    }
    await pg.waitForTimeout(1500);
    await pg.screenshot({ path: out + `/c3-round${round}.png` });
    const sc = await pg.evaluate(() => ({ scores: __T.G.scores, cups: __T.G.cups.map(q => [q.v.toFixed(2), (q.m / q.v).toFixed(2)]), spilled: __T.G.spilled.toFixed(3) }));
    console.log(JSON.stringify(sc));
    await pg.click('#nextBtn'); await pg.waitForTimeout(600);
  }
  await pg.waitForTimeout(800); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log('errs', errs); await b.close();
})();
