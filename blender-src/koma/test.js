// node test.js <html> <outdir> [skill]  — launches on GO, then dashes at the cat's top (skill 0..1 = aim + timing)
const { chromium } = require('playwright');
(async () => {
  const [html, out, sk] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(1200);
  const S = 390 / 720, OY = (780 - 1280 * S) / 2;
  await pg.mouse.move(360 * S, 1100 * S + OY); await pg.mouse.down(); await pg.mouse.move(380 * S, 1240 * S + OY, { steps: 5 });
  await pg.screenshot({ path: out + '/c2-aim.png' });
  await pg.waitForFunction(() => __T.G.st >= __T.GO_AT, null, { timeout: 5000 }); await pg.mouse.up(); await pg.waitForTimeout(900);
  await pg.screenshot({ path: out + '/c3-fight.png' });
  await pg.evaluate((K) => { const T = __T, G = T.G; let w = 0, rel = 0;
    (function bot() { if (G.phase === 'play') { if (G.stage === 'ready') { if (!G.drag && !G.launch && G.st > 1) T.down({ x: 360, y: 1100 }), T.move({ x: 360 + (Math.random() - .5) * 80, y: 1260 }), rel = __T.GO_AT + (Math.random() - .5) * (1 - K) * .8; if (G.drag && G.st >= rel) T.up() }
        else if (G.stage === 'fight' && --w <= 0) { w = Math.round(50 - K * 12); const me = G.tops[0], op = G.tops[1]; if (me && op) { const e = (1 - K) * 1.2, a = Math.atan2(op.y - me.y, op.x - me.x) + (Math.random() - .5) * e; T.down({ x: me.x + Math.cos(a) * 100, y: me.y + Math.sin(a) * 100 }); T.up() } } } requestAnimationFrame(bot) })() }, +(sk || .6));
  await pg.waitForFunction(() => __T.G.foe >= 1 || __T.G.lives < 3, null, { timeout: 60000 }).catch(() => {}); await pg.waitForTimeout(400); await pg.screenshot({ path: out + '/c4-bout.png' });
  await pg.waitForFunction(() => __T.G.phase !== 'play', null, { timeout: 240000 }).catch(() => {}); await pg.waitForTimeout(2200);
  await pg.screenshot({ path: out + '/c5-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, w: __T.G.wins, l: __T.G.lives, n: __T.G.nice, o: __T.G.outs, t: __T.G.t.toFixed(0) }))));
  console.log('errs', errs); await b.close();
})();
