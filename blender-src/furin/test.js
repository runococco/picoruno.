// node test.js <html> <outdir>   — taps the right chime with real clicks for several rounds (one mistake), then misses on purpose to end
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn');
  const T = await pg.evaluate(() => { const r = document.getElementById('cv').getBoundingClientRect(); const W = r.width, H = r.height, S = Math.min(W / 720, Math.max(H / 1280, W / 720 * .92)); return { S, OX: (W - 720 * S) / 2, OY: (H - 1280 * S) / 2 } });
  const P = (x, y) => [T.OX + x * T.S, T.OY + y * T.S];
  let shots = 0, wrongDone = false, revSeen = 0;
  for (let n = 0; n < 900; n++) {
    const st = await pg.evaluate(() => ({ st: __T.G.st, ph: __T.G.phase, round: __T.G.round, rev: __T.G.rev, e: __T.G.st === 'input' ? __T.expect() : -1 }));
    if (st.ph !== 'play' || st.round > 9) break;
    if (st.st === 'listen' && st.rev && shots < 1) { await pg.waitForTimeout(500); await pg.screenshot({ path: out + '/c2-rev.png' }); shots++ }
    if (st.st === 'input') {
      let k = st.e; if (st.round === 3 && !wrongDone) { k = (k + 1) % 5; wrongDone = true }
      await pg.mouse.click(...P(__XS[k], 420)); await pg.waitForTimeout(160);
      if (n === 30) await pg.screenshot({ path: out + '/c3-input.png' });
    } else await pg.waitForTimeout(120);
  }
  await pg.screenshot({ path: out + '/c3b.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ round: __T.G.round, s: __T.G.score, lives: __T.G.lives, rc: __T.G.revCleared }))));
  for (let n = 0; n < 200; n++) { const st = await pg.evaluate(() => ({ st: __T.G.st, ph: __T.G.phase, e: __T.G.st === 'input' ? __T.expect() : -1 })); if (st.ph !== 'play') break; if (st.st === 'input') { await pg.mouse.click(...P(__XS[(st.e + 2) % 5], 420)) } await pg.waitForTimeout(150) }
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, round: __T.G.round, s: __T.G.score }))));
  console.log('errs', errs); await b.close();
})();
const __XS = [96, 228, 360, 492, 624];
