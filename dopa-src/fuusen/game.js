/* ふうせんわり：下から上がる風船をタップ。 */
const GAME={...META,sprites:['icon','balloon'],unit:'点',time:30,fullBleed:true,
  bgm:{bpm:140,root:62,scale:'major',prog:[1,5,6,4],seed:58,lead:'square',drums:'four',density:.6},
  ranks:[[0,'空気ぬけ'],[200,'パンパン見習い'],[500,'わり上手'],[900,'ふうせんハンター'],[1400,'パンパンの達人'],[2000,'ふうせんの悪夢']],
  shareText:(v,f)=>`ふうせんわりで ${f}点！`,
  icon(c,x,y,s){this.balloon(c,x-s*.2,y+s*.05,s*.22,'#e2645a');this.balloon(c,x+s*.2,y-s*.15,s*.16,'#7fb2e0');this.balloon(c,x+s*.1,y+s*.25,s*.12,'#f2c84b')},
  balloon(c,x,y,r,col){c.lineWidth=2;c.strokeStyle=OL;c.beginPath();c.moveTo(x,y+r*1.15);c.quadraticCurveTo(x+r*.3,y+r*1.7,x-r*.1,y+r*2.3);c.stroke();D.ellipse(c,x,y,r,r*1.15,col);D.poly(c,[[x-r*.15,y+r*1.1],[x+r*.15,y+r*1.1],[x,y+r*1.35]],col,2);D.face(c,x,y+r*.1,r*1.1)},
  reset(api){this.st={b:[],spawn:0,t:0,ct:0};api.score=0},
  down(x,y,api){const st=this.st;let hit=null;for(let i=st.b.length-1;i>=0;i--){const b=st.b[i];if(dist(x,y,b.x,b.y)<b.r*1.2+10){hit=b;st.b.splice(i,1);break}}
    if(!hit){S.tap(.4);return}
    if(hit.k==='black'){api.combo=0;S.bad();api.shake(6);api.burst(hit.x,hit.y,{c:'#5b5560',n:10,sp:200});api.float(hit.x,hit.y-30,'コンボ切れ',{size:20});return}
    api.combo++;st.ct=1;const base=hit.k==='gold'?100:Math.round(60-hit.r);const pts=base+Math.min(api.combo,30)*3;api.add(pts);S.pop(1+Math.min(api.combo,20)*.03);S.noise(.05,{v:.4,f:3000});
    api.burst(hit.x,hit.y,{c:[hit.c,'#fff'],n:10,sp:220,r:4,shape:'s'});api.float(hit.x,hit.y-30,'+'+pts,{size:hit.k==='gold'?30:20,c:hit.k==='gold'?'#f3c84b':'#fff'});
    if(hit.k==='gold'){S.perfect();api.flash('#fff6c8',.3)}if(api.combo%10===0){S.fanfare();api.float(W/2,250,api.combo+'コンボ！',{size:34,c:'#f3c84b'})}},
  update(dt,api){const st=this.st;st.t+=dt;st.ct-=dt;if(st.ct<=0)api.combo=0;const lv=Math.min(1,st.t/30);
    st.spawn-=dt;if(st.spawn<=0){st.spawn=rnd(.25,.5)-lv*.12;const r=Math.random();const k=r<.07?'gold':r<.18?'black':'n';const rr=k==='gold'?22:k==='black'?26:rnd(14,34);
      st.b.push({x:rnd(40,W-40),y:H+60,r:rr,k,c:k==='gold'?'#f2c84b':k==='black'?'#5b5560':pick(['#e2645a','#7fb2e0','#9cc86a','#f2a5c0','#c49ae0']),vy:-(70+rnd(0,60)+lv*60+(40-rr)*1.5),ph:rnd(7)})}
    for(let i=st.b.length-1;i>=0;i--){const b=st.b[i];b.y+=b.vy*dt;b.ph+=dt*2;b.x+=Math.sin(b.ph)*20*dt;if(b.y<-80){st.b.splice(i,1);if(b.k!=='black'){api.combo=0}}}},
  draw(c,api){const st=this.st;c.fillStyle='#e8f1f7';c.fillRect(0,api.top,W,api.bottom-api.top);for(let i=0;i<5;i++)D.ellipse(c,(i*137+st.t*10)%(W+100)-50,150+i*110,50,16,'#fff',0);
    for(const b of st.b){if(b.k==='black'){D.ellipse(c,b.x,b.y,b.r,b.r*1.15,b.c);D.face(c,b.x,b.y+b.r*.1,b.r*1.1,'angry')}else this.balloon(c,b.x,b.y,b.r,b.c)}},
  __bot(api){const st=this.st;const b=st.b.filter(q=>q.k!=='black'&&q.y<H&&q.y>100).sort((a,b)=>a.y-b.y)[0];if(b&&Math.random()<.5)this.down(b.x,b.y,api)},
};
