// node test.js <html> <outdir>   — a real tap on the right card + a foul, then a bot with human-ish reaction times
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn');
  const S = 390 / 720, OY = (780 - 1280 * S) / 2;
  await pg.waitForFunction(() => __T.G.phase === 'read' && __T.G.shown >= 3 && !__T.G.kara);
  await pg.screenshot({ path: out + '/c2-read.png' });
  const t = await pg.evaluate(() => { const i = __T.cardIdx(__T.G.line); const c = __T.G.table[i]; return [c.x, c.y] });
  await pg.mouse.click(t[0] * S, t[1] * S + OY); await pg.waitForTimeout(300);
  await pg.screenshot({ path: out + '/c3-took.png' });
  console.log('after real tap', JSON.stringify(await pg.evaluate(() => ({ me: __T.G.me, cat: __T.G.cat }))));
  await pg.evaluate(() => { const T = __T, G = T.G; let tgt = null;
    (function bot() { if (G.phase === 'read' && G.shown >= 1) { if (tgt == null) tgt = { at: G.pt + 1.4 + Math.random() * 2.2 }; if (G.pt > tgt.at && !G.kara) { const i = T.cardIdx(G.line); if (i >= 0) T.tapCard(i) } } else tgt = null; requestAnimationFrame(bot) })() });
  await pg.waitForFunction(() => __T.G.paw && __T.G.paw.t > .2 && __T.G.paw.t < .32, null, { timeout: 60000 }).catch(() => {}); await pg.screenshot({ path: out + '/c4-paw.png' });
  await pg.waitForFunction(() => __T.G.phase === 'end', null, { timeout: 120000 }); await pg.waitForTimeout(2300);
  await pg.screenshot({ path: out + '/c5-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ me: __T.G.me, cat: __T.G.cat, kara: __T.G.karaN, fast: __T.G.fast }))));
  console.log('errs', errs); await b.close();
})();
