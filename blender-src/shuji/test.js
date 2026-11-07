// node test.js <html> <outdir> [skill] — a real mouse stroke, then a bot that traces each model stroke with noise
// (skill 1 = near-perfect tracing, lower = wobblier and slower)
const { chromium } = require('playwright');
(async () => {
  const [html, out, skill] = process.argv.slice(2); const K = +(skill || 1);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(e.stack.slice(0,300))); pg.on('console', m => { if (m.type() === 'error' && !/ERR_/.test(m.text())) errs.push('c:' + m.text()) });
  await pg.goto('file://' + html); await pg.waitForTimeout(1500);
  await pg.screenshot({ path: out + '/c1-title.png' });
  await pg.click('#startBtn'); await pg.waitForTimeout(700);
  await pg.screenshot({ path: out + '/c2-start.png' });
  const box = await pg.evaluate(() => { const r = document.getElementById('cv').getBoundingClientRect(); const S = Math.min(r.width / 720, Math.max(r.height / 1280, r.width / 720 * .92)); return { S, ox: r.left + (r.width - 720 * S) / 2, oy: r.top + (r.height - 1280 * S) / 2 } });
  const s0 = await pg.evaluate(() => __T.G.strokes[0].filter((p, i) => i % 3 === 0));
  await pg.mouse.move(box.ox + s0[0].x * box.S, box.oy + s0[0].y * box.S); await pg.mouse.down();
  for (const p of s0) await pg.mouse.move(box.ox + p.x * box.S, box.oy + p.y * box.S, { steps: 2 });
  await pg.mouse.up(); console.log('mouse stroke acc', await pg.evaluate(() => __T.G.accs));
  await pg.evaluate((K) => { const T = __T, G = T.G; let st = null, i = 0, wait = 0; const err = (1 - K) * 50, sp = Math.round(2 + K * 2);
    let ox = 0, oy = 0;
    (function bot() { if (G.phase === 'play' && G.between <= 0 && G.si < G.strokes.length) {
        if (wait > 0) wait--; else { const s = G.strokes[G.si];
          if (!st) { st = s; i = 0; ox = (Math.random() - .5) * err; oy = (Math.random() - .5) * err; T.down(s[0].x + ox, s[0].y + oy) }
          else { i = Math.min(s.length - 1, i + sp); ox += (Math.random() - .5) * err * .2; oy += (Math.random() - .5) * err * .2; T.move(s[i].x + ox, s[i].y + oy);
            if (i >= s.length - 1) { T.up(); st = null; wait = 10 + (1 - K) * 30 } } } }
      else if (st) { st = null }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(6000); console.log('errs early', errs); await pg.waitForTimeout(6000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase === 'end', null, { timeout: 120000 }).catch(() => {});
  const st = await pg.evaluate(() => ({ ph: __T.G.phase, score: __T.G.score, chars: __T.G.list, accs: __T.G.charScores, hana: __T.G.hana }));
  await pg.waitForTimeout(2600); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(st)); console.log('errs', errs); await b.close();
})();
