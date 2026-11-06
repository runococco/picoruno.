// node test.js <html> <outdir>   — real crank circle + bottle tap + real pour drag, then a bot serves the remaining customers
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(800);
  const S = 390 / 720, OY = (780 - 1280 * S) / 2, f = (x, y) => [x * S, y * S + OY];
  // real crank: circles around the wheel clockwise
  const [wx, wy] = f(592, 516), R = 70 * S * 1.6;
  await pg.mouse.move(wx + R, wy); await pg.mouse.down();
  for (let k = 1; k <= 48; k++) { const a = k / 12 * Math.PI * 2 / 4 * 1; await pg.mouse.move(wx + Math.cos(k / 8 * Math.PI) * R, wy + Math.sin(k / 8 * Math.PI) * R) }
  await pg.mouse.up();
  console.log('h after 3 turns', await pg.evaluate(() => Math.round(__T.G.h)));
  await pg.screenshot({ path: out + '/c2-shave.png' });
  const [bx, by] = f(100, 1180); await pg.mouse.click(bx, by);
  const [mx, my] = f(300, 840); await pg.mouse.move(mx, my); await pg.mouse.down();
  for (let k = 0; k < 20; k++) { const [x, y] = f(300 + (k % 5) * 30, 860 - Math.floor(k / 5) * 22); await pg.mouse.move(x, y, { steps: 2 }) }
  await pg.screenshot({ path: out + '/c3-pour.png' }); await pg.mouse.up();
  console.log('eval', JSON.stringify(await pg.evaluate(() => __T.evaluate())));
  const [sx, sy] = f(630, 1140); await pg.mouse.click(sx, sy); await pg.waitForTimeout(500);
  await pg.screenshot({ path: out + '/c4-serve.png' });
  await pg.waitForTimeout(2200);
  // bot: shave to target, then paint every cell with its wanted syrup
  const bot = async (sloppy) => pg.evaluate(async (sloppy) => {
    const T = __T, G = T.G, o = G.order, tgt = T.SIZES[o.size].h * (1 + (sloppy ? (Math.random() - .5) * .3 : 0));
    while (G.h < tgt) { T.crank(.2); await new Promise(r => setTimeout(r, 8)) }
    const sm = T.SM, sy = G.h / (sm.base[1] - sm.top[1]);
    for (let r = 0; r < 10; r++) for (let q = 0; q < 16; q++) {
      const cx = 36 + (q + .5) * 248 / 16, cy = 80 + (r + .5) * 16, u = (cx - sm.base[0]) / sm.halfw, v = (sm.base[1] - cy) / (sm.base[1] - sm.top[1]); const k = T.want(o, u, v); if (k < 0) continue;
      if (sloppy && Math.random() < .15) continue; T.pick(k); T.paintAt(T.MB[0] + (cx - sm.base[0]) * T.MSX, T.MB[1] + (cy - sm.base[1]) * sy) }
    const e = T.evaluate(); T.serve(); return { pat: o.pat, size: o.size, h: Math.round(G.h), e }
  }, sloppy);
  for (let i = 0; i < 5; i++) { await pg.waitForFunction(() => __T.G.phase === 'play' || __T.G.phase === 'end'); if (await pg.evaluate(() => __T.G.phase) === 'end') break;
    console.log(JSON.stringify(await bot(i % 2 === 1))); if (i === 2) { await pg.waitForTimeout(300); await pg.screenshot({ path: out + '/c5-bot.png' }) } await pg.waitForTimeout(2300) }
  await pg.waitForTimeout(2500); await pg.screenshot({ path: out + '/c6-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ ph: __T.G.phase, s: __T.G.score, res: __T.G.res }))));
  console.log('errs', errs); await b.close();
})();
