/* かっとばしホームラン：奥のマシンから手前へ来るボールをタイミングで打つ。人は出さずバットだけ。 */
const MX=W/2,MY=250,HY=610,N=15;
const GAME={...META,sprites:['icon','machine','bat'],unit:'点',fullBleed:true,comboHud:false,
  bgm:{bpm:126,root:60,scale:'major',prog:[1,4,5,1],seed:5,lead:'square',drums:'pop',density:.55},
  ranks:[[0,'からぶり'],[300,'ヒット職人'],[800,'クリーンアップ'],[1500,'ホームランバッター'],[2500,'4番打者'],[3800,'場外の伝説']],
  shareText:(v,f)=>`かっとばしホームランで ${f}点！`,
  icon(c,x,y,s){this.bat(c,x-s*.38,y+s*.32,s*.95,-.75);D.circle(c,x+s*.22,y-s*.24,s*.15,'#fbf7f0',4);c.strokeStyle='#e2645a';c.lineWidth=3;c.beginPath();c.arc(x+s*.1,y-s*.24,s*.12,-.8,.8);c.stroke();D.star(c,x+s*.42,y-s*.4,s*.06,'#f4d66d',2.5)},
  machine(c,x,y,s){D.rrect(c,x-s*.35,y-s*.1,s*.7,s*.5,s*.1,'#7fb2e0');D.circle(c,x,y-s*.2,s*.3,'#a9c7e6');D.circle(c,x,y-s*.2,s*.12,'#4b3e37',3);D.face(c,x,y+s*.18,s*.4);D.rrect(c,x-s*.3,y+s*.4,s*.6,s*.12,4,'#8a8392')},
  bat(c,x,y,len,a){c.save();c.translate(x,y);c.rotate(a);D.path(c,c=>{c.moveTo(0,-5);c.lineTo(len*.35,-6);c.quadraticCurveTo(len*.8,-len*.08,len,-len*.07);c.arc(len,0,len*.07,-Math.PI/2,Math.PI/2);c.quadraticCurveTo(len*.8,len*.08,len*.35,6);c.lineTo(0,5);c.closePath()},'#e3b47a',3.5);
    D.rrect(c,-12,-7,22,14,5,'#5b4d45',0);c.restore()},
  reset(api){this.st={n:0,ball:null,wait:1.2,swing:0,res:[],hr:0,fly:null,t:0,streak:0};api.score=0},
  pitch(){const st=this.st;const k=st.n<3?0:rndi(0,st.n<7?1:3);const T=[{d:1.05,n:'ストレート'},{d:1.5,n:'スロー'},{d:.75,n:'速球'},{d:1.15,n:'ゆれる球',wob:1}][k];
    st.ball={t:0,d:T.d*rnd(.92,1.08),k,wob:T.wob||0,name:T.n,hit:false};st.n++;S.tone(180,.15,{type:'sine',v:.4,to:90});S.noise(.15,{v:.3,f:800})},
  bpos(b){const k=b.t/b.d,e=k*k*(.6+.4*k);const y=lerp(MY,HY,e)+(k>1?(k-1)*300:0);const x=MX+(b.wob?Math.sin(k*9)*28*k:0);return{x,y,s:.35+.65*Math.min(1.3,e)}},
  down(x,y,api){const st=this.st;if(st.swing>0)return;st.swing=.28;S.whoosh();const b=st.ball;if(!b||b.hit)return;
    const p=this.bpos(b),off=(p.y-HY)/26;// -1..1 がジャスト付近
    if(Math.abs(off)<1.6&&Math.abs(p.x-MX)<46){b.hit=true;const q=Math.max(0,1-Math.abs(off)/1.6),side=clamp(off*.7+(p.x-MX)/80,-1,1);
      const dist0=Math.round(30+q*q*120+rnd(0,8));const hr=dist0>=110;
      st.fly={t:0,x:p.x,y:p.y,ang:side,dist:dist0,hr};
      let pts=dist0;if(hr){pts=300+(dist0-110)*10;st.hr++;st.streak++;if(st.streak>=2)pts+=100*st.streak}else st.streak=0;api.add(pts);st.res.push(hr?'HR':dist0>=70?'H':'h');
      if(hr){S.boom();S.fanfare();api.flash('#fff',.7);api.shake(12);api.hitstop(120);api.float(W/2,330,'ホームラン！！',{size:44,c:'#f3c84b',life:1.6});api.float(W/2,390,dist0+'m　+'+pts,{size:26,life:1.6});if(st.streak>=2)api.float(W/2,430,st.streak+'連続！',{size:24,c:'#e2645a',life:1.6})}
      else{S.thud();S.tone(900,.1,{type:'square',v:.15});api.shake(4);api.float(W/2,360,(dist0>=70?'ヒット！ ':'ポテン ')+dist0+'m',{size:30,life:1.2})}
      api.burst(p.x,p.y,{c:['#fff','#f4d66d'],n:hr?24:10,sp:hr?360:180,shape:hr?'star':'c'})}},
  key(k,api){if(k===' ')this.down(0,0,api)},
  update(dt,api){const st=this.st;st.t+=dt;st.swing=Math.max(0,st.swing-dt);
    if(st.fly){st.fly.t+=dt}
    if(!st.ball){st.wait-=dt;if(st.wait<=0){if(st.n>=N){api.end();return}this.pitch()}}
    else{const b=st.ball;b.t+=dt;if(!b.hit&&b.t>b.d*1.35){st.ball=null;st.wait=1;st.res.push('x');st.streak=0;S.bad();api.float(W/2,360,'ストライク…',{size:26})}
      if(b.hit&&st.fly.t>(st.fly.hr?2.2:1.3)){st.ball=null;st.fly=null;st.wait=.6}}},
  drawHud(c,api){const st=this.st;D.rrect(c,60,20,300,56,28,'#fffdf8',3.5);D.text(c,api.score+'点　HR '+st.hr+'本',W/2,48,22,'#5b4d45');
    for(let i=0;i<N;i++){const r=st.res[i],x=W/2-(N-1)*12+i*24;D.circle(c,x,98,8,r==='HR'?'#f4d66d':r==='H'||r==='h'?'#9cc86a':r==='x'?'#c9bfb4':'#fffdf8',2)}},
  draw(c,api){const st=this.st,f=st.fly;let sky=0;if(f&&f.hr)sky=Math.min(1,f.t/1.2);
    c.save();c.translate(0,sky*sky*60);
    c.fillStyle='#bfe0ef';c.fillRect(0,api.top-80,W,330-api.top+80);
    for(let i=0;i<5;i++)D.ellipse(c,(i*110+st.t*8)%(W+120)-60,120+(i%2)*40,50,16,'#fff',0);
    c.fillStyle='#7fb394';c.fillRect(0,200,W,60);c.fillStyle='#6fa383';for(let x=0;x<W;x+=24)c.fillRect(x,200,12,60);
    c.fillStyle='#9cc86a';c.fillRect(0,260,W,api.bottom-260);
    D.path(c,c=>{c.moveTo(MX,250);c.lineTo(W+60,api.bottom);c.lineTo(-60,api.bottom);c.closePath()},'#d9b98d',0);
    D.poly(c,[[MX-26,HY+30],[MX+26,HY+30],[MX+26,HY+44],[MX,HY+58],[MX-26,HY+44]],'#fbf7f0',3);
    c.globalAlpha=.4;c.lineWidth=3;c.strokeStyle='#fff';c.beginPath();c.ellipse(MX,HY,48,18,0,0,7);c.stroke();c.globalAlpha=1;
    this.machine(c,MX,MY-20,90);
    const b=st.ball;if(b){if(!b.hit){const p=this.bpos(b);c.globalAlpha=.2;D.ellipse(c,p.x,lerp(MY+30,HY+40,(p.y-MY)/(HY-MY)),12*p.s,4*p.s,'#5b4d45',0);c.globalAlpha=1;
        D.circle(c,p.x,p.y,16*p.s,'#fbf7f0',3*p.s);c.strokeStyle='#e2645a';c.lineWidth=2*p.s;c.beginPath();c.arc(p.x-8*p.s,p.y,12*p.s,-.9,.9);c.stroke()}
      else if(f){const k=Math.min(1,f.t/(f.hr?1.2:.9));const tx=MX+f.ang*180,ty=f.hr?-200:300-f.dist*1.2;const x=lerp(f.x,tx,k),y=lerp(f.y,ty,k)-Math.sin(k*Math.PI)*(f.hr?150:80);
        D.circle(c,x,y,Math.max(3,16*(1-k*.8)),'#fbf7f0',3);if(f.hr&&k>=1){D.star(c,tx,40,18+Math.sin(st.t*10)*4,'#f4d66d',3)}}}
    c.restore();
    // バット（手前）
    const sw=st.swing>0?1-st.swing/.28:0;const a=st.swing>0?lerp(-1.9,.5,ease.out(sw)):-1.9;this.bat(c,MX-95,HY+70,170,a);
    if(!b&&st.n===0&&api.state==='play')D.text(c,'ボールが円に来たらタップ！',W/2,HY+90,17,'#5b4d45','center','#fffdf8',5)},
  __bot(api){const st=this.st,b=st.ball;if(!b||b.hit)return;const p=this.bpos(b);if(p.y>HY-12+rnd(-10,10))this.down(0,0,api)},
};
