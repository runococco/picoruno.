// 一覧用サムネ（900x487・タイトル入り・中央寄せ）を書き出す。usage: node test/thumb.js outdir slug...
const {chromium}=require('playwright');const fs=require('fs'),path=require('path');
const [out,...slugs]=process.argv.slice(2);
(async()=>{fs.mkdirSync(out,{recursive:true});const b=await chromium.launch();const p=await b.newPage();
  for(const s of slugs){await p.goto('file://'+path.resolve(__dirname,'../../'+s+'.html'));await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);
    const d=await p.evaluate(()=>{const c=document.createElement('canvas');c.width=900;c.height=487;const x=c.getContext('2d');const G=__G;
      x.fillStyle=G.bg;x.fillRect(0,0,900,487);
      x.globalAlpha=.16;x.fillStyle=G.accent;for(let i=0;i<26;i++){x.beginPath();x.arc((i*173)%900,(i*97+40)%487,10+(i%4)*7,0,7);x.fill()}x.globalAlpha=1;
      D.rrect(x,185,26,530,435,48,'#fffdf8',7);
      G.icon(x,450,195,270);
      const t=G.title;let fs=58;x.font=fs+'px "Mochiy Pop One",sans-serif';const w=x.measureText(t).width;if(w>480)fs=fs*480/w;
      D.text(x,t,450,385,fs,'#5b4d45');
      return c.toDataURL('image/jpeg',.88)});
    fs.writeFileSync(path.join(out,s+'.jpg'),Buffer.from(d.split(',')[1],'base64'));console.log('thumb',s)}
  await b.close()})();
