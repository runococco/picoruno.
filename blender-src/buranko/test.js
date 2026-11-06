// node test.js <html> <outdir> [jumpAngle] [sloppy] — taps, then a bot that pumps at the bottom and jumps forward at the given angle
const { chromium } = require('playwright');
(async () => {
  const [html, out, ang, sl] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(500);
  await pg.mouse.click(100, 650); await pg.waitForTimeout(300);
  await pg.evaluate(([A, SL]) => { const T = __T, G = T.G; let lastP = -1;
    (function bot() { if (G.phase === 'play' && G.state === 'swing') { const tol = SL ? .2 : .08; if (Math.abs(G.th) < tol && G.t - lastP > .5) { lastP = G.t; T.pump() }
        const amp = Math.acos(Math.max(-1, Math.min(1, Math.cos(G.th) - G.om * G.om * 230 / (2 * 880))));
        if ((amp > 1.08 || G.pumpT < 1.4) && G.om > 0 && G.th > A - (SL ? .15 : .03) && G.th < A + (SL ? .25 : .05)) T.jump() } requestAnimationFrame(bot) })() }, [+(ang || .6), +(sl || 0)]);
  await pg.waitForTimeout(4500); await pg.screenshot({ path: out + '/c2-swing.png' });
  await pg.waitForFunction(() => __T.G.state === 'fly', null, { timeout: 20000 }).catch(() => {}); await pg.waitForTimeout(250); await pg.screenshot({ path: out + '/c3-fly.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 120000 }).catch(() => {});
  await pg.waitForTimeout(2200); await pg.screenshot({ path: out + '/c5-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, tot: __T.G.total.toFixed(1), best: __T.G.best.toFixed(2), st: __T.G.stars, gr: __T.G.greats, marks: __T.G.marks.map(m => ((m.x - 248) / 90).toFixed(1)) }))));
  console.log('errs', errs); await b.close();
})();
