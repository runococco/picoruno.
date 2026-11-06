// node test.js <html> <outdir> — a real swipe throw, a simulated sweep of (speed, flatness), then a bot game to the result
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(600);
  await pg.mouse.move(200, 650); await pg.mouse.down(); await pg.waitForTimeout(500); await pg.screenshot({ path: out + '/c2-aim.png' });
  await pg.mouse.move(205, 600, { steps: 2 }); await pg.mouse.move(210, 450, { steps: 4 }); await pg.mouse.up();
  await pg.waitForTimeout(700); await pg.screenshot({ path: out + '/c3-fly.png' });
  console.log('real', await pg.evaluate(() => [__T.G.state, __T.G.stone && __T.G.stone.vy.toFixed(1)]));
  await pg.waitForFunction(() => __T.G.state === 'aim', null, { timeout: 20000 });
  const sweep = await pg.evaluate(() => { const T = __T, G = T.G, res = {}; const saved = { n: G.n, score: G.score, throws: G.throws.slice(), pads: G.pads };
    for (const v of [8, 12, 15, 17, 19, 22]) for (const q of [.3, .6, .85, 1]) { let tot = 0, far = 0, shore = 0;
      for (let k = 0; k < 20; k++) { G.state = 'aim'; G.pads = []; T.throwStone(v, 0, q); const s = G.stone; let n = 0;
        while (G.stone && n++ < 20000) { s.vz -= 9.8 / 600; s.x += s.vx / 600; s.y += s.vy / 600; s.z += s.vz / 600; if (s.y >= 64) { shore++; tot += s.skips; G.stone = null; break } if (s.z <= 0 && s.vz < 0) { s.z = 0; if (!T.contact(s)) { tot += s.skips; far += s.y; break } } } }
      res[v + '/' + q] = (tot / 20).toFixed(1) + ' ' + (far / 20).toFixed(0) + 'm sh' + shore }
    Object.assign(G, { n: saved.n, score: saved.score, throws: saved.throws, pads: saved.pads, state: 'aim', ripples: [], texts: [] }); return res });
  console.log(JSON.stringify(sweep));
  await pg.evaluate(() => { const T = __T, G = T.G; (function bot() { if (G.phase === 'play' && G.state === 'aim' && !G.hold) { G.hold = true; G.botT = .4 + Math.random() } if (G.hold && G.phase === 'play') { G.botT -= 1 / 60; if (G.botT < 0 && Math.abs(G.tilt) < 10) T.throwStone(14 + Math.random() * 6, (Math.random() - .5) * .3, T.quality()) } requestAnimationFrame(bot) })() });
  await pg.waitForFunction(() => __T.G.stone && __T.G.stone.skips >= 3, null, { timeout: 30000 }).catch(() => {}); await pg.screenshot({ path: out + '/c4-skips.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 120000 }).catch(() => {});
  await pg.waitForTimeout(2400); await pg.screenshot({ path: out + '/c5-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, th: __T.G.throws, pad: __T.G.padN, sh: __T.G.shores }))));
  console.log('errs', errs); await b.close();
})();
