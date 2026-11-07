// node test.js <html> <outdir> [skill] — real mouse taps on both buttons, then a bot that adds wood when the bath runs cool
// and pours water when it runs hot (skill = how often it checks and how far ahead it looks)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.stack.slice(0, 300))); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(700);
  const box = await pg.evaluate(() => { const r = document.getElementById('cv').getBoundingClientRect(); const S = Math.min(r.width / 720, Math.max(r.height / 1280, r.width / 720 * .92)); return { S, ox: r.left + (r.width - 720 * S) / 2, oy: r.top + (r.height - 1280 * S) / 2 } });
  await pg.mouse.click(box.ox + 550 * box.S, box.oy + 1180 * box.S); await pg.mouse.click(box.ox + 170 * box.S, box.oy + 1180 * box.S);
  console.log('mouse taps f/T', await pg.evaluate(() => [__T.G.f.toFixed(2), __T.G.T.toFixed(1)]));
  await pg.screenshot({ path: out + '/c2-start.png' });
  await pg.evaluate((K) => { const T = __T, G = T.G; let next = 0, lastT = G.T; const lag = (.25 + (1 - K) * .9) * 1000, look = K * 3;
    (function bot() { const now = performance.now(); if (G.phase === 'play' && now > next) { const dT = (G.T - lastT) / (lag / 1000); lastT = G.T; next = now + lag;
        const pred = G.T + dT * look; if (pred > G.c + .6 && G.T > G.c - .2) T.water(); else if (pred < G.c - .2 && G.T < G.c + .3 && G.f < 1.8 + K) T.wood() }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(20000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase === 'end', null, { timeout: 90000 }).catch(() => {});
  const st = await pg.evaluate(() => ({ ph: __T.G.phase, score: __T.G.score, inT: Math.round(__T.G.inT), goku: Math.round(__T.G.gokuT), streak: Math.round(__T.G.maxStreak) }));
  await pg.waitForTimeout(2600); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(st)); console.log('errs', errs); await b.close();
})();
