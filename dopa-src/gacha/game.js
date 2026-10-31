/* ガチャガチャずかん：コインキャッチ→ガチャ→ずかん（localStorage に残る）。スコアはずかんの種類数。 */
const CT=20,PER=5,KEY='dopa-gacha-col';
const RAR={N:{c:'#c9bfb4',n:'ノーマル',w:60},R:{c:'#7fb2e0',n:'レア',w:28},SR:{c:'#c49ae0',n:'スーパーレア',w:10},SSR:{c:'#f2c84b',n:'ウルトラレア',w:2}};
const MAS=[
  ['まるもち','maru','#fbf7f0','N'],['ももまる','maru','#f2a5b5','N'],['みかんまる','maru','#f2b45a','N'],['しかくパン','kaku','#e3b47a','N'],['とうふ','kaku','#fbfaf6','N'],['ゼリーしかく','kaku','#9fd2d9','N'],
  ['しずくちゃん','drop','#a9d6e6','N'],['ジュースしずく','drop','#f08a8a','N'],['くもくも','cloud','#fbfaf6','N'],['あめくも','cloud','#a7a3ad','N'],['まめた','mame','#9cc86a','N'],['あずき','mame','#b0646a','N'],
  ['ほしのこ','star','#f4d66d','N'],['おばけ','ghost','#fbfaf6','N'],
  ['はーとん','heart','#f2a5c0','R'],['あおはーと','heart','#7fb2e0','R'],['きのこ','kinoko','#e2645a','R'],['しいたけ','kinoko','#a07a5a','R'],['みかづき','moon','#f4d66d','R'],['よぞらぼし','star','#7d6aa8','R'],
  ['おうさまもち','maru','#fbf7f0','SR','crown'],['てんしくも','cloud','#fbfaf6','SR','halo'],['はなまめ','mame','#f2a5c0','SR','flower'],
  ['にじいろスター','star','rainbow','SSR','crown']];
