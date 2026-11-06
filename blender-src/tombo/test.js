// node test.js <html> <outdir>   — a bot that circles perched dragonflies and taps them when dizzy
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error') errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1200);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(1500);
  const T = await pg.evaluate(() => __T.toFrame());
  const scr = (x, y) => [T.OX + x * T.S, T.OY + y * T.S];
  let shots = 0, ang = 0; const t0 = Date.now();
  await pg.mouse.move(...scr(560, 1000)); await pg.mouse.down();
  while (Date.now() - t0 < 64000) {
    const st = await pg.evaluate(() => ({ ph: __T.G.phase, f: __T.G.flies.filter(f => f.st === 'perch' || f.st === 'dizzy').map(f => ({ c: __T.center(f), st: f.st, dz: f.dz, k: f.kind })) }));
    if (st.ph !== 'play') break;
    if (!st.f.length) { await pg.waitForTimeout(100); continue }
    const f = st.f.find(q => q.st === 'dizzy') || st.f.sort((a, b) => b.dz - a.dz)[0];
    if (f.st === 'dizzy') { await pg.mouse.move(...scr(f.c.x, f.c.y), { steps: 6 }); await pg.waitForTimeout(120); continue }
    for (let k = 0; k < 10; k++) { ang += 0.22; const R = 110 * (f.k === 'oniyanma' ? 1.45 : 1); await pg.mouse.move(...scr(f.c.x + Math.cos(ang) * R, f.c.y + Math.sin(ang) * R)); await pg.waitForTimeout(16) }
    if (shots < 2 && f.dz > .5) { await pg.screenshot({ path: out + `/c2-play${shots}.png` }); shots++ }
  }
  await pg.mouse.up();
  await pg.waitForTimeout(2500); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(await pg.evaluate(() => ({ score: __T.G.score, bag: __T.G.bag }))));
  console.log('errs', errs); await b.close();
})();
