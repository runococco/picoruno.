/* ひっぱりつり：針を沈めて、戻すときに当たった魚を全部つる。深いほど大きい魚。 */
const SEA=200,BOT=700,BX=W/2;
const FK=[{r:12,c:'#8fc46a',p:5},{r:16,c:'#f2a24a',p:10},{r:20,c:'#7fb2e0',p:20},{r:26,c:'#e46a6a',p:40},{r:34,c:'#c49ae0',p:80}];
const GAME={...META,sprites:['icon','fish','fugu','boat'],unit:'点',time:60,fullBleed:true,
  bgm:{bpm:108,root:60,scale:'major',prog:[1,4,6,5],seed:72,lead:'triangle',drums:'pop',density:.5},
  ranks:[[0,'ボウズ'],[200,'つり初心者'],[600,'まずまずの大漁'],[1200,'つり名人'],[2200,'海のぬし'],[3500,'伝説のつり師']],
  shareText:(v,f)=>`ひっぱりつりで ${f}点！`,
  icon(c,x,y,s){D.ellipse(c,x,y+s*.1,s*.46,s*.3,'#8ccbdb');this.boat(c,x,y-s*.2,s*.5);this.fish(c,x+s*.12,y+s*.2,s*.14,'#f2a24a',3.4,0)},
  boat(c,x,y,s){D.path(c,c=>{c.moveTo(x-s*.5,y);c.lineTo(x+s*.5,y);c.lineTo(x+s*.35,y+s*.25);c.lineTo(x-s*.35,y+s*.25);c.closePath()},'#e3b47a');D.rrect(c,x-s*.12,y-s*.3,s*.24,s*.3,s*.06,'#f2a5c0')},
  fish(c,x,y,r,col,a,sw){c.save();c.translate(x,y);c.rotate(a);const w=Math.sin(sw)*.35;D.group(c,()=>{c.save();c.translate(-r*.9,0);c.rotate(w);D.path(c,c=>{c.moveTo(0,0);c.lineTo(-r*.7,-r*.55);c.lineTo(-r*.7,r*.55);c.closePath()},col,Math.max(2,r*.12));c.restore();D.ellipse(c,0,0,r,r*.62,col,Math.max(2,r*.12))});
    c.fillStyle=OL;c.beginPath();c.arc(r*.45,-r*.12,Math.max(1.5,r*.1),0,7);c.fill();c.restore()},
  fugu(c,x,y,r){D.circle(c,x,y,r,'#f4e2b4');c.fillStyle=OL;for(let i=0;i<8;i++){const a=i*.785;c.beginPath();c.moveTo(x+Math.cos(a)*r*.95,y+Math.sin(a)*r*.95);c.lineTo(x+Math.cos(a)*r*1.2,y+Math.sin(a)*r*1.2);c.lineTo(x+Math.cos(a+.25)*r*.95,y+Math.sin(a+.25)*r*.95);c.fill()}D.face(c,x,y+r*.1,r,'angry')},
  newFish(){const d=Math.random();const k=d<.35?0:d<.6?1:d<.8?2:d<.93?3:4;const y=SEA+40+(k/4)*(BOT-SEA-100)+rnd(-40,40);return{x:Math.random()<.5?-40:W+40,y:clamp(y,SEA+30,BOT-30),k,v:(Math.random()<.5?1:-1)*rnd(40,80),sw:rnd(7),fugu:false}},
  reset(api){const st=this.st={f:[],hy:SEA,ph:'idle',caught:[],t:0,hx:BX,bob:0};for(let i=0;i<14;i++){const f=this.newFish();f.x=rnd(30,W-30);st.f.push(f)}for(let i=0;i<3;i++){const f=this.newFish();f.fugu=true;f.k=2;f.x=rnd(30,W-30);st.f.push(f)}api.score=0},
  down(){const st=this.st;if(st.ph==='idle'){st.ph='down';S.noise(.15,{v:.15,f:600,type:'lowpass'})}},
  up(){const st=this.st;if(st.ph==='down'){st.ph='up';S.whoosh()}},
  key(k){if(k===' ')this.down()},keyUp(k){if(k===' ')this.up()},
  update(dt,api){const st=this.st;st.t+=dt;
    for(let i=st.f.length-1;i>=0;i--){const f=st.f[i];if(f.held)continue;f.x+=f.v*dt;f.sw+=dt*8;if((f.v>0&&f.x>W+50)||(f.v<0&&f.x<-50)){const n=this.newFish();if(f.fugu){n.fugu=true;n.k=2}st.f[i]=n;if(n.x<0)n.v=Math.abs(n.v);else n.v=-Math.abs(n.v)}}
    if(st.ph==='down'){st.hy+=240*dt;if(st.hy>=BOT-14){st.hy=BOT-14;st.ph='up';S.thud()}}
    else if(st.ph==='up'){const sp=300-st.caught.length*18;st.hy-=Math.max(120,sp)*dt;
      for(const f of st.f){if(f.held)continue;const R=f.fugu?20:FK[f.k].r;if(Math.abs(f.x-st.hx)<R+8&&Math.abs(f.y-st.hy)<R*.7){
          if(f.fugu){f.held=true;st.caught.push(f);S.bad();api.shake(8);api.float(st.hx,st.hy-40,'ふぐ！ぜんぶ落とした…',{size:22,c:'#fff'});for(const g of st.caught){if(!g.fugu){g.held=false;g.y=clamp(g.y+rnd(40,120),SEA+30,BOT-30)}}st.caught=[f]}
          else{f.held=true;st.caught.push(f);S.pop(1.2-f.k*.1);api.burst(f.x,f.y,{c:['#fff','#bfe3ee'],n:6,sp:120,r:3})}}}
      for(const f of st.caught){f.x+=(st.hx-f.x)*Math.min(1,dt*10);f.y=st.hy+10}
      if(st.hy<=SEA){st.hy=SEA;st.ph='idle';let pts=0,n=0;for(const f of st.caught){if(f.fugu)continue;pts+=FK[f.k].p;n++;const i=st.f.indexOf(f);st.f[i]=this.newFish()}
        for(const f of st.caught)if(f.fugu){f.held=false;f.y=rnd(SEA+100,BOT-60)}
        if(n){const mul=1+Math.max(0,n-1)*.5;pts=Math.round(pts*mul);api.add(pts);api.combo=n;S.coin();if(n>=3){S.perfect();api.flash('#fff',.3);api.float(BX,SEA-60,n+'ひき同時！ ×'+mul.toFixed(1),{size:28,c:'#f3c84b'})}api.float(BX,SEA-20,'+'+pts,{size:26})}
        st.caught=[]}}},
  draw(c,api){const st=this.st;c.fillStyle='#dcecf4';c.fillRect(0,api.top,W,SEA-api.top);
    const g=c.createLinearGradient(0,SEA,0,BOT);g.addColorStop(0,'#8ccbdb');g.addColorStop(1,'#3f6f8c');c.fillStyle=g;c.fillRect(0,SEA,W,api.bottom-SEA);
    c.fillStyle='#b7dbe6';c.beginPath();for(let x=0;x<=W;x+=20)c.lineTo(x,SEA+Math.sin(x*.05+st.t*2)*4);c.lineTo(W,SEA+12);c.lineTo(0,SEA+12);c.fill();
    c.fillStyle='#2f5569';c.fillRect(0,BOT,W,api.bottom-BOT);for(let i=0;i<6;i++)D.ellipse(c,40+i*70,BOT,26,10,'#2f5569',0);
    c.lineWidth=2.5;c.strokeStyle='#fbf7f0';c.beginPath();c.moveTo(st.hx,SEA-30);c.lineTo(st.hx,st.hy);c.stroke();
    for(const f of st.f)if(!f.held){if(f.fugu)this.fugu(c,f.x,f.y,20);else this.fish(c,f.x,f.y,FK[f.k].r,FK[f.k].c,f.v>0?0:Math.PI,f.sw)}
    for(const f of st.caught){if(f.fugu)this.fugu(c,f.x,f.y,20);else this.fish(c,f.x,f.y,FK[f.k].r,FK[f.k].c,-Math.PI/2,f.sw)}
    D.path(c,c=>{c.arc(st.hx,st.hy,7,Math.PI*1.5,Math.PI*.5)},null,3);
    this.boat(c,BX,SEA-32+Math.sin(st.t*2)*3,90);
    if(st.ph==='idle'&&api.t<3&&api.state==='play')D.text(c,'おしてしずめる→はなして引き上げ',W/2,SEA+40,16,'#fff','center',OL,4)},
  __bot(api){const st=this.st;if(st.ph==='idle')this.down();if(st.ph==='down'&&st.hy>rnd(400,680))this.up()},
};
