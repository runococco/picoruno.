/* ころころパター：真上から見たミニゴルフ9ホール。合計打数が少ないほどよい。 */
const CL=30,CR=390,CT=140,CB=690,BR=10,MAXS=6;
const HOLES=[
  {s:[210,620],cup:[210,220],w:[]},
  {s:[210,630],cup:[210,200],w:[[120,380,180,24]]},
  {s:[110,630],cup:[330,195],w:[[30,140,230,330]]},
  {s:[330,640],cup:[90,200],w:[[30,300,250,24],[140,470,250,24]]},
  {s:[210,640],cup:[210,200],w:[],sand:[[100,300,220,140]]},
  {s:[210,640],cup:[210,200],w:[],mv:{y:400,w:150,amp:110,sp:1.4}},
  {s:[210,640],cup:[210,195],w:[[30,260,155,320],[235,260,155,320]]},
  {s:[100,640],cup:[330,195],w:[[100,270,290,24]],sand:[[260,380,130,120]]},
  {s:[210,640],cup:[300,195],w:[[30,430,140,24],[250,430,140,24]],sand:[[30,150,120,110]],mv:{y:300,w:120,amp:120,sp:1.8}},
];
const GAME={...META,sprites:['icon','ball','flag'],unit:'打',lowerIsBetter:true,fullBleed:true,comboHud:false,
  validScore:v=>v>=9,
  bgm:{bpm:100,root:62,scale:'major',prog:[1,6,2,5],seed:15,lead:'triangle',drums:'pop',density:.5},
  ranks:[[99,'まだまだこれから'],[40,'ころころ見習い'],[30,'ナイスパット'],[22,'パターの名手'],[17,'グリーンの魔術師'],[13,'ホールインワン王']],
  shareText:(v,f)=>`ころころパターで 9ホールを ${f}打 でまわった！`,
  icon(c,x,y,s){D.ellipse(c,x,y+s*.25,s*.45,s*.14,'#9cc86a');D.ellipse(c,x+s*.12,y+s*.24,s*.12,s*.05,'#4b3e37');this.flag(c,x+s*.12,y+s*.24,s*.9);this.ball(c,x-s*.2,y+s*.18,s*.12)},
  ball(c,x,y,r){D.circle(c,x,y,r,'#fbf7f0');D.face(c,x,y+r*.05,r*1.1)},
  flag(c,x,y,h){c.lineWidth=Math.max(2,h*.03);c.strokeStyle=OL;c.beginPath();c.moveTo(x,y);c.lineTo(x,y-h*.6);c.stroke();D.poly(c,[[x,y-h*.6],[x+h*.3,y-h*.5],[x,y-h*.4]],'#e2645a',Math.max(2,h*.025))},
  reset(api){this.st={h:-1,strokes:0,total:0,t:0,ph:'aim',b:null,pull:null,res:[]};this.load(0);api.score=0},
  load(i){const st=this.st;st.h=i;const H0=HOLES[i];st.b={x:H0.s[0],y:H0.s[1],vx:0,vy:0};st.strokes=0;st.ph='aim';st.in=0},
  walls(){const st=this.st,H0=HOLES[st.h],w=H0.w.slice();if(H0.mv){const m=H0.mv,x=W/2+Math.sin(st.t*m.sp)*m.amp-m.w/2;w.push([x,m.y,m.w,22])}return w},
  down(x,y){const st=this.st;if(st.ph!=='aim')return;st.pull={x0:x,y0:y,x,y}},
  move(x,y){const p=this.st.pull;if(p){p.x=x;p.y=y}},
  up(x,y,api){const st=this.st,p=st.pull;st.pull=null;if(!p||st.ph!=='aim')return;const dx=p.x0-x,dy=p.y0-y,l=Math.hypot(dx,dy);if(l<12)return;const pw=Math.min(l,170)/170;this.hit(Math.atan2(dy,dx),pw,api)},
  hit(a,pw,api){const st=this.st;st.b.vx=Math.cos(a)*pw*1250;st.b.vy=Math.sin(a)*pw*1250;st.strokes++;st.total++;api.score=st.total;st.ph='roll';S.tone(300,.08,{type:'triangle',v:.4});S.noise(.04,{v:.4,f:2500})},
  key(k,api){const st=this.st;if(st.ph!=='aim')return;st.ka=st.ka??-Math.PI/2;st.kp=st.kp??.5;if(k==='ArrowLeft')st.ka-=.08;if(k==='ArrowRight')st.ka+=.08;if(k==='ArrowUp')st.kp=Math.min(1,st.kp+.05);if(k==='ArrowDown')st.kp=Math.max(.1,st.kp-.05);if(k===' ')this.hit(st.ka,st.kp,api)},keyRepeat:true,
  update(dt,api){const st=this.st;st.t+=dt;const b=st.b,H0=HOLES[st.h];
    if(st.ph==='roll'){const sub=6,h=dt/sub,ws=this.walls();for(let s=0;s<sub;s++){b.x+=b.vx*h;b.y+=b.vy*h;
        const inSand=(H0.sand||[]).some(r=>b.x>r[0]&&b.x<r[0]+r[2]&&b.y>r[1]&&b.y<r[1]+r[3]);const f=Math.pow(inSand?.04:.42,h);b.vx*=f;b.vy*=f;
        if(b.x<CL+BR){b.x=CL+BR;b.vx=Math.abs(b.vx)*.8;this.bonk()}if(b.x>CR-BR){b.x=CR-BR;b.vx=-Math.abs(b.vx)*.8;this.bonk()}
        if(b.y<CT+BR){b.y=CT+BR;b.vy=Math.abs(b.vy)*.8;this.bonk()}if(b.y>CB-BR){b.y=CB-BR;b.vy=-Math.abs(b.vy)*.8;this.bonk()}
        for(const r of ws){const cx=clamp(b.x,r[0],r[0]+r[2]),cy=clamp(b.y,r[1],r[1]+r[3]),dx=b.x-cx,dy=b.y-cy,d=Math.hypot(dx,dy);
          if(d<BR){let nx,ny;if(d>0){nx=dx/d;ny=dy/d}else{nx=0;ny=b.y<r[1]+r[3]/2?-1:1}b.x=cx+nx*BR;b.y=cy+ny*BR;const vn=b.vx*nx+b.vy*ny;if(vn<0){b.vx-=1.8*vn*nx;b.vy-=1.8*vn*ny;this.bonk()}}}
        const dc=dist(b.x,b.y,H0.cup[0],H0.cup[1]),sp=Math.hypot(b.vx,b.vy);
        if(dc<13&&sp<700){this.sink(api);return}else if(dc<14){// ふちでくるっと
          const nx=(b.x-H0.cup[0])/(dc||1),ny=(b.y-H0.cup[1])/(dc||1);b.vx+=-ny*30;b.vy+=nx*30}}
      if(Math.hypot(b.vx,b.vy)<12){b.vx=b.vy=0;st.ph='aim';if(st.strokes>=MAXS){st.res.push(MAXS+1);st.total++;api.score=st.total;api.float(W/2,360,'ギブアップ +1',{size:26});S.bad();st.ph='done';st.in=1.2}}}
    else if(st.ph==='sinking'||st.ph==='done'){st.in-=dt;if(st.ph==='sinking'){b.x=lerp(b.x,H0.cup[0],.3);b.y=lerp(b.y,H0.cup[1],.3)}if(st.in<=0){if(st.h+1>=HOLES.length){api.end();return}this.load(st.h+1);S.whoosh()}}},
  bonk(){const t=performance.now();if(this.lb&&t-this.lb<60)return;this.lb=t;S.tone(520,.05,{type:'square',v:.08})},
  sink(api){const st=this.st,H0=HOLES[st.h];st.ph='sinking';st.in=1.6;st.res.push(st.strokes);const[x,y]=H0.cup;
    const msg=st.strokes===1?'ホールインワン！！':st.strokes===2?'バーディー！':st.strokes===3?'パー！':st.strokes+'打でカップイン';
    if(st.strokes===1){S.fanfare();api.flash('#fff6c8',.7);api.shake(10);for(let i=0;i<6;i++)api.burst(rnd(60,W-60),rnd(200,600),{c:['#f4d66d','#e2645a','#fff','#9cc86a'],n:20,shape:'star',sp:320})}
    else if(st.strokes<=2){S.perfect();api.burst(x,y,{c:['#f4d66d','#fff'],n:20,shape:'star'})}else S.coin();
    api.float(W/2,380,msg,{size:st.strokes===1?40:32,c:st.strokes<=2?'#f3c84b':'#fff',life:1.4});api.ring(x,y,{c:'#fff',r:50})},
  drawHud(c,api){const st=this.st;D.rrect(c,60,20,300,56,28,'#fffdf8',3.5);D.text(c,'ホール'+(st.h+1)+'/9　'+st.strokes+'打目　合計'+st.total,W/2,48,19,'#5b4d45');
    let x=W/2-(st.res.length-1)*14;st.res.forEach((r,i)=>{D.text(c,r>MAXS?'×':r===1?'★':String(r),x+i*28,100,16,r===1?'#e2645a':'#5b4d45','center','#fffdf8',4)})},
  draw(c,api){const st=this.st,H0=HOLES[st.h];c.fillStyle='#c9dcb5';c.fillRect(0,api.top,W,api.bottom-api.top);
    D.rrect(c,CL-10,CT-10,CR-CL+20,CB-CT+20,14,'#9a6a4e',4);c.fillStyle='#9cc86a';c.fillRect(CL,CT,CR-CL,CB-CT);
    c.fillStyle='#93bf62';for(let y=CT;y<CB;y+=60)c.fillRect(CL,y,CR-CL,Math.min(30,CB-y));
    for(const r of H0.sand||[])D.rrect(c,r[0],r[1],r[2],r[3],26,'#efdcae',0);
    for(const r of this.walls())D.rrect(c,r[0],r[1],r[2],r[3],5,'#b98450',3.5);
    D.ellipse(c,H0.s[0],H0.s[1],14,6,'#86b257',0);
    const[cx,cy]=H0.cup;D.circle(c,cx,cy,14,'#4b3e37',3);
    if(st.ph!=='sinking')this.ball(c,st.b.x,st.b.y,BR+2);else{const k=st.in/1.6;if(k>.6)this.ball(c,st.b.x,st.b.y,(BR+2)*(k-.3))}
    this.flag(c,cx,cy,90);
    const p=st.pull;if(p&&st.ph==='aim'){const dx=p.x0-p.x,dy=p.y0-p.y,l=Math.min(Math.hypot(dx,dy),170),a=Math.atan2(dy,dx),k=l/170;
      c.fillStyle=k>.8?'#e2645a':'#fffdf8';for(let i=1;i<=8;i++){const d=i*l/8*1.3;c.globalAlpha=1-i/10;c.beginPath();c.arc(st.b.x+Math.cos(a)*d,st.b.y+Math.sin(a)*d,4+k*2,0,7);c.fill()}c.globalAlpha=1;
      D.rrect(c,st.b.x-30,st.b.y+22,60,10,5,'#fffdf8',2);D.rrect(c,st.b.x-29,st.b.y+23,58*k,8,4,k>.8?'#e2645a':'#f2c84b',0)}
    if(api.state==='play'&&st.ph==='aim'&&st.strokes===0&&st.h===0)D.text(c,'ボールのうしろへ引っぱって、はなす',W/2,CB+18,15,'#5b4d45')},
  __bot(api){const st=this.st;if(st.ph!=='aim')return;const H0=HOLES[st.h];const a=Math.atan2(H0.cup[1]-st.b.y,H0.cup[0]-st.b.x)+rnd(-.5,.5);this.hit(a,clamp(dist(st.b.x,st.b.y,H0.cup[0],H0.cup[1])/600,.2,.9),api)},
};
