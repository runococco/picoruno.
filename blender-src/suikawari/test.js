// node test.js <html> <outdir>   — real drag-walk + button swing in round 1, then a bot that follows the cat's hints
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(1200);
  await pg.screenshot({ path: out + '/c2-look.png' });
  await pg.waitForTimeout(1900); await pg.screenshot({ path: out + '/c3-spin.png' });
  await pg.waitForFunction(() => __T.G.phase === 'walk');
  const S = 390 / 720, OY = (780 - 1280 * S) / 2, f = (x, y) => [x * S, y * S + OY];
  const m = await pg.evaluate(() => ({ m: __T.G.melon, p: __T.G.p }));
  // walk with real drags toward the melon in 3 strokes
  for (let k = 0; k < 3; k++) { const [x0, y0] = f(360, 700); await pg.mouse.move(x0, y0); await pg.mouse.down(); const dx = (m.m.x - m.p.x) / 3, dy = (m.m.y - m.p.y) / 3; const [x1, y1] = f(360 + dx, 700 + dy); await pg.mouse.move(x1, y1, { steps: 10 }); await pg.mouse.up(); await pg.waitForTimeout(700) }
  await pg.waitForTimeout(600); await pg.screenshot({ path: out + '/c4-walk.png' });
  console.log('pos', JSON.stringify(await pg.evaluate(() => ({ m: __T.G.melon, p: __T.G.p, hint: __T.G.hint }))));
  const [bx, by] = f(360, 1186); await pg.mouse.click(bx, by); await pg.waitForTimeout(900);
  await pg.screenshot({ path: out + '/c5-reveal.png' });
  console.log('r1', JSON.stringify(await pg.evaluate(() => ({ g: __T.G.grade, d: Math.round(__T.G.dist), s: __T.G.score }))));
  // bot: follow hints (direction words) in small steps, swing on "そこ"
  await pg.evaluate(() => { const T = __T, G = T.G; let wait = 0;
    (function bot() { if (G.phase === 'walk' && G.hint && --wait <= 0) { wait = 10; if (G.hint.a == null) T.swing(); else { const near = /ちょっと|すこし/.test(G.hint.s) ? 25 : /ずーっと/.test(G.hint.s) ? 120 : 60; T.walk(Math.sin(G.hint.a) * near, -Math.cos(G.hint.a) * near) } }
      requestAnimationFrame(bot) })() });
  await pg.waitForFunction(() => __T.G.phase === 'end', null, { timeout: 120000 }); await pg.waitForTimeout(2200);
  await pg.screenshot({ path: out + '/c6-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ s: __T.G.score, res: __T.G.res, best: Math.round(__T.G.best) }))));
  console.log('errs', errs); await b.close();
})();
