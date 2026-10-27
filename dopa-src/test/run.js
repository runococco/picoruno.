// usage: node test/run.js slug [playMs]  — タイトル→プレイ（ランダム入力 or GAME.__bot）→結果 をスクショ、コンソールエラーを出す
const {chromium}=require('playwright');
const slug=process.argv[2],playMs=+(process.argv[3]||6000),out=process.env.OUT||'/tmp/claude-0/shots';
(async()=>{
  require('fs').mkdirSync(out,{recursive:true});
  const b=await chromium.launch();const p=await b.newPage({viewport:{width:390,height:844},deviceScaleFactor:2,hasTouch:false});
  const errs=[];p.on('pageerror',e=>errs.push('pageerror '+e.message));p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
  await p.goto('file://'+require('path').resolve(__dirname,'../../'+slug+'.html'));await p.waitForTimeout(800);
  await p.screenshot({path:`${out}/${slug}-1title.png`});
  await p.click('#startBtn');await p.waitForTimeout(3300);
  const t0=Date.now();let shot=false;
  const botMs=+(process.env.BOTMS||30);await p.evaluate(ms=>{if(__G.__bot)window.__bi=setInterval(()=>{if(__P.state==='play')__G.__bot(__P)},ms)},botMs);
  while(Date.now()-t0<playMs){
    const st=await p.evaluate(()=>__P.state);if(st!=='play')break;
    const hasBot=await p.evaluate(()=>!!__G.__bot);
    if(hasBot){await p.waitForTimeout(100)}
    else{const box=await p.locator('#cv').boundingBox();const x=box.x+Math.random()*box.width,y=box.y+box.height*(.2+Math.random()*.75);
      await p.mouse.move(x,y);await p.mouse.down();await p.mouse.move(x+(Math.random()-.5)*200,y+(Math.random()-.5)*200,{steps:5});await p.mouse.up();await p.waitForTimeout(60)}
    if(!shot&&Date.now()-t0>playMs*(+process.env.SHOTAT||.5)){await p.screenshot({path:`${out}/${slug}-2play.png`});shot=true}
  }
  if(!shot)await p.screenshot({path:`${out}/${slug}-2play.png`});
  await p.evaluate(()=>__P.end());await p.waitForTimeout(2600);
  await p.screenshot({path:`${out}/${slug}-3result.png`});
  const sc=await p.evaluate(()=>__P.score);
  console.log(slug,'score',sc,'errors',errs.length?[...new Set(errs)].slice(0,5):'none');
  await b.close();
})();
