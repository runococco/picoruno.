/* ぬいぐるみキャッチャー：横から見たクレーンゲーム。ぬいぐるみは円の物理で山になる。 */
const FL=570,CH=118,CX0=70,TOPY=170,PLAYS=12;
const KINDS=[{c:'#fbf7f0',n:'おばけ'},{c:'#f4d66d',n:'ほし'},{c:'#a9d6e6',n:'くも'},{c:'#f2a5b5',n:'だんご'},{c:'#9cc86a',n:'まりも'},{c:'#c9a0e0',n:'ぶどうゼリー'}];
const GAME={...META,sprites:['icon','plush'],unit:'個',hudUnit:true,comboHud:false,
  bgm:{bpm:116,root:60,scale:'major',prog:[1,6,2,5],seed:88,lead:'triangle',drums:'pop',density:.55},
  ranks:[[0,'おしい！'],[2,'はじめてのゲット'],[4,'キャッチャー上手'],[7,'アームの使い手'],[10,'ゲーセンの主'],[15,'UFOマスター']],
  shareText:(v,f)=>`ぬいぐるみキャッチャーで ${f}個 ゲット！`,
  icon(c,x,y,s){this.claw(c,x,y-s*.25,s*.5,.3);this.plush(c,x,y+s*.15,s*.2,1,false)},
  plush(c,x,y,r,k,gold,rot=0){c.save();c.translate(x,y);c.rotate(rot);const col=gold?'#f2c84b':KINDS[k].c,lw=Math.max(2.5,r*.1);
    if(k===0){D.path(c,c=>{c.arc(0,-r*.1,r*.9,Math.PI,0);c.lineTo(r*.9,r*.8);for(let i=0;i<4;i++){const x0=r*.9-i*r*.45;c.quadraticCurveTo(x0-r*.11,r*.55,x0-r*.22,r*.8);c.quadraticCurveTo(x0-r*.33,r*1.05,x0-r*.45,r*.8)}c.closePath()},col,lw)}
    else if(k===1)D.star(c,0,0,r*1.15,col,lw,0,5,.58);
    else if(k===2){D.path(c,c=>{c.arc(-r*.45,r*.15,r*.55,Math.PI*.5,Math.PI*1.5);c.arc(0,-r*.3,r*.6,Math.PI*1.1,Math.PI*1.9);c.arc(r*.5,r*.1,r*.55,Math.PI*1.5,Math.PI*.5);c.closePath()},col,lw)}
    else if(k===3){D.circle(c,0,0,r,col,lw)}
    else if(k===4){D.circle(c,0,0,r,col,lw);c.strokeStyle='#7aa850';c.lineWidth=2;for(let i=0;i<6;i++){const a=i*1.05;c.beginPath();c.moveTo(Math.cos(a)*r*.7,Math.sin(a)*r*.7);c.lineTo(Math.cos(a)*r*.85,Math.sin(a)*r*.85);c.stroke()}}
    else{D.path(c,c=>{c.moveTo(-r*.9,r*.8);c.lineTo(-r*.7,-r*.6);c.quadraticCurveTo(0,-r*1.05,r*.7,-r*.6);c.lineTo(r*.9,r*.8);c.closePath()},col,lw)}
    D.face(c,0,r*.1,r*.95,gold?'o':'smile');c.restore()},
  claw(c,x,y,s,open){c.lineWidth=4;c.strokeStyle=OL;c.beginPath();c.moveTo(x,Math.min(y,y-400<124?124:y-400));c.lineTo(x,y);c.stroke();
    D.rrect(c,x-s*.3,y-s*.12,s*.6,s*.3,s*.08,'#b9c3cc',3.5);
    for(const sg of[-1,1]){c.save();c.translate(x+sg*s*.22,y+s*.15);c.rotate(sg*(.15+open*.6));D.path(c,c=>{c.moveTo(-3,0);c.lineTo(3,0);c.lineTo(sg*-s*.05+3,s*.45);c.lineTo(sg*-s*.22,s*.62);c.lineTo(sg*-s*.18,s*.52);c.lineTo(-3,s*.4);c.closePath()},'#b9c3cc',3);c.restore()}},
  reset(api){const st=this.st={p:[],plays:PLAYS,ph:'ready',cx:CX0,cy:TOPY,open:.5,held:null,got:0,t:0,shake:0};
    for(let i=0;i<14;i++)st.p.push({x:rnd(CH+40,380),y:rnd(320,560),vx:0,vy:0,r:rnd(27,36),k:rndi(0,5),gold:i<2,rot:0});
    for(let i=0;i<200;i++)this.phys(1/60);api.score=0},
  phys(dt){const st=this.st,P=st.p;
    for(const p of P){if(p===st.held)continue;p.vy+=900*dt;p.vx*=.98;p.x+=p.vx*dt;p.y+=p.vy*dt;
      if(p.x>CH-4){if(p.y+p.r>FL){p.y=FL-p.r;p.vy*=-.2;p.vx*=.85}}
      if(p.x<CH+p.r&&p.x>CH-p.r&&p.y+p.r>FL-56){// 仕切りのへり
        if(p.x>CH){p.x=CH+p.r;p.vx=Math.abs(p.vx)*.3}else{p.x=Math.min(p.x,CH-p.r)}}
      if(p.x+p.r>392){p.x=392-p.r;p.vx*=-.3}if(p.x-p.r<28){p.x=28+p.r;p.vx*=-.3}}
    for(let it=0;it<3;it++)for(let i=0;i<P.length;i++)for(let j=i+1;j<P.length;j++){const a=P[i],b=P[j];if(a===st.held||b===st.held)continue;const dx=b.x-a.x,dy=b.y-a.y,rr=(a.r+b.r)*.92,d=Math.hypot(dx,dy)||.01;
      if(d<rr){const o=(rr-d)/2,nx=dx/d,ny=dy/d;a.x-=nx*o;a.y-=ny*o;b.x+=nx*o;b.y+=ny*o;const rv=(b.vx-a.vx)*nx+(b.vy-a.vy)*ny;if(rv<0){a.vx+=rv*nx*.5;a.vy+=rv*ny*.5;b.vx-=rv*nx*.5;b.vy-=rv*ny*.5}}}},
  down(x,y,api){const st=this.st;if(st.ph==='ready'&&st.plays>0){st.ph='right';st.plays--;S.coin();st.pressed=true}},
  up(x,y,api){const st=this.st;st.pressed=false;if(st.ph==='right'){st.ph='drop';S.whoosh()}},
  key(k,api){if(k===' ')this.down(0,0,api)},keyUp(k,api){if(k===' ')this.up(0,0,api)},
  update(dt,api){const st=this.st;st.t+=dt;this.phys(dt);
    // 取り出し口に落ちたもの
    for(let i=st.p.length-1;i>=0;i--){const p=st.p[i];if(p.y-p.r>FL+10&&p.x<CH){st.p.splice(i,1);const n=p.gold?3:1;st.got+=n;api.add(n);
        S.fanfare();api.flash('#fff',.4);api.float(70,FL-60,p.gold?'金だ！ +3':'ゲット！',{size:30,c:'#f3c84b',life:1.2});api.burst(70,FL,{c:['#f2a5b5','#f4d66d','#fff'],n:24,shape:'star',sp:300});
        if(st.p.length<8)st.p.push({x:rnd(200,380),y:200,vx:0,vy:0,r:rnd(27,36),k:rndi(0,5),gold:Math.random()<.2,rot:0})}}
    const sp=150;
    if(st.ph==='right'){st.cx=Math.min(372,st.cx+sp*dt);if(Math.floor(st.t*8)!==Math.floor((st.t-dt)*8))S.tick();if(st.cx>=372){st.ph='drop';S.whoosh()}}
    else if(st.ph==='drop'){st.open=Math.min(1,st.open+dt*3);st.cy+=200*dt;const tipY=st.cy+48;
      const under=st.p.some(p=>Math.abs(p.x-st.cx)<p.r*.7&&tipY>p.y-p.r*.4);if(under||tipY>FL-10){st.ph='close';st.ct=0}}
    else if(st.ph==='close'){st.ct+=dt;st.open=Math.max(0,1-st.ct*2.2);if(st.ct>.5){let best=null,bd=1e9;for(const p of st.p){const d=Math.abs(p.x-st.cx);if(d<p.r*.95&&Math.abs(p.y-(st.cy+48))<p.r*1.3&&d<bd){bd=d;best=p}}
        if(best){const ch=1-bd/best.r*.9-(best.r-28)/40;if(Math.random()<ch+.05){st.held=best;st.off=best.x-st.cx;S.good()}else{best.vx+=rnd(-80,80);best.vy-=120;S.tap(.5);api.float(st.cx,st.cy-20,'つるっ',{size:20})}}else S.tap(.5);st.ph='up'}}
    else if(st.ph==='up'){st.cy-=170*dt;if(st.held){st.held.x=st.cx+st.off*.6;st.held.y=st.cy+40+st.held.r*.7;st.held.vx=st.held.vy=0}
      if(st.cy<=TOPY){st.cy=TOPY;st.ph='back'}}
    else if(st.ph==='back'){st.cx=Math.max(CX0,st.cx-sp*dt);if(st.held){st.held.x=st.cx+st.off*.6;st.held.y=st.cy+40+st.held.r*.7;
        const slip=.12*Math.abs(st.off)/st.held.r+.04;if(Math.random()<slip*dt){st.held.vy=0;st.held=null;S.bad();api.float(st.cx,st.cy+40,'あっ…',{size:24});api.shake(4)}}
      if(st.cx<=CX0){st.ph='release';st.ct=0}}
    else if(st.ph==='release'){st.ct+=dt;st.open=Math.min(1,st.ct*3);if(st.held&&st.ct>.15){st.held.vy=50;st.held=null}if(st.ct>.7){st.ph='ready';st.open=.5;if(st.plays<=0)st.ph='end'}}
    else if(st.ph==='end'){st.ct+=dt;if(st.ct>2.2)api.end()}},
  drawHud(c,api){const st=this.st;D.rrect(c,70,20,280,56,28,'#fffdf8',3.5);D.text(c,'ゲット '+st.got+'　のこり '+st.plays+'回',W/2,48,22,'#5b4d45')},
  draw(c,api){const st=this.st;c.fillStyle='#f4dde4';c.fillRect(0,0,W,H);
    D.rrect(c,12,100,W-24,H-120,24,'#d97a9a',4);c.fillStyle='#f9eef2';c.fillRect(28,120,W-56,FL-120+56);
    c.fillStyle='#efd7e0';for(let i=0;i<7;i++)c.fillRect(28+i*60,120,30,FL-120);
    D.rrect(c,20,112,W-40,22,8,'#b9c3cc',3);
    // 床と取り出し口
    c.fillStyle='#c9b29a';c.fillRect(CH,FL,W-28-CH,56);c.strokeStyle=OL;c.lineWidth=3.5;c.strokeRect(CH,FL,W-28-CH,56);
    c.fillStyle='#5b4d45';c.fillRect(28,FL,CH-28,56);D.rrect(c,CH-8,FL-56,12,112,4,'#e9e3f0',3);
    D.text(c,'とりだし口',(28+CH)/2,FL+30,13,'#fffdf8');
    for(const p of st.p)if(p!==st.held)this.plush(c,p.x,p.y,p.r,p.k,p.gold,clamp(p.vx*.003,-.4,.4));
    if(st.held)this.plush(c,st.held.x,st.held.y,st.held.r,st.held.k,st.held.gold);
    this.claw(c,st.cx,st.cy,80,st.open);
    D.rrect(c,12,FL+68,W-24,H-FL-84,20,'#c9637f',4);
    const can=st.ph==='ready'||st.ph==='right';D.rrect(c,W/2-110,FL+78,220,44,22,can?'#fffdf8':'#e9e2d9',3);
    D.text(c,st.ph==='right'?'はなすとおりる！':st.ph==='ready'?'おしてアームを右へ':'……',W/2,FL+100,17,can?'#5b4d45':'#b0a59b')},
  __bot(api){const st=this.st;if(st.ph==='ready'){st.want=pick(st.p.filter(p=>p.x>CH+30)||st.p).x+rnd(-6,6);this.down(0,0,api)}if(st.ph==='right'&&st.cx>=st.want)this.up(0,0,api)},
};
