/* くしゃくしゃポイ：疑似3Dの紙くず投げ。x=左右 y=高さ z=奥行き（メートル）。 */
const F=640,ZC=1.6,CAMH=1.35,HOR=300,G=9.8,BRm=.07;
const GAME={...META,sprites:['icon','can','paper'],unit:'回',hudUnit:true,fullBleed:true,comboHud:false,
  bgm:{bpm:104,root:60,scale:'major',prog:[1,4,2,5],seed:8,lead:'triangle',drums:'pop',density:.5},
  ranks:[[0,'ポイすて注意'],[3,'ナイスイン'],[7,'ゴミ箱名人'],[12,'風よみの達人'],[18,'スポッの神'],[25,'伝説のシューター']],
  shareText:(v,f)=>`くしゃくしゃポイで ${f}回 入った！`,
  icon(c,x,y,s){this.can(c,x,y+s*.4,s*.5,s*.55);this.paper(c,x+s*.18,y-s*.32,s*.13,1);c.setLineDash([6,8]);c.lineWidth=3;c.strokeStyle='#b0a59b';c.beginPath();c.moveTo(x-s*.42,y+s*.1);c.quadraticCurveTo(x-s*.2,y-s*.5,x+s*.08,y-s*.36);c.stroke();c.setLineDash([])},
  proj(x,y,z){const d=z+ZC;return[W/2+x*F/d,HOR+(CAMH-y)*F/d,F/d]},
  can(c,x,y,w,h){D.path(c,c=>{c.moveTo(x-w/2,y-h);c.lineTo(x-w*.4,y);c.lineTo(x+w*.4,y);c.lineTo(x+w/2,y-h);c.closePath()},'#8fc1a4');
    c.strokeStyle='#7fb394';c.lineWidth=Math.max(1.5,w*.03);for(const k of[-.22,0,.22]){c.beginPath();c.moveTo(x+k*w,y-h*.85);c.lineTo(x+k*w*.85,y-h*.1);c.stroke()}
    D.ellipse(c,x,y-h,w/2,w*.16,'#4b3e37');D.ellipse(c,x,y-h,w/2,w*.16,null);D.face(c,x,y-h*.45,w*.45)},
  paper(c,x,y,r,rot){c.save();c.translate(x,y);c.rotate(rot);D.path(c,c=>{for(let i=0;i<9;i++){const a=i/9*Math.PI*2,rr=r*(i%2?.86:1.04);i?c.lineTo(Math.cos(a)*rr,Math.sin(a)*rr):c.moveTo(Math.cos(a)*rr,Math.sin(a)*rr)}c.closePath()},'#fbfaf6',Math.max(2,r*.13));
    c.strokeStyle='#c9bfb4';c.lineWidth=Math.max(1,r*.07);c.beginPath();c.moveTo(-r*.5,-r*.2);c.lineTo(0,r*.1);c.lineTo(r*.4,-r*.35);c.moveTo(-r*.2,r*.5);c.lineTo(r*.1,r*.15);c.stroke();c.restore()},
  reset(api){this.st={b:null,miss:0,made:0,cz:3,cx:0,wind:0,t:0,res:null,trail:[]};this.setup();api.score=0},
  setup(){const st=this.st,m=st.made;st.cz=Math.min(7,3+m*.25);st.cx=m<3?0:rnd(-.6,.6)*Math.min(1,m/8);st.wind=m<2?0:rnd(-1,1)*Math.min(3.5,.5+m*.25);st.wind=Math.round(st.wind*10)/10;st.b=null;st.res=null},
  down(x,y){if(this.st.b)return;this.st.sw={x,y,t:performance.now(),pts:[[x,y,performance.now()]]}},
  move(x,y){const s=this.st.sw;if(s)s.pts.push([x,y,performance.now()])},
  up(x,y,api){const st=this.st,s=st.sw;st.sw=null;if(!s||st.b)return;const now=performance.now();let p0=s.pts[0];for(const p of s.pts)if(now-p[2]<140){p0=p;break}
    const dt=Math.max(30,now-p0[2])/1000,dy=p0[1]-y,dx=x-p0[0];if(dy<30)return;const vup=dy/dt;
    this.throwB(clamp(vup/280,1.6,9.5),dx/dt/420,api)},
  throwB(vz,vx,api){const st=this.st;st.b={x:0,y:1,z:0,vx:clamp(vx,-2.5,2.5),vy:vz*.62,vz,rot:0,above:true};st.trail=[];S.whoosh()},
  key(k,api){const st=this.st;if(st.b)return;st.kp=st.kp??4;st.kx=st.kx??0;if(k==='ArrowUp')st.kp+=.2;if(k==='ArrowDown')st.kp-=.2;if(k==='ArrowLeft')st.kx-=.1;if(k==='ArrowRight')st.kx+=.1;if(k===' ')this.throwB(st.kp,st.kx,api)},keyRepeat:true,
  update(dt,api){const st=this.st;st.t+=dt;const b=st.b;
    if(st.res){st.res.t-=dt;if(st.res.t<=0){if(st.miss>=3){api.end();return}this.setup()}}
    if(!b||st.res)return;const sub=5,h=dt/sub,R=.26,CH=.6;
    for(let s=0;s<sub;s++){const py=b.y;b.vx+=st.wind*.45*h;b.vy-=G*h;b.x+=b.vx*h;b.y+=b.vy*h;b.z+=b.vz*h;b.rot+=h*8;
      const d=Math.hypot(b.x-st.cx,b.z-st.cz);
      if(py>=CH&&b.y<CH){if(d<R-BRm*.5){this.result(true,api);return}if(d<R+BRm){// ふちに当たる
          S.tap(.8);api.shake(3);const nx=(b.x-st.cx)/d,nz=(b.z-st.cz)/d;b.vx=nx*1.2+b.vx*.2;b.vz=nz*1.2;b.vy=Math.abs(b.vy)*.35;b.y=CH+.01;if(Math.random()<.35){b.x=st.cx;b.z=st.cz;}}}
      if(b.y<CH&&d<R+BRm&&d>R-BRm*.5&&py<CH){const nx=(b.x-st.cx)/d,nz=(b.z-st.cz)/d;b.x=st.cx+nx*(R+BRm);b.z=st.cz+nz*(R+BRm);b.vx=nx*.8;b.vz=nz*.8;S.tap(.5)}
      if(b.y<BRm){this.result(false,api);return}}
    const[sx,sy]=this.proj(b.x,b.y,b.z);st.trail.push([sx,sy]);if(st.trail.length>14)st.trail.shift()},
  result(ok,api){const st=this.st;st.res={ok,t:ok?1.1:1.2};
    if(ok){st.made++;api.score=st.made;const[sx,sy]=this.proj(st.cx,.6,st.cz);S.perfect();api.burst(sx,sy,{c:['#f4d66d','#fff','#9cc86a'],n:16,shape:'star',sp:220});api.float(sx,sy-60,pick(['スポッ！','ナイス！','イン！']),{size:34,c:'#f3c84b'});if(st.made%5===0){S.fanfare();api.flash('#fff',.4);api.float(W/2,250,st.made+'回！',{size:40,c:'#f3c84b'})}}
    else{st.miss++;S.bad();api.float(W/2,360,'はずれ…',{size:30})}},
  drawHud(c,api){const st=this.st;D.rrect(c,70,20,280,56,28,'#fffdf8',3.5);D.text(c,st.made+'回',150,48,26,'#5b4d45');
    for(let i=0;i<3;i++){D.text(c,'×',250+i*32,48,26,i<st.miss?'#e2645a':'#e3dad1')}
    const w=st.wind;D.rrect(c,130,88,160,40,20,'#fffdf8',3);D.text(c,'かぜ',165,108,15,'#8e8077');
    if(w===0)D.text(c,'なし',235,108,17,'#5b4d45');else{D.text(c,Math.abs(w).toFixed(1),250,108,17,'#5b4d45');const ax=208,dir=Math.sign(w);c.lineWidth=4;c.strokeStyle='#6fa6c9';c.lineCap='round';c.beginPath();c.moveTo(ax-12*dir,108);c.lineTo(ax+12*dir,108);c.moveTo(ax+12*dir,108);c.lineTo(ax+4*dir,101);c.moveTo(ax+12*dir,108);c.lineTo(ax+4*dir,115);c.stroke()}},
  draw(c,api){const st=this.st;c.fillStyle='#efe9df';c.fillRect(0,api.top,W,HOR+20-api.top);
    c.fillStyle='#d8cdbd';c.fillRect(0,HOR-40,W,60);c.fillStyle='#e8dccb';c.fillRect(0,HOR+20,W,api.bottom-HOR-20);
    c.strokeStyle='#dccfba';c.lineWidth=2;for(let z=0;z<12;z+=1){const[,y]=this.proj(0,0,z);c.beginPath();c.moveTo(0,y);c.lineTo(W,y);c.stroke()}
    // 風のすじ
    if(st.wind){c.strokeStyle='rgba(111,166,201,.35)';c.lineWidth=3;for(let i=0;i<5;i++){const x=((st.t*st.wind*60+i*97)%(W+80)+W+80)%(W+80)-40,y=140+i*40;c.beginPath();c.moveTo(x,y);c.lineTo(x+30*Math.sign(st.wind),y);c.stroke()}}
    const[cx,cy,k]=this.proj(st.cx,0,st.cz);const b=st.b;
    const drawBall=()=>{if(!b)return;const[bx,by,bk]=this.proj(b.x,b.y,b.z);const[,gy]=this.proj(b.x,0,b.z);c.globalAlpha=.15;D.ellipse(c,bx,gy,BRm*bk,BRm*bk*.3,'#5b4d45',0);c.globalAlpha=1;this.paper(c,bx,by,Math.max(5,BRm*bk*1.2),b.rot)};
    const inCan=st.res&&st.res.ok;if(b&&b.z>st.cz&&!inCan)drawBall();
    c.globalAlpha=.15;D.ellipse(c,cx,cy,.3*k,.08*k,'#5b4d45',0);c.globalAlpha=1;this.can(c,cx,cy,.52*k,.6*k);
    if(b&&b.z<=st.cz&&!inCan)drawBall();
    if(!b){const[bx,by,bk]=this.proj(0,1,0);this.paper(c,bx,by+Math.sin(st.t*3)*3,BRm*bk*1.2,0);if(st.made===0&&st.miss===0&&api.state==='play')D.text(c,'↑ 上にシュッとスワイプ',W/2,by+70,18,'#5b4d45','center','#fffdf8',5)}
    D.text(c,(st.cz).toFixed(1)+'m',cx,cy+22,14,'#8e8077')},
  __bot(api){const st=this.st;if(st.b||st.res)return;const t=1;// だいたいの初速
    const vz=Math.sqrt(4.9*st.cz*st.cz/(.62*st.cz+.4))*rnd(.97,1.04);const tt=st.cz/vz;this.throwB(vz,(st.cx-st.wind*.45*tt*tt/2)/tt*rnd(.9,1.1),api)},
};
