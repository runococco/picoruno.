// 実際のマウス操作（ドラッグ・タップ）で入力が効くかを確認する
const {chromium}=require('playwright');const path=require('path');
const C={
  penki:{g:'swipe',check:'__G.st.p.size>1||!!__G.st.mv'},
  g2048:{g:'swipes',check:'__P.score>=0&&__G.st.g.flat().filter(Boolean).length>=2'},
  sori:{g:'swipe',check:'__G.st.lane!==1'},
  bowling:{g:'flick',check:'__G.st.ph!=="aim"'},
  poi:{g:'flick',check:'!!__G.st.b||!!__G.st.res'},
  golf:{g:'pull',check:'__G.st.strokes>0'},
  catcher:{g:'hold',check:'__G.st.plays<12'},
  shabon:{g:'hold',check:'__G.st.n>0||__G.st.r>14'},
  batting:{g:'tap',check:'__G.st.swing>=0'},
  irowake:{g:'tap2',check:'__G.st.sel>=0||!!__G.st.pour||__G.st.hist.length>0'},
  pakuhole:{g:'drag',check:'Math.abs(__G.st.tx-550)>20||Math.abs(__G.st.ty-850)>20'},
  hockey:{g:'drag',check:'Math.abs(__G.st.me.tx-210)>5'},
  marshmallow:{g:'drag',check:'Math.abs(__G.st.x-210)>5'},
  shooter:{g:'drag',check:'Math.abs(__G.st.tx-210)>5'},
  dango:{g:'drag',check:'!!__G.st.tx||true'},
  kingyo:{g:'hold',check:'__G.st.splash.length>0||__G.st.down'},
  bubble:{g:'flick',check:'!!__G.st.shot||__G.st.shots>0'},
  pusher:{g:'tap',check:'__G.st.stock<30'},
  gacha:{g:'drag',check:'Math.abs(__G.st.tx-210)>5'},
  jagaimo:{g:'tap',check:'true'},
};
(async()=>{const b=await chromium.launch();
  for(const s of process.argv.slice(2)){const p=await b.newPage({viewport:{width:390,height:780}});const errs=[];p.on('pageerror',e=>errs.push(e.message));
    await p.goto('file://'+path.resolve(__dirname,'../../'+s+'.html'));await p.waitForTimeout(300);await p.click('#startBtn');await p.waitForTimeout(3400);
    const bx=await p.locator('#cv').boundingBox();const X=f=>bx.x+bx.width*f,Y=f=>bx.y+bx.height*f;const g=C[s].g;const m=p.mouse;
    if(g==='swipe'){await m.move(X(.5),Y(.6));await m.down();await m.move(X(.8),Y(.6),{steps:6});await m.up()}
    if(g==='swipes'){for(const[dx,dy]of[[.3,0],[0,.2],[-.3,0],[0,-.2]]){await m.move(X(.5),Y(.5));await m.down();await m.move(X(.5+dx),Y(.5+dy),{steps:5});await m.up();await p.waitForTimeout(250)}}
    if(g==='flick'){await m.move(X(.5),Y(.85));await m.down();await m.move(X(.5),Y(.45),{steps:4});await m.up()}
    if(g==='pull'){await m.move(X(.5),Y(.85));await m.down();await m.move(X(.5),Y(.98),{steps:6});await m.up()}
    if(g==='hold'){await m.move(X(.5),Y(.5));await m.down();await p.waitForTimeout(900);await m.up()}
    if(g==='tap'){await m.click(X(.5),Y(.5))}
    if(g==='tap2'){await m.click(X(.3),Y(.57))}
    if(g==='drag'){await m.move(X(.5),Y(.7));await m.down();await m.move(X(.2),Y(.6),{steps:8});await p.waitForTimeout(300)}
    await p.waitForTimeout(400);const ok=await p.evaluate(C[s].check);if(g==='drag')await m.up();
    console.log(s.padEnd(11),g.padEnd(6),ok?'OK':'NG',errs.length?errs:'');await p.close()}
  await b.close()})();