const GAME={...META,sprites:['icon','mascot','machine','capsule'],unit:'種',fullBleed:true,comboHud:false,overDelay:.6,
  bgm:{bpm:128,root:62,scale:'major',prog:[1,5,6,4],seed:99,lead:'square',drums:'pop',density:.6},
  ranks:[[0,'ずかんスタート'],[4,'コレクター見習い'],[8,'ガチャ好き'],[13,'ずかん半分こえ'],[19,'コンプまであと少し'],[24,'コンプリート！']],
  shareText:(v,f)=>`ガチャガチャずかん ${f}/24種 あつめた！`,
  icon(c,x,y,s){this.machine(c,x,y,s*.85,0)},
  col(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return{}}},
  saveCol(o){try{localStorage.setItem(KEY,JSON.stringify(o))}catch(e){}},
  mascot(c,x,y,r,i,sil){const m=MAS[i],sh=m[1],lw=Math.max(2,r*.1);let col=sil?'#d9cfc6':m[2];
    if(col==='rainbow'){const g=c.createLinearGradient(x-r,y-r,x+r,y+r);['#f08a8a','#f2c84b','#9cc86a','#7fb2e0','#c49ae0'].forEach((cc,k)=>g.addColorStop(k/4,cc));col=g}
    D.group(c,()=>{
    if(sh==='maru')D.circle(c,x,y,r,col,lw);
    else if(sh==='kaku')D.rrect(c,x-r,y-r*.85,r*2,r*1.75,r*.35,col,lw);
    else if(sh==='drop')D.path(c,c=>{c.moveTo(x,y-r*1.15);c.quadraticCurveTo(x+r*1.05,y,x+r*.9,y+r*.3);c.arc(x,y+r*.3,r*.9,0,Math.PI);c.quadraticCurveTo(x-r*1.05,y,x,y-r*1.15)},col,lw);
    else if(sh==='cloud')D.path(c,c=>{c.arc(x-r*.5,y+r*.15,r*.55,Math.PI*.5,Math.PI*1.5);c.arc(x,y-r*.3,r*.62,Math.PI*1.1,Math.PI*1.9);c.arc(x+r*.52,y+r*.1,r*.55,Math.PI*1.5,Math.PI*.5);c.closePath()},col,lw);
    else if(sh==='mame')D.path(c,c=>{c.ellipse(x,y,r*.8,r,0,0,7)},col,lw);
    else if(sh==='star')D.star(c,x,y,r*1.2,col,lw,0,5,.58);
    else if(sh==='ghost')D.path(c,c=>{c.arc(x,y-r*.1,r*.85,Math.PI,0);c.lineTo(x+r*.85,y+r*.8);for(let k=0;k<3;k++){const x0=x+r*.85-k*r*.57;c.quadraticCurveTo(x0-r*.14,y+r*.55,x0-r*.28,y+r*.8);c.quadraticCurveTo(x0-r*.42,y+r*1.05,x0-r*.57,y+r*.8)}c.closePath()},col,lw);
    else if(sh==='heart')D.path(c,c=>{c.moveTo(x,y+r*.9);c.bezierCurveTo(x-r*1.4,y,x-r*.7,y-r*1.1,x,y-r*.45);c.bezierCurveTo(x+r*.7,y-r*1.1,x+r*1.4,y,x,y+r*.9)},col,lw);
    else if(sh==='kinoko'){D.rrect(c,x-r*.45,y,r*.9,r*.9,r*.3,sil?col:'#fbf2e4',lw);D.path(c,c=>{c.moveTo(x-r*1.05,y+r*.1);c.quadraticCurveTo(x-r,y-r,x,y-r);c.quadraticCurveTo(x+r,y-r,x+r*1.05,y+r*.1);c.closePath()},col,lw)}
    else if(sh==='moon')D.path(c,c=>{c.arc(x,y,r,-Math.PI*.35,Math.PI*1.35);c.arc(x+r*.45,y-r*.4,r*.75,Math.PI*1.1,Math.PI*-.05,true);c.closePath()},col,lw);
    if(!sil&&m[4]==='crown')D.poly(c,[[x-r*.45,y-r*.95],[x-r*.45,y-r*1.4],[x-r*.2,y-r*1.15],[x,y-r*1.45],[x+r*.2,y-r*1.15],[x+r*.45,y-r*1.4],[x+r*.45,y-r*.95]],'#f2c84b',lw*.8);
    if(!sil&&m[4]==='flower')for(let k=0;k<5;k++)D.circle(c,x+r*.45+Math.cos(k*1.26)*r*.18,y-r*.75+Math.sin(k*1.26)*r*.18,r*.14,'#fbfaf6',lw*.6);
    });
    if(!sil&&m[4]==='halo'){c.lineWidth=lw;c.strokeStyle='#f2c84b';c.beginPath();c.ellipse(x,y-r*1.15,r*.45,r*.13,0,0,7);c.stroke()}
    if(sil){D.text(c,'？',x,y+r*.05,r*.9,'#fbf7f0');return}
    const fy=sh==='kinoko'?y+r*.42:sh==='drop'?y+r*.3:sh==='moon'?y+r*.15:y+r*.05,fx=sh==='moon'?x-r*.3:x;D.face(c,fx,fy,r*(sh==='kinoko'?.6:.9))},
  machine(c,x,y,s,turn){D.rrect(c,x-s*.42,y+s*.05,s*.84,s*.45,s*.08,'#e0789a');D.circle(c,x,y-s*.15,s*.4,'#f9f2f4');
    const cc=['#f2a5b5','#7fb2e0','#f4d66d','#9cc86a','#c49ae0'];c.save();c.beginPath();c.arc(x,y-s*.15,s*.37,0,7);c.clip();for(let i=0;i<9;i++){const a=i*.9+turn*2;this.capsule(c,x+Math.cos(a)*s*.2*(i%3*.5+.5),y-s*.05+Math.sin(a)*s*.08-(i%3)*s*.09,s*.09,cc[i%5],a)}c.restore();
    D.circle(c,x,y-s*.15,s*.4,null,3.5);D.circle(c,x+s*.18,y+s*.27,s*.1,'#fbf7f0');c.save();c.translate(x+s*.18,y+s*.27);c.rotate(turn*Math.PI);D.rrect(c,-s*.11,-s*.025,s*.22,s*.05,s*.02,'#f2c84b',2.5);c.restore();
    D.rrect(c,x-s*.3,y+s*.2,s*.22,s*.18,s*.04,'#4b3e37',3);D.face(c,x-s*.05,y+s*.12,s*.25)},
  capsule(c,x,y,r,col,rot=0,open=0){c.save();c.translate(x,y);c.rotate(rot);D.path(c,c=>{c.arc(0,-open*r*.8,r,Math.PI,0);c.closePath()},col,Math.max(2,r*.12));D.path(c,c=>{c.arc(0,open*r*.8,r,0,Math.PI);c.closePath()},'#fbfaf6',Math.max(2,r*.12));c.restore()},
  reset(api){const st=this.st={ph:'catch',t:CT,bx:W/2,tx:W/2,items:[],coins:0,spawn:0,turns:0,cap:null,got:[],turn:0,msg:'',col:this.col()};api.score=Object.keys(st.col).length},
  roll(){const r=Math.random()*100;let acc=0,rar='N';for(const k of['SSR','SR','R','N']){acc+=RAR[k].w;if(r<acc){rar=k;break}}const pool=MAS.map((m,i)=>i).filter(i=>MAS[i][3]===rar);return pick(pool)},
  down(x,y,api){const st=this.st;if(st.ph==='catch'){st.tx=x;return}
    if(st.ph==='gacha'&&!st.cap){if(st.turns<=0)return;st.turns--;st.cap={ph:'turn',t:0,i:this.roll()};S.noise(.5,{v:.3,f:400,to:900});for(let k=0;k<5;k++)S.tone(300+k*40,.05,{at:k*.09,v:.1});return}
    if(st.cap&&st.cap.ph==='wait'){st.cap.ph='open';st.cap.t=0;this.reveal(api)}
    else if(st.cap&&st.cap.ph==='show'&&st.cap.t>.5){st.cap=null;if(st.turns<=0){st.ph='done';st.doneT=.6}}},
  move(x){if(this.st.ph==='catch')this.st.tx=x},
  key(k,api){const st=this.st;if(k==='ArrowLeft')st.tx=st.bx-60;if(k==='ArrowRight')st.tx=st.bx+60;if(k===' ')this.down(st.bx,400,api)},keyRepeat:true,
  reveal(api){const st=this.st,i=st.cap.i,m=MAS[i],isNew=!st.col[m[0]];st.col[m[0]]=(st.col[m[0]]||0)+1;this.saveCol(st.col);st.cap.isNew=isNew;st.got.push(i);api.score=Object.keys(st.col).length;
    const R=m[3];S.pop(1);if(R==='SSR'){S.fanfare();api.flash('#fff6c8',.9);api.shake(12);for(let k=0;k<6;k++)api.burst(rnd(60,W-60),rnd(200,600),{c:['#f08a8a','#f2c84b','#9cc86a','#7fb2e0','#c49ae0'],n:20,shape:'star',sp:340})}
    else if(R==='SR'){S.perfect();api.flash('#f4ecff',.6);api.burst(W/2,400,{c:['#c49ae0','#fff'],n:30,shape:'star',sp:300})}
    else if(R==='R'){S.good();api.burst(W/2,400,{c:['#7fb2e0','#fff'],n:16,shape:'star'})}else S.coin();
    if(isNew)setTimeout(()=>S.coin(1.5),300)},
  update(dt,api){const st=this.st;st.turn+=dt*(st.cap&&st.cap.ph==='turn'?6:.3);
    if(st.ph==='catch'){st.t-=dt;st.bx+=(clamp(st.tx,40,W-40)-st.bx)*Math.min(1,dt*14);st.spawn-=dt;
      if(st.spawn<=0){st.spawn=rnd(.18,.36);const r=Math.random();st.items.push({x:rnd(30,W-30),y:120,vy:rnd(220,330)+(CT-st.t)*8,k:r<.12?'big':r<.27?'cloud':'coin',rot:rnd(7)})}
      for(let i=st.items.length-1;i>=0;i--){const it=st.items[i];it.y+=it.vy*dt;it.rot+=dt*4;
        if(it.y>590&&it.y<640&&Math.abs(it.x-st.bx)<52){st.items.splice(i,1);
          if(it.k==='cloud'){const n=Math.min(st.coins,3);st.coins-=n;S.zap(.6);api.shake(6);api.float(st.bx,540,'-'+n,{size:26,c:'#e2645a'})}
          else{const n=it.k==='big'?5:1;st.coins+=n;S.coin(it.k==='big'?.8:1.2);api.float(st.bx,540,'+'+n,{size:it.k==='big'?28:20,c:'#f3c84b'});api.burst(it.x,600,{c:['#f4d66d','#fff'],n:5,sp:120,r:3})}continue}
        if(it.y>H+40)st.items.splice(i,1)}
      if(st.t<=0){st.ph='gacha';st.turns=Math.max(1,Math.floor(st.coins/PER));st.items.length=0;S.fanfare();api.float(W/2,300,'ガチャ '+st.turns+'回！',{size:40,c:'#f3c84b',life:1.4})}}
    else if(st.cap){const cp=st.cap;cp.t+=dt;if(cp.ph==='turn'&&cp.t>.9){cp.ph='drop';cp.t=0;S.thud()}else if(cp.ph==='drop'&&cp.t>.45){cp.ph='wait';cp.t=0}else if(cp.ph==='open'&&cp.t>.35){cp.ph='show';cp.t=0}}
    else if(st.ph==='done'){st.doneT-=dt;if(st.doneT<=0)api.end()}},
  sharePhoto(c,x,y,w,h){const st=this.st;D.rrect(c,x,y,w,h,24,'#fdf6f8',4);D.text(c,'ずかん '+Object.keys(st.col).length+'/24',x+w/2,y+32,26,'#5b4d45');
    const cw=w/6,chh=(h-60)/4;MAS.forEach((m,i)=>{const cx=x+cw*(i%6)+cw/2,cy=y+60+chh*Math.floor(i/6)+chh/2;if(st.col[m[0]]){D.circle(c,cx,cy,cw*.42,RAR[m[3]].c+'55',0)}this.mascot(c,cx,cy+2,Math.min(cw,chh)*.28,i,!st.col[m[0]])})},
  drawHud(c,api){const st=this.st;if(st.ph==='catch'){D.rrect(c,70,20,280,56,28,'#fffdf8',3.5);D.text(c,'コイン '+st.coins+'　のこり'+Math.ceil(st.t)+'秒',W/2,48,20,'#5b4d45')}
    else{D.rrect(c,60,20,300,56,28,'#fffdf8',3.5);D.text(c,'のこり '+st.turns+'回　ずかん '+Object.keys(st.col).length+'/24',W/2,48,19,'#5b4d45')}},
  draw(c,api){const st=this.st;c.fillStyle='#f7e6ea';c.fillRect(0,api.top,W,api.bottom-api.top);c.fillStyle='#f2dbe1';for(let i=-2;i<12;i++)c.fillRect(i*60+((st.turn*10)%60),api.top,26,api.bottom-api.top);
    if(st.ph==='catch'){for(const it of st.items){if(it.k==='cloud'){D.path(c,c=>{const x=it.x,y=it.y,r=22;c.arc(x-r*.5,y+r*.15,r*.55,Math.PI*.5,Math.PI*1.5);c.arc(x,y-r*.3,r*.62,Math.PI*1.1,Math.PI*1.9);c.arc(x+r*.52,y+r*.1,r*.55,Math.PI*1.5,Math.PI*.5);c.closePath()},'#8a8392');D.poly(c,[[it.x-2,it.y+12],[it.x+8,it.y+12],[it.x,it.y+28],[it.x+4,it.y+18],[it.x-6,it.y+18]],'#f4d66d',2)}
        else{const r=it.k==='big'?20:13;c.save();c.translate(it.x,it.y);c.scale(Math.cos(it.rot),1);D.circle(c,0,0,r,'#e9b949',3);D.star(c,0,0,r*.45,'#f4d66d',0);c.restore()}}
      D.rrect(c,st.bx-52,600,104,50,16,'#e0789a',4);D.rrect(c,st.bx-46,592,92,16,8,'#f2a5c0',3);D.face(c,st.bx,628,40);
      if(st.t>CT-2&&api.state==='play')D.text(c,'左右に動かしてキャッチ！',W/2,360,22,'#5b4d45','center','#fffdf8',6);return}
    const tw=st.cap&&st.cap.ph==='turn'?st.turn:st.turn*.2;this.machine(c,W/2,330,300,tw);
    if(!st.cap&&st.turns>0)D.text(c,'タップでガチャを回す',W/2,560,22,'#5b4d45','center','#fffdf8',6);
    const cp=st.cap;if(cp){const R=MAS[cp.i][3],cc={N:'#f2a5b5',R:'#7fb2e0',SR:'#c49ae0',SSR:'#f2c84b'}[R];
      if(cp.ph==='drop'){const k=Math.min(1,cp.t/.45);this.capsule(c,W/2-45+k*45,lerp(390,470,ease.outBack(k)),24+k*20,cc,k*6)}
      if(cp.ph==='wait'){const wb=Math.sin(cp.t*20)*.1;this.capsule(c,W/2,470,44,cc,wb);D.text(c,'タップしてあける！',W/2,560,22,'#5b4d45','center','#fffdf8',6)}
      if(cp.ph==='open'||cp.ph==='show'){c.globalAlpha=.9;c.fillStyle='#fffaf3';c.fillRect(0,api.top,W,api.bottom-api.top);c.globalAlpha=1;const k=cp.ph==='open'?cp.t/.35:1;
        if(R!=='N'){c.save();c.translate(W/2,400);c.rotate(st.turn);c.globalAlpha=.35;for(let i=0;i<12;i++){c.rotate(Math.PI/6);c.fillStyle=RAR[R].c;c.beginPath();c.moveTo(0,0);c.lineTo(-30,-320);c.lineTo(30,-320);c.fill()}c.restore();c.globalAlpha=1}
        if(cp.ph==='open')this.capsule(c,W/2,470-k*70,44,cc,0,k*2);
        else{const s=ease.outBack(Math.min(1,cp.t*3));c.save();c.translate(W/2,400);c.scale(s,s);this.mascot(c,0,0,70,cp.i);c.restore();
          D.rrect(c,W/2-90,250,180,40,20,RAR[R].c,3);D.text(c,RAR[R].n,W/2,270,18,'#fffdf8','center',OL,4);D.text(c,MAS[cp.i][0],W/2,520,32,'#5b4d45','center','#fffdf8',7);
          if(cp.isNew)D.text(c,'NEW!',W/2+100,320,28,'#e2645a','center','#fffdf8',6);if(cp.t>.5)D.text(c,'タップでつぎへ',W/2,600,18,'#8e8077')}}}},
  __bot(api){const st=this.st;if(st.ph==='catch'){const it=st.items.filter(i=>i.k!=='cloud'&&i.y<600).sort((a,b)=>b.y-a.y)[0];if(it)st.tx=it.x}else this.down(W/2,400,api)},
};
