// node test.js <html> <outdir>   — real press/release, then a bot that pulls in normal wind and lets go in gusts
const { chromium } = require('playwright');
(async () => {
  const [html, out, mode] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(500);
  await pg.mouse.move(200, 400); await pg.mouse.down(); await pg.waitForTimeout(2200);
  console.log('after hold', await pg.evaluate(() => [__T.G.h.toFixed(2), __T.G.T.toFixed(2)]));
  await pg.screenshot({ path: out + '/c2-pull.png' });
  await pg.mouse.up(); await pg.waitForTimeout(1200);
  console.log('after release', await pg.evaluate(() => [__T.G.h.toFixed(2), __T.G.T.toFixed(2)]));
  await pg.evaluate((mode) => { const T = __T, G = T.G;
    (function bot() { if (G.phase === 'play') { const gust = G.ev && G.ev.type === 'gust' && G.ev.t > G.ev.warn - .2;
        let want = !gust && G.T < .9; if (mode === 'greedy') want = true; if (mode === 'idle') want = Math.random() < .5;
        const b = G.balloons.filter(b => b.x < G.x && b.x > G.x - 260)[0]; if (b && !gust && mode !== 'greedy') { const ty = b.y, ky = T.hY(G.h); if (ky < ty - 30) want = false }
        if (want !== G.pull) T.press(want) } requestAnimationFrame(bot) })() }, mode || 'smart');
  await pg.waitForFunction(() => __T.G.ev && __T.G.ev.type === 'gust' && __T.G.ev.t > 1.4, null, { timeout: 30000 }); await pg.screenshot({ path: out + '/c3-gust.png' });
  await pg.waitForTimeout(9000); await pg.screenshot({ path: out + '/c4-play.png' });
  await pg.evaluate(() => { __T.G.left = 25 }); await pg.waitForTimeout(25000);
  await pg.waitForTimeout(3000);
  await pg.screenshot({ path: out + '/c5-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, bal: __T.G.bal, sn: __T.G.snaps, bo: __T.G.bonks, hi: __T.G.highT.toFixed(1), mh: __T.G.maxH.toFixed(2) }))));
  console.log('errs', errs); await b.close();
})();
