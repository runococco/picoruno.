const { chromium, devices } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ ...devices['iPhone 13'] });
  const pg = await ctx.newPage(); const errs=[];
  pg.on('pageerror', e => errs.push(e.message));
  await pg.goto('file://' + process.argv[2]); await pg.waitForTimeout(1200);
  await pg.tap('#freeBtn'); await pg.waitForTimeout(900);
  const cdp = await ctx.newCDPSession(pg);
  const r = await pg.evaluate(() => { const c = document.getElementById('cv').getBoundingClientRect(); const p = __T.G.stage.pieces.find(p=>__T.TYPES[p.type].cells.length>1); const sh=__T.shapeOf(p.type,p.rot); return { ox: c.left, oy: c.top, x: p.x, y: p.y, id:p.id, gx: __T.L.gx, gy: __T.L.gy, S: __T.L.S, w:sh.w,h:sh.h } });
  const pt = (x, y) => [{ x: r.ox + x, y: r.oy + y }];
  // tap to rotate
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: pt(r.x, r.y) });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await pg.waitForTimeout(300);
  const rot = await pg.evaluate(id => __T.G.stage.pieces.find(p=>p.id===id).rot, r.id);
  // drag into box top-left
  const p2 = await pg.evaluate(id => { const p=__T.G.stage.pieces.find(p=>p.id===id); const sh=__T.shapeOf(p.type,p.rot); return {x:p.x,y:p.y,w:sh.w,h:sh.h} }, r.id);
  const tx = r.gx + p2.w * r.S / 2, ty = r.gy + p2.h * r.S / 2;
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: pt(p2.x, p2.y) });
  for (let i = 1; i <= 10; i++) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: pt(p2.x + (tx - p2.x) * i / 10, p2.y + (ty - p2.y) * i / 10) }); await pg.waitForTimeout(16) }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await pg.waitForTimeout(500);
  const res = await pg.evaluate(id => __T.G.stage.pieces.find(p=>p.id===id).place, r.id);
  console.log('rotated', r, '->', rot, 'placed', JSON.stringify(res), 'errs', errs);
  await pg.screenshot({ path: 'shots/touch.png' });
  await b.close();
})();
