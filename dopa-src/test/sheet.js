// 全タイトル画面＋シェア画像のサムネを1枚にまとめる
const {chromium}=require('playwright');const fs=require('fs');
const slugs=process.argv.slice(2);
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:390,height:800}});
  for(const s of slugs){await p.goto('file://'+require('path').resolve(__dirname,'../../'+s+'.html'));await p.waitForTimeout(500);
    await p.screenshot({path:`/tmp/claude-0/shots/t-${s}.png`});
    const d=await p.evaluate(()=>{__P.score=1234;return P.shareImage().toDataURL('image/png')});fs.writeFileSync(`/tmp/claude-0/shots/s-${s}.png`,Buffer.from(d.split(',')[1],'base64'))}
  await b.close()})();
