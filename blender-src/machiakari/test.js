const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  await pg.goto('file://' + html); await pg.waitForTimeout(1200);
  await pg.screenshot({ path: out + '/m1-title.png' });
  const gen = await pg.evaluate(() => { const { makeLevel, mulberry, LEVELS, minSolution } = __T; let fail = 0, n = 0, pars = [];
    for (let s = 0; s < 40; s++) LEVELS.forEach(([N, K], i) => { const lv = makeLevel(N, K, mulberry(s * 1000 + i)); n++; if (!lv) { fail++; return } if (lv.par !== K) pars.push([N,K,lv.par]); });
    return { n, fail, offPar: pars.slice(0,5), offCount: pars.length } });
  console.log('gen', JSON.stringify(gen));
  await pg.click('#dailyBtn'); await pg.waitForTimeout(900);
  await pg.screenshot({ path: out + '/m2-l1.png' });
  // real click on the solution house
  const tgt = await pg.evaluate(() => { const s = __T.minSolution(__T.G.lit, __T.G.lv.nb)[0]; const p = __T.G.lv.P[s]; const q = __T.scr(p.x, p.y, .4); const r = document.getElementById('cv').getBoundingClientRect(); return { x: q.x + r.left, y: q.y + r.top, s } });
  await pg.mouse.click(tgt.x, tgt.y); await pg.waitForTimeout(500);
  console.log('after click', await pg.evaluate(() => ({ phase: __T.G.phase, lit: __T.G.lit, moves: __T.G.moves })));
  await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/m3-win.png' });
  for (let i = 1; i < 8; i++) {
    await pg.click('#nextBtn'); await pg.waitForTimeout(700);
    if (i === 3 || i === 7) await pg.screenshot({ path: out + `/m4-l${i + 1}.png` });
    if (i === 7) { // try undo/reset then hint
      const h = await pg.evaluate(() => { const p = __T.G.lv.P[0]; const q = __T.scr(p.x, p.y, .4); const r = document.getElementById('cv').getBoundingClientRect(); return { x: q.x + r.left, y: q.y + r.top } });
      await pg.mouse.click(h.x, h.y); await pg.waitForTimeout(400); await pg.click('#undoBtn'); await pg.waitForTimeout(300);
      await pg.click('#pauseBtn'); await pg.click('#hintBtn'); await pg.waitForTimeout(300);
      await pg.screenshot({ path: out + '/m5-hint.png' });
      console.log('undo ok', await pg.evaluate(() => ({ moves: __T.G.moves, same: __T.G.lit.join() === __T.G.lv.start.join(), hint: __T.G.hint })));
    }
    await pg.evaluate(() => __T.solve()); await pg.waitForTimeout(1700);
  }
  await pg.click('#nextBtn'); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/m6-result.png' });
  console.log('final', await pg.evaluate(() => ({ phase: __T.G.phase, stars: __T.G.stars })), 'errs', errs);
  await b.close();
})();
