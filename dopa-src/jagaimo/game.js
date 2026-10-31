/* ぽこぽこジャガイモ：3x3 のもぐらたたき。 */
const COLS=3,ROWS=3,HX=[95,210,325],HY=[330,470,610];
const GAME={...META,sprites:['icon','imo','onion'],unit:'点',time:30,fullBleed:true,
  bgm:{bpm:136,root:62,scale:'major',prog:[1,4,5,1],seed:13,lead:'square',drums:'four',density:.6},
  ranks:[[0,'ねぼすけ'],[300,'畑の見習い'],[700,'ぽこぽこ上手'],[1200,'ジャガイモ番長'],[1800,'収穫の達人'],[2600,'ポテトの神']],
  shareText:(v,f)=>`ぽこぽこジャガイモで ${f}点！`,
  icon(c,x,y,s){D.ellipse(c,x,y+s*.25,s*.42,s*.12,'#6b4f3a');this.imo(c,x,y+s*.05,s*.32,0,0)},
  imo(c,x,y,s,gold,hit){const col=gold?'#f2c84b':'#d9a86a';D.path(c,c=>{c.ellipse(x,y,s*.78,s,0,0,7)},col,Math.max(2.5,s*.08));
    c.fillStyle=gold?'#d9a23f':'#b98450';for(const[a,b]of[[-.45,-.45],[.4,-.6],[.5,.35]]){c.beginPath();c.arc(x+a*s*.7,y+b*s*.8,s*.05,0,7);c.fill()}
    if(hit){c.lineWidth=Math.max(2,s*.07);c.strokeStyle=OL;c.lineCap='round';for(const sx of[-1,1]){c.beginPath();c.moveTo(x+sx*s*.3,y-s*.12);c.lineTo(x+sx*s*.12,y-s*.02);c.lineTo(x+sx*s*.3,y+s*.08);c.stroke()}}
    else D.face(c,x,y,s*.75,gold?'o':'smile')},
  onion(c,x,y,s){D.path(c,c=>{c.moveTo(x,y-s*1.05);c.quadraticCurveTo(x+s*.25,y-s*.6,x+s*.75,y-s*.1);c.quadraticCurveTo(x+s*.85,y+s*.75,x,y+s*.8);c.quadraticCurveTo(x-s*.85,y+s*.75,x-s*.75,y-s*.1);c.quadraticCurveTo(x-s*.25,y-s*.6,x,y-s*1.05)},'#e8d6ee',Math.max(2.5,s*.08));
    c.strokeStyle='#c9a8d6';c.lineWidth=Math.max(1.5,s*.05);c.beginPath();c.moveTo(x-s*.3,y-s*.5);c.quadraticCurveTo(x-s*.45,y+s*.2,x-s*.25,y+s*.7);c.moveTo(x+s*.3,y-s*.5);c.quadraticCurveTo(x+s*.45,y+s*.2,x+s*.25,y+s*.7);c.stroke();D.face(c,x,y+s*.15,s*.6,'angry')},
  reset(api){this.st={h:Array.from({length:9},()=>({k:null,t:0,up:0,stay:0,hit:0})),spawn:.6,t:0,ct:0,sw:0,swx:0,swy:0};api.score=0},
  down(x,y,api){const st=this.st;st.sw=.12;st.swx=x;st.swy=y;let hit=false;
    for(let i=0;i<9;i++){const h=st.h[i];if(!h.k||h.hit)continue;const hx=HX[i%3],hy=HY[Math.floor(i/3)];if(Math.abs(x-hx)<56&&y>hy-110*h.up-20&&y<hy+30){hit=true;h.hit=.01;
        if(h.k==='onion'){api.timeLeft=Math.max(0,api.timeLeft-3);api.combo=0;S.bad();api.shake(8);api.flash('#e8d6ee',.5);api.float(hx,hy-90,'しみる〜 -3秒',{size:24,c:'#c49ae0'})}
        else{api.combo++;st.ct=1.1;const g=h.k==='gold',pts=(g?50:10)+Math.min(api.combo,30)*2;api.add(pts);api.hitstop(30);
          if(g){S.perfect();api.flash('#fff6c8',.4);api.burst(hx,hy-60,{c:['#f4d66d','#fff'],n:20,shape:'star',sp:260})}else{S.thud();S.pop(1+Math.min(api.combo,20)*.03)}
          api.burst(hx,hy-50,{c:['#d9a86a','#fff','#b98450'],n:8,sp:180,r:4});api.float(hx,hy-110,'+'+pts,{size:g?30:22,c:g?'#f3c84b':'#fff'});api.ring(hx,hy-50,{c:'#fff',r:50})}
        break}}
    if(!hit){api.combo=0;S.tap(.5)}},
  key(k,api){const n='789456123'.indexOf(k);if(n>=0)this.down(HX[n%3],HY[Math.floor(n/3)]-50,api)},
  update(dt,api){const st=this.st;st.t+=dt;st.sw=Math.max(0,st.sw-dt);st.ct-=dt;if(st.ct<=0)api.combo=0;
    const lv=Math.min(1,st.t/30);api.fever=api.combo>=15;
    st.spawn-=dt;if(st.spawn<=0){st.spawn=rnd(.32,.6)-lv*.18;const free=st.h.map((h,i)=>h.k?-1:i).filter(i=>i>=0);if(free.length){const h=st.h[pick(free)];const r=Math.random();h.k=r<.08?'gold':r<.24+lv*.08?'onion':'imo';h.t=0;h.up=0;h.hit=0;h.stay=rnd(.7,1.1)-lv*.35;S.tone(500,.05,{type:'sine',v:.1,to:800})}}
    for(const h of st.h){if(!h.k)continue;h.t+=dt;if(h.hit>0){h.hit+=dt;h.up=Math.max(0,h.up-dt*5);if(h.hit>.35){h.k=null}continue}
      if(h.t<.12)h.up=ease.outBack(h.t/.12);else if(h.t<.12+h.stay)h.up=1;else{h.up=Math.max(0,1-(h.t-.12-h.stay)/.12);if(h.up<=0){if(h.k!=='onion')api.combo=0;h.k=null}}}},
  draw(c,api){const st=this.st;c.fillStyle='#bfe0ef';c.fillRect(0,api.top,W,200-api.top);c.fillStyle='#9cc86a';c.fillRect(0,200,W,40);c.fillStyle='#c9a274';c.fillRect(0,240,W,api.bottom-240);
    c.fillStyle='#bd9466';for(let y=260;y<api.bottom;y+=46)c.fillRect(0,y,W,8);
    for(let i=0;i<9;i++){const hx=HX[i%3],hy=HY[Math.floor(i/3)],h=st.h[i];D.ellipse(c,hx,hy,58,20,'#5e4532',3.5);
      if(h.k){c.save();c.beginPath();c.rect(hx-80,hy-200,160,200);c.ellipse(hx,hy,56,18,0,0,Math.PI);c.clip();const yy=hy+60-110*h.up;const sq=h.hit>0?1-Math.min(.25,h.hit*2):1;
        c.translate(hx,yy+50);c.scale(1/sq,sq);if(h.k==='onion')this.onion(c,0,-50,48);else this.imo(c,0,-50,50,h.k==='gold',h.hit>0);c.restore()}
      D.path(c,c=>{c.ellipse(hx,hy,58,20,0,0,Math.PI)},null,3.5)}
    if(st.sw>0){const k=st.sw/.12;c.save();c.translate(st.swx+30,st.swy-40);c.rotate(-.6+k*.8);D.rrect(c,-8,0,16,70,6,'#e3b47a',3);D.rrect(c,-30,-24,60,30,10,'#f2a5c0',3.5);c.restore()}},
  __bot(api){const st=this.st;for(let i=0;i<9;i++){const h=st.h[i];if(h.k&&h.k!=='onion'&&!h.hit&&h.up>.6&&Math.random()<.5){this.down(HX[i%3],HY[Math.floor(i/3)]-50,api);return}}},
};
