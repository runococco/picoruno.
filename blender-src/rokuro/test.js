// node test.js <html> <outdir> [skill] — a real mouse drag, then a bot that sweeps a finger up and down the dashed target
// edge (skill = how closely it follows the edge)
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
  await pg.mouse.move(box.ox + 520 * box.S, box.oy + 850 * box.S); await pg.mouse.down(); await pg.mouse.move(box.ox + 430 * box.S, box.oy + 800 * box.S, { steps: 10 }); await pg.waitForTimeout(400);
  await pg.screenshot({ path: out + '/c2-start.png' }); await pg.mouse.up();
  await pg.evaluate((K) => { const T = __T, G = T.G; let i = 0, dir = 1, on = false; const err = (1 - K) * 40, off = (Math.random() - .5) * err;
    (function bot() { if (G.phase === 'play' && !G.fired && G.between <= 0) { if (!on) { T.down(360 + G.tgt[0], T.rowY(0)); on = true }
        i += dir * .5; if (i >= T.N - 1) { i = T.N - 1; dir = -1 } if (i <= 0) { i = 0; dir = 1 } const k = Math.round(i);
        T.move(360 + G.tgt[k] + off + Math.sin(G.t * 7) * err * .5, T.rowY(k)) } else if (on) { T.up(); on = false }
      requestAnimationFrame(bot) })() }, K);
  await pg.waitForTimeout(10000); await pg.screenshot({ path: out + '/c3-mid.png' });
  await pg.waitForFunction(() => __T.G.phase === 'end', null, { timeout: 120000 }).catch(() => {});
  const st = await pg.evaluate(() => ({ ph: __T.G.phase, score: __T.G.score, accs: __T.G.accs }));
  await pg.waitForTimeout(2600); await pg.screenshot({ path: out + '/c4-result.png' });
  console.log(JSON.stringify(st)); console.log('errs', errs); await b.close();
})();
