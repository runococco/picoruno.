/* ぽよんダイブ：Helix Jump を横スクロールにした版。全床が同じだけスライドする。 */
const L=W,FH=170,BY0=200,BALLX=W/2,BR=16,TH=22;
const FC=['#8fcfc4','#a9c8e8','#c6b4e4','#f3c48a','#a9d68f'];
const GAME={...META,unit:'段',hudUnit:true,
  bgm:{bpm:138,root:60,scale:'major',prog:[1,6,4,5],seed:52,lead:'square',drums:'four',density:.6},
  ranks:[[0,'ころころ初心者'],[10,'ぽよんの子'],[25,'すとん名人'],[45,'ダイブの達人'],[70,'地底探検家'],[100,'地球のうら側']],
  shareText:(v,f)=>`ぽよんダイブで ${f}段 落ちた！`,
  icon(c,x,y,s){D.rrect(c,x-s*.45,y+s*.2,s*.32,s*.08,s*.04,'#8fcfc4',s*.02);D.rrect(c,x+s*.05,y+s*.2,s*.4,s*.08,s*.04,'#e2645a',s*.02);this.ball(c,x-s*.04,y-s*.1,s*.14,0)},
  ball(c,x,y,r,sq){c.save();c.translate(x,y);c.scale(1+sq,1-sq);D.circle(c,0,0,r,'#f6d26a',Math.max(2,r*.18));D.face(c,0,r*.1,r*1.2,'smile');c.restore()},
  reset(api){this.st={off:0,floors:[],y:BY0-80,vy:0,cam:0,chain:0,sq:0,trail:[],dead:false,px:null,lv:0};for(let i=0;i<8;i++)this.addFloor();api.score=0},
  addFloor(){const st=this.st,i=st.floors.length,y=BY0+i*FH,lv=Math.min(i,60);
    const segs=[];const gw=Math.max(70,110-lv*.6),gx=rnd(L);segs.push({a:gx,b:gx+gw,t:'gap'});
    if(i>0){const nd=Math.min(3,Math.floor(lv/8)+(lv>2?1:0));for(let k=0;k<nd;k++){const w=rnd(50,70+lv*.8);let a;let tries=0;do{a=rnd(L);tries++}while(tries<30&&segs.some(s=>this.ov(a-10,a+w+10,s.a,s.b)));if(tries<30)segs.push({a,b:a+w,t:'red'})}}
    else segs[0].a=(L/2-st.off-gw/2),segs[0].b=segs[0].a+gw;
    st.floors.push({y,segs,col:FC[i%FC.length],broken:0,passed:false,phase:(i%3===1?1:0)})},
  ov(a1,b1,a2,b2){for(const s of[-L,0,L])if(a1<b2+s&&a2+s<b1)return true;return false},
  typeAt(f,x){const u=((x-this.st.off)%L+L)%L;for(const s of f.segs){for(const sh of[-L,0,L]){if(u>=s.a+sh&&u<=s.b+sh)return s.t}}return 'n'},
  down(x){this.st.px=x},move(x){const st=this.st;if(st.px===null)return;st.off+=(x-st.px)*1.1;st.px=x},up(){this.st.px=null},
  key(k){if(k==='ArrowLeft')this.st.off-=30;if(k==='ArrowRight')this.st.off+=30},keyRepeat:true,
  update(dt,api){const st=this.st;if(st.dead)return;const py=st.y;st.vy=Math.min(900,st.vy+1700*dt);st.y+=st.vy*dt;st.sq=lerp(st.sq,0,1-Math.pow(.001,dt));
    for(const f of st.floors){if(f.broken)continue;if(py+BR<=f.y&&st.y+BR>f.y){const t=this.typeAt(f,BALLX);
      if(t==='gap'){if(!f.passed){f.passed=true;st.chain++;api.score++;api.combo=st.chain;S.whoosh();if(st.chain>=2)S.combo(st.chain*2);api.float(BALLX+60,f.y-st.cam,st.chain>=3?'スマッシュ準備！':'+1',{size:st.chain>=3?20:22,c:st.chain>=3?'#f3c84b':'#fff'})}}
      else if(st.chain>=3){f.broken=1;api.score+=2;S.boom();api.shake(12);api.flash('#fff',.4);api.float(BALLX,f.y-st.cam-40,'ドカーン！ +2',{size:32,c:'#f3c84b'});api.burst(BALLX,f.y-st.cam,{c:[f.col,'#e2645a','#fff'],n:30,sp:380,shape:'s',r:7});f.passed=true;st.chain=0;api.combo=0;st.y=f.y-BR;st.vy=-430}
      else if(t==='red'){this.die(api);return}
      else{st.y=f.y-BR;st.vy=-560;st.sq=.3;st.chain=0;api.combo=0;S.boing(1.2);api.burst(BALLX,f.y-st.cam,{c:['#fff',f.col],n:6,sp:140,r:4});
        f.splat=(f.splat||[]);f.splat.push(((BALLX-st.off)%L+L)%L)}}}
    const target=st.y-260;st.cam=Math.max(st.cam,lerp(st.cam,target,1-Math.pow(.01,dt)));
    if(st.floors[st.floors.length-1].y<st.cam+H+200)this.addFloor();
    st.trail.push({x:BALLX,y:st.y});if(st.trail.length>8)st.trail.shift()},
  die(api){const st=this.st;st.dead=true;S.bad();S.boom();api.shake(14);api.flash('#e2645a',.4);api.burst(BALLX,st.y-st.cam,{c:['#f6d26a','#fff'],n:30,sp:380});api.end()},
  overText:'赤にあたった！',
  draw(c,api){const st=this.st;c.fillStyle=this.bg;c.fillRect(0,0,W,H);
    c.fillStyle='#d6e8e5';for(let i=0;i<10;i++){const y=((i*120-st.cam*.4)%1200+1200)%1200-100;c.fillRect(0,y,W,50)}
    c.save();c.translate(0,-st.cam);
    // 中央の柱
    c.fillStyle='#cfe1de';c.fillRect(W/2-30,st.cam-50,60,H+100);
    for(const f of st.floors){if(f.y<st.cam-60||f.y>st.cam+H+60)continue;
      if(f.broken){continue}
      const sh=((st.off%L)+L)%L;
      // 通常床
      const g=f.segs.find(q=>q.t==='gap');
      for(const k of[-2,-1,0,1]){const x=sh+k*L+g.b,w=L-(g.b-g.a);if(x>W+20||x+w<-20)continue;D.rrect(c,x,f.y,w,TH,8,f.col,3.5)}
      for(const q of f.segs){if(q.t!=='red')continue;for(const k of[-2,-1,0,1]){const x=sh+k*L+q.a,w=q.b-q.a;if(x>W+20||x+w<-20)continue;D.rrect(c,x,f.y,w,TH,6,'#e2645a',3.5)}}
      if(f.splat)for(const u of f.splat)for(const k of[-1,0,1]){const x=sh+k*L+u;c.fillStyle='rgba(246,210,106,.7)';c.beginPath();c.ellipse(x,f.y+3,12,3,0,0,7);c.fill()}}
    if(!st.dead){c.globalAlpha=.3;st.trail.forEach((p,i)=>D.circle(c,p.x,p.y,BR*(i/8),'#f6d26a',0));c.globalAlpha=1;this.ball(c,BALLX,st.y,BR,st.sq);if(st.chain>=3){c.lineWidth=4;c.strokeStyle=`hsl(${api.t*600%360},80%,60%)`;c.beginPath();c.arc(BALLX,st.y,BR+7,0,7);c.stroke()}}
    c.restore();
    if(api.state==='play'&&api.t<2.5)D.text(c,'← 左右になぞる →',W/2,H-60,22,'#fff','center',OL,6);
  },
  __bot(api){const st=this.st;const f=st.floors.find(f=>!f.broken&&f.y>st.y);if(!f)return;const g=f.segs.find(s=>s.t==='gap');const u=((BALLX-st.off)%L+L)%L,mid=(g.a+g.b)/2;let d=mid-u;d=((d+L/2)%L+L)%L-L/2;st.off-=clamp(d,-25,25)},
};
