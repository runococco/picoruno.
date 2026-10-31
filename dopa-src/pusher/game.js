/* おかしプッシャー：真上から見たメダルプッシャー。円どうしを押し合いで解く。 */
const TL=50,TR=370,TB=600,PZ=170;// 台の左右・手前の縁・押し台の奥
const GAME={...META,sprites:['icon','medal','prize'],unit:'枚',
  bgm:{bpm:120,root:57,scale:'major',prog:[1,4,5,1],seed:71,lead:'square',drums:'pop',density:.58},
  ranks:[[0,'すっからかん'],[20,'ちょびっと'],[50,'ジャラジャラ'],[100,'メダル持ち'],[200,'プッシャー名人'],[400,'おかしの大富豪']],
  shareText:(v,f)=>`おかしプッシャーで ${f}枚 ゲット！`,
  icon(c,x,y,s){for(let i=0;i<5;i++)this.medal(c,x-s*.3+i*s*.15,y+s*.2-(i%2)*s*.06,s*.1);this.prize(c,x,y-s*.08,s*.2,0)},
  medal(c,x,y,r){D.circle(c,x,y,r,'#e9b949',2.5);D.circle(c,x,y,r*.6,'#d9a23f',0);D.star(c,x,y,r*.38,'#f4d66d',0)},
  prize(c,x,y,r,k){if(k===0){D.circle(c,x,y,r,'#f08a8a');D.face(c,x,y+r*.1,r*1.1)}
    else if(k===1){D.rrect(c,x-r,y-r*.7,r*2,r*1.4,r*.25,'#9a6a4e');c.strokeStyle='#7a4f38';c.lineWidth=2;c.beginPath();c.moveTo(x,y-r*.7);c.lineTo(x,y+r*.7);c.moveTo(x-r,y);c.lineTo(x+r,y);c.stroke();D.face(c,x,y+r*.05,r*.9)}
    else{D.circle(c,x,y,r,'#a07bd0');D.star(c,x,y,r*.6,'#f4d66d',2.5)}},
  reset(api){const st=this.st={m:[],stock:30,got:0,pz:0,pt:0,drops:0,idle:0,fallFx:[],rain:0,dropCd:0};
    for(let i=0;i<88;i++){const x=rnd(TL+16,TR-16),y=rnd(PZ+40,TB-20);st.m.push({x,y,r:15,k:-1})}
    for(let i=0;i<3;i++)st.m.push({x:rnd(TL+40,TR-40),y:rnd(PZ+80,TB-120),r:24,k:i%2});
    for(let i=0;i<30;i++)this.solve();api.score=0},
  plate(){return PZ+50+Math.sin(this.st.pt*1.9)*45},
  down(x,y,api){const st=this.st;if(st.stock<=0||st.dropCd>0)return;st.dropCd=.12;st.stock--;st.drops++;
    const px=clamp(x,TL+16,TR-16),f=this.plate();
    let k=-1,r=15;if(st.drops%9===0){k=rndi(0,1);r=24}if(st.drops%23===0){k=2;r=20}
    st.m.push({x:px,y:f+r+rnd(4,30),r,k,z:1});S.clink(1.1);api.idle=0},
  solve(){const st=this.st,M=st.m,f=this.plate();
    for(const a of M){if(a.y-a.r<f)a.y=f+a.r;a.x=clamp(a.x,TL+a.r,TR-a.r)}
    for(let it=0;it<3;it++)for(let i=0;i<M.length;i++){const a=M[i];for(let j=i+1;j<M.length;j++){const b=M[j],dx=b.x-a.x,dy=b.y-a.y,rr=a.r+b.r;if(Math.abs(dx)>rr||Math.abs(dy)>rr)continue;const d=Math.hypot(dx,dy)||.01;if(d<rr){const o=(rr-d)/2,nx=dx/d,ny=dy/d;
      // 押し台に近い方は奥へは逃げない
      const aw=a.y-a.r<=f+1?0:1,bw=b.y-b.r<=f+1?0:1,s=aw+bw||1;a.x-=nx*o*2*aw/s;a.y-=ny*o*2*aw/s;b.x+=nx*o*2*bw/s;b.y+=ny*o*2*bw/s}}
      if(a.y-a.r<f)a.y=f+a.r;a.x=clamp(a.x,TL+a.r,TR-a.r)}},
  update(dt,api){const st=this.st;st.pt+=dt;st.dropCd-=dt;this.solve();
    if(st.rain>0){st.rain-=dt;if(Math.random()<dt*30){st.m.push({x:rnd(TL+20,TR-20),y:rnd(PZ+60,TB-160),r:15,k:-1,z:1});S.clink(rnd(.9,1.3))}}
    for(let i=st.m.length-1;i>=0;i--){const m=st.m[i];if(m.z>0)m.z=Math.max(0,m.z-dt*5);
      if(m.y>TB+m.r*.2){st.m.splice(i,1);const side=m.x<TL+50||m.x>TR-50;
        if(side){st.fallFx.push({x:m.x,y:TB,k:m.k,r:m.r,t:0,lost:true});S.tap(.5);continue}
        let n=m.k<0?1:m.k===2?0:m.k===0?5:8;st.stock+=n;st.got+=n;api.add(n);api.combo++;st.comboT=1;
        st.fallFx.push({x:m.x,y:TB,k:m.k,r:m.r,t:0});
        if(m.k===2){st.rain=2.2;S.perfect();api.flash('#fff8d0',.5);api.shake(10);api.float(W/2,300,'メダルの大雨！',{size:38,c:'#f3c84b',life:1.4});api.burst(m.x,TB,{c:['#f4d66d','#fff'],n:30,shape:'star',sp:320})}
        else if(m.k>=0){S.fanfare();api.float(m.x,TB-30,'+'+n,{size:30,c:'#f3c84b'});api.burst(m.x,TB,{c:['#f08a8a','#fff','#f4d66d'],n:16,shape:'star'})}
        else{S.coin(1+Math.min(api.combo,12)*.04);api.float(m.x,TB-20,'+1',{size:18})}}}
    st.comboT=(st.comboT||0)-dt;if(st.comboT<=0)api.combo=0;
    for(let i=st.fallFx.length-1;i>=0;i--){st.fallFx[i].t+=dt;if(st.fallFx[i].t>.6)st.fallFx.splice(i,1)}
    if(st.stock<=0&&st.rain<=0){st.idle+=dt;if(st.idle>4.5)api.end()}else st.idle=0},
  drawHud(c,api){const st=this.st;D.rrect(c,90,20,240,58,29,'#fffdf8',3.5);this.medal(c,122,49,17);D.text(c,'手持ち '+st.stock,220,49,24,'#5b4d45');
    
    if(st.stock<=0&&st.rain<=0&&api.state==='play')D.text(c,'メダル切れ… あと'+Math.ceil(4.5-st.idle)+'秒',W/2,H-30,20,'#e2645a','center','#fffdf8',5)},
  draw(c,api){const st=this.st;c.fillStyle='#f3e2cf';c.fillRect(0,0,W,H);
    D.rrect(c,TL-22,110,TR-TL+44,TB-90,20,'#c98a5b',4);
    c.fillStyle='#8fc1a4';c.fillRect(TL,PZ-60,TR-TL,TB-PZ+60);
    c.fillStyle='#7fb394';for(let y=PZ;y<TB;y+=40)c.fillRect(TL,y,TR-TL,2);
    // すみの穴
    c.fillStyle='#5b4d45';c.fillRect(TL,TB-4,50,8);c.fillRect(TR-50,TB-4,50,8);
    D.rrect(c,TL+50,TB-6,TR-TL-100,14,6,'#f4d66d',3);
    const f=this.plate();D.rrect(c,TL-4,100,TR-TL+8,f-100,8,'#e9d3b5',4);c.fillStyle='#d6b994';c.fillRect(TL,f-14,TR-TL,10);
    D.text(c,'ここをタップしてメダルを落とす',W/2,128,15,'#8e7a69');D.text(c,'ゲット '+st.got+'枚',W/2,f-36,18,'#a58564');
    const ms=st.m.slice().sort((a,b)=>a.k-b.k);
    for(const m of ms){const s=1+(m.z||0)*.6;c.globalAlpha=1-(m.z||0)*.4;if(m.k<0)this.medal(c,m.x,m.y,m.r*s);else this.prize(c,m.x,m.y,m.r*s,m.k);c.globalAlpha=1}
    // 受け皿
    D.rrect(c,20,TB+20,W-40,90,22,'#e9cfa8',4);D.text(c,'うけざら',W/2,TB+40,15,'#a58564');
    for(const fx of st.fallFx){const k=fx.t/.6;c.globalAlpha=1-k;const y=fx.y+k*70;if(fx.k<0)this.medal(c,fx.x,y,fx.r*(1-k*.3));else this.prize(c,fx.x,y,fx.r,fx.k);if(fx.lost)D.text(c,'×',fx.x,y-20,16,'#e2645a');c.globalAlpha=1}
  },
  __bot(api){if(Math.random()<.35)this.down(rnd(TL+20,TR-20),140,api)},
};
