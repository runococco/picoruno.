// 全ゲーム：起動→プレイ（bot）→結果→シェア画像→もういちど→やめる、をエラーなく通るか
const {chromium}=require('playwright');
const slugs=process.argv.slice(2);
(async()=>{const b=await chromium.launch();
  for(const slug of slugs){const p=await b.newPage({viewport:{width:390,height:740}});const errs=[];
    p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
    await p.goto('file://'+require('path').resolve(__dirname,'../../'+slug+'.html'));await p.waitForTimeout(400);
    await p.click('#startBtn');
    await p.evaluate(()=>{window.__bi=setInterval(()=>{if(__P.state==='play'&&__G.__bot)__G.__bot(__P)},40)});
    const t0=Date.now();while(Date.now()-t0<12000){if(await p.evaluate(()=>__P.state)!=='play'&&Date.now()-t0>4000)break;await p.waitForTimeout(250)}
    const st1=await p.evaluate(()=>__P.state);await p.evaluate(()=>__P.end());await p.waitForTimeout(3800);
    const res=await p.evaluate(()=>({state:__P.state,score:document.getElementById('rScore').textContent,rank:document.getElementById('rRank').textContent,x:document.getElementById('xBtn').href.length}));
    const share=await p.evaluate(()=>P.shareImage().toDataURL().length);
    await p.click('#againBtn');await p.waitForTimeout(3600);const st2=await p.evaluate(()=>__P.state);
    await p.waitForTimeout(1500);if(await p.isVisible('#quitBtn'))await p.click('#quitBtn');await p.waitForTimeout(300);const st3=await p.evaluate(()=>__P.state);
    console.log(slug.padEnd(11),'after-play',st1,'| result',res.state,res.score,res.rank,'| share',share>20000?'ok':'SMALL','| again',st2,'| quit',st3,'| errors',errs.length?[...new Set(errs)].slice(0,3):'none');
    await p.close()}
  await b.close()})();
