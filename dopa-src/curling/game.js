/* つるつるカーリング：縦長のシート。投げた後、こすると摩擦が減る。相手の石は固定で配置。 */
const HX=W/2,HY=200,SX=W/2,SY=640,N=6;
const GAME={...META,sprites:['icon','stone'],unit:'点',fullBleed:true,comboHud:false,
  bgm:{bpm:96,root:62,scale:'major',prog:[1,4,5,1],seed:36,lead:'triangle',drums:'pop',density:.45},
  ranks:[[0,'つるん'],[30,'カーリング初心者'],[60,'まずまず'],[100,'ストーンの使い手'],[150,'氷上の達人'],[220,'カーリングの神']],
  shareText:(v,f)=>`つるつるカーリングで ${f}点！`,
  icon(c,x,y,s){for(const[r,col]of[[.42,'#7fb2e0'],[.3,'#fbf7f0'],[.18,'#e2645a']])D.circle(c,x,y,s*r,col,3);this.stone(c,x+s*.08,y+s*.22,s*.14,'#f2a5c0')},
  stone(c,x,y,r,col){D.ellipse(c,x,y+r*.1,r,r*.8,'#8a8392');D.ellipse(c,x,y-r*.1,r*.95,r*.7,col);D.rrect(c,x-r*.3,y-r*.5,r*.6,r*.25,r*.1,'#5b4d45',0);D.face(c,x,y,r*1.05)},
  reset(api){this.st={n:0,s:[],cur:null,wait:0,sw:null,brush:0,res:[],t:0};for(let i=0;i<3;i++)this.st.s.push({x:HX+rnd(-90,90),y:HY+rnd(-40,60),vx:0,vy:0,me:false});api.score=0},
  down(x,y){const st=this.st;if(st.cur){st.brush=Math.min(1,st.brush+.35);S.noise(.08,{v:.25,f:1500,type:'highpass'});st.bx=x;st.by=y;return}if(st.wait>0||st.n>=N)return;st.sw={x,y,t:performance.now()}},
  move(x,y){const st=this.st;if(st.cur){st.brush=Math.min(1,st.brush+.08);st.bx=x;st.by=y;if(Math.random()<.3)S.noise(.05,{v:.15,f:1800,type:'highpass'})}},
  up(x,y,api){const st=this.st,s=st.sw;st.sw=null;if(!s||st.cur||st.wait>0||st.n>=N)return;const dx=x-s.x,dy=y-s.y;if(dy>-30)return;const dt=Math.max(60,performance.now()-s.t);const v=clamp(Math.hypot(dx,dy)/dt*1000,250,900);const a=Math.atan2(dy,dx);
    st.cur={x:SX,y:SY,vx:Math.cos(a)*v,vy:Math.sin(a)*v,me:true};st.s.push(st.cur);st.n++;S.whoosh()},
  key(k,api){const st=this.st;if(k===' '&&!st.cur&&st.wait<=0&&st.n<N){st.cur={x:SX,y:SY,vx:rnd(-20,20),vy:-rnd(500,700),me:true};st.s.push(st.cur);st.n++}},
  update(dt,api){const st=this.st;st.t+=dt;st.brush=Math.max(0,st.brush-dt*1.5);if(st.wait>0){st.wait-=dt;return}
    const fr=st.cur?Math.pow(st.brush>0?.75:.5,dt):1;
    for(const s of st.s){s.x+=s.vx*dt;s.y+=s.vy*dt;const f=s===st.cur?fr:Math.pow(.5,dt);s.vx*=f;s.vy*=f;if(s.x<30||s.x>W-30)s.vx*=-.6;if(s.y<70||s.y>H+40)s.out=true}
    for(let i=0;i<st.s.length;i++)for(let j=i+1;j<st.s.length;j++){const a=st.s[i],b=st.s[j];const d=dist(a.x,a.y,b.x,b.y);if(d<44&&d>0){const nx=(b.x-a.x)/d,ny=(b.y-a.y)/d,rv=(a.vx-b.vx)*nx+(a.vy-b.vy)*ny;if(rv>0){a.vx-=nx*rv;a.vy-=ny*rv;b.vx+=nx*rv;b.vy+=ny*rv;S.tone(700,.06,{type:'square',v:.2});S.noise(.05,{v:.3,f:2500});api.shake(3)}const o=(44-d)/2;a.x-=nx*o;a.y-=ny*o;b.x+=nx*o;b.y+=ny*o}}
    const before=st.s.length;const outs=st.s.filter(s=>s.out&&!s.me).length;st.s=st.s.filter(s=>!s.out);if(outs){api.add(outs*15);S.coin();api.float(W/2,HY+120,'はじき出し！ +'+outs*15,{size:24,c:'#f3c84b'})}
    if(st.cur&&Math.hypot(st.cur.vx,st.cur.vy)<8){const c=st.cur;st.cur=null;const d=dist(c.x,c.y,HX,HY);let pts=d<15?50:d<45?30:d<80?20:d<120?10:0;
      api.add(pts);st.res.push(pts);st.wait=.9;if(pts>=30){S.perfect();api.flash('#fff',.3);api.burst(c.x,c.y,{c:['#f4d66d','#fff'],n:16,shape:'star'})}else if(pts)S.good();else S.tap(.5);api.float(c.x,c.y-40,pts?'+'+pts:'とどかず…',{size:pts>=30?30:22,c:pts>=30?'#f3c84b':'#fff'})}
    if(st.n>=N&&!st.cur){st.endT=(st.endT||0)+dt;if(st.endT>1.4)api.end()}},
  drawHud(c,api){const st=this.st;D.rrect(c,70,20,280,56,28,'#fffdf8',3.5);D.text(c,api.score+'点　'+st.n+'/'+N+'投',W/2,48,22,'#5b4d45')},
  draw(c,api){const st=this.st;c.fillStyle='#d6e5f0';c.fillRect(0,api.top,W,api.bottom-api.top);D.rrect(c,20,api.top-10,W-40,api.bottom-api.top+20,0,'#eef5fb',4);
    for(const[r,col]of[[120,'#7fb2e0'],[80,'#fbf7f0'],[45,'#e2645a'],[15,'#fbf7f0']])D.circle(c,HX,HY,r,col,3);
    c.strokeStyle='#a9c7e6';c.lineWidth=3;c.beginPath();c.moveTo(20,SY+40);c.lineTo(W-20,SY+40);c.stroke();
    const ss=st.s.slice().sort((a,b)=>a.y-b.y);for(const s of ss)this.stone(c,s.x,s.y,22,s.me?'#f2a5c0':'#f2c84b');
    if(!st.cur&&st.n<N&&st.wait<=0)this.stone(c,SX,SY,22,'#f2a5c0');
    if(st.cur&&st.brush>0){const bx=st.bx||st.cur.x,by=st.by||st.cur.y;D.rrect(c,bx-30,by-8,60,16,8,'#e3b47a',3);c.globalAlpha=.6;for(let i=0;i<4;i++)D.circle(c,st.cur.x+rnd(-20,20),st.cur.y-30+rnd(-10,10),3,'#fff',0);c.globalAlpha=1}
    if(api.t<3&&api.state==='play')D.text(c,'↑ 上へスワイプ。すべってる間にこする',W/2,SY+70,15,'#5b4d45','center','#fffdf8',5)},
  __bot(api){const st=this.st;if(st.cur){if(Math.random()<.5)this.move(st.cur.x,st.cur.y);return}if(st.wait>0||st.n>=N)return;st.cur={x:SX,y:SY,vx:rnd(-30,30),vy:-rnd(480,640),me:true};st.s.push(st.cur);st.n++},
};
