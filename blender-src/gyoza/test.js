// node test.js <html> <outdir> [skill] — real hold/taps, then a bot (skill 1 = releases in the green band, taps each pleat close to its mark)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(500);
  await pg.mouse.move(200, 400); await pg.mouse.down(); await pg.waitForTimeout(700); await pg.screenshot({ path: out + '/c2-scoop.png' }); await pg.waitForTimeout(350); await pg.mouse.up();
  await pg.waitForTimeout(1200); await pg.mouse.click(200, 400); await pg.waitForTimeout(150); await pg.screenshot({ path: out + '/c3-pleat.png' });
  await pg.evaluate((K) => { const T = __T, G = T.G; let tf = null, ta = null;
    (function bot() { if (G.phase === 'play') {
      if (G.state === 'ready') { tf = .78 + (Math.random() * 2 - 1) * (.06 + (1 - K) * .2); T.scoopStart() }
      if (G.state === 'scoop' && G.f >= tf) T.scoopEnd();
      if (G.state === 'pleat') { const nx = T.TICKA.find((a, i) => !G.pleats.some(p => p.i === i) && a < G.ang + .5);
        if (nx !== undefined) { if (ta === null) ta = nx + (Math.random() * 2 - 1) * (T.win() * .5 + (1 - K) * 7); if (G.ang <= ta) { T.pleat(); ta = null } } } else ta = null }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForFunction(() => __T.G.n >= 4 && __T.G.state === 'pleat' && __T.G.pleats.length >= 3, null, { timeout: 60000 }).catch(() => {}); await pg.screenshot({ path: out + '/c4-mid.png' });
  await pg.waitForFunction(() => __T.G.state === 'fry' && __T.G.stT > 1, null, { timeout: 90000 }).catch(() => {}); await pg.screenshot({ path: out + '/c5-fry.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 30000 }).catch(() => {});
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c6-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, perf: __T.G.perfN, fill: __T.G.fillN, full: __T.G.fullN, t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
