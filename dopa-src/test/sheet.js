// 全タイトル画面＋シェア画像のサムネを1枚にまとめる
const {chromium}=require('playwright');const fs=require('fs');
const slugs=process.argv.slice(2);
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:390,height:800}});
  for(const s of slugs){await p.goto('file://'+require('path').resolve(__dirname,'../../'+s+'.html'));await p.waitForTimeout(500);
    await p.screenshot({path:`/tmp/claude-0/shots/t-${s}.png`});
    const d=await p.evaluate(()=>{__P.score=1234;if(__G.slug==='pancake'){__P.score=24;const L=[{x:120,w:180}];let w=180,x=120;for(let i=0;i<24;i++){const c=Math.random()*10-5;w=Math.max(60,w-Math.abs(c)*.6);x+=c*.3;L.push({x,w})}__G.st.L=L}return P.shareImage().toDataURL('image/png')});fs.writeFileSync(`/tmp/claude-0/shots/s-${s}.png`,Buffer.from(d.split(',')[1],'base64'))}
  await b.close()})();
