/* テッポウウオのはやうち：反応速度5本勝負。光の玉がピカッと光ったら口から水をピュッ。フェイント（葉っぱ・あわ）あり。スコア=平均ms（フライングは+600ms） */
const PX=105,RX=W-105,FY=500,FLYX=W/2,FLYY=250,ROUNDS=5,WATER=455;
const GAME={...META,sprites:['icon','fish','orb'],unit:'ミリ秒',hudUnit:false,lowerIsBetter:true,countdown:false,hud:false,
  fmt:v=>Math.round(v)+'',validScore:v=>v>0,
  bgm:{bpm:100,root:57,scale:'minor',prog:[1,1,6,5],seed:12,lead:'triangle',drums:'pop',density:.4},
  ranks:[[9999,'ねぼすけテッポウウオ'],[400,'ふつうのテッポウウオ'],[320,'すばやいテッポウウオ'],[260,'水鉄砲名人'],[220,'反射神経おばけ'],[185,'光の速さのピュッ']],
  shareText:(v,f)=>`テッポウウオのはやうち、平均 ${f}ミリ秒！`,
  icon(c,x,y,s){this.orb(c,x+s*.26,y-s*.28,s*.11,1);this.jet(c,x-s*.02,y-s*.02,x+s*.22,y-s*.24,s*.035,1);this.fish(c,x-s*.12,y+s*.14,s*.42,-.8,'#f2d27a')},
  // テッポウウオ：上向きの口（とがった先）、背びれ・しっぽ、太いしま2本
  fish(c,x,y,s,rot,col){c.save();c.translate(x,y);c.rotate(rot);const lw=Math.max(2,s*.035);
    D.poly(c,[[-s*.42,0],[-s*.7,-s*.24],[-s*.66,s*.24]],col,lw);
    D.path(c,c=>{c.moveTo(-s*.1,-s*.24);c.quadraticCurveTo(-s*.18,-s*.42,-s*.32,-s*.3);c.lineTo(-s*.34,-s*.12);c.closePath()},col,lw);
    D.path(c,c=>{c.moveTo(s*.5,-s*.04);c.quadraticCurveTo(s*.3,-s*.3,-s*.1,-s*.27);c.quadraticCurveTo(-s*.46,-s*.2,-s*.46,0);c.quadraticCurveTo(-s*.46,s*.22,-s*.1,s*.26);c.quadraticCurveTo(s*.3,s*.26,s*.5,s*.02);c.closePath()},col,lw);
    if(D.mode!=='sil'){c.save();c.beginPath();c.moveTo(s*.5,-s*.04);c.quadraticCurveTo(s*.3,-s*.3,-s*.1,-s*.27);c.quadraticCurveTo(-s*.46,-s*.2,-s*.46,0);c.quadraticCurveTo(-s*.46,s*.22,-s*.1,s*.26);c.quadraticCurveTo(s*.3,s*.26,s*.5,s*.02);c.closePath();c.clip();
      c.fillStyle='rgba(91,77,69,.28)';for(const bx of[-s*.05,-s*.28])c.fillRect(bx,-s*.4,s*.08,s*.8);c.restore();
      c.fillStyle=OL;c.beginPath();c.arc(s*.24,-s*.08,Math.max(1.5,s*.045),0,7);c.fill();
      c.fillStyle='rgba(241,156,156,.7)';c.beginPath();c.ellipse(s*.2,s*.06,s*.06,s*.035,0,0,7);c.fill()}
    c.restore()},
  // 光の玉：on=1でピカッ
  orb(c,x,y,r,on){if(on&&D.mode!=='sil'){c.save();c.globalAlpha=.35*on;c.fillStyle='#fff3a6';c.beginPath();c.arc(x,y,r*2.2,0,7);c.fill();c.restore()}
    D.circle(c,x,y,r,on?'#fff1a0':'#c9cfd8',Math.max(2,r*.12))},
  jet(c,x0,y0,x1,y1,w,k){if(k<=0)return;const x=lerp(x0,x1,k),y=lerp(y0,y1,k);c.lineCap='round';
    c.lineWidth=w+5;c.strokeStyle=OL;c.beginPath();c.moveTo(x0,y0);c.lineTo(x,y);c.stroke();
    c.lineWidth=w;c.strokeStyle='#bfe6f5';c.beginPath();c.moveTo(x0,y0);c.lineTo(x,y);c.stroke()},
  reset(api){this.st={round:0,ph:'ready',t:0,wait:0,times:[],res:[],fake:null,tongue:0,rt:0,cpu:0,win:0,msg:'',msgC:'#fff'};api.score=0;this.st.readyT=1.2},
  startRound(){const st=this.st;st.ph='wait';st.t=0;st.wait=rnd(1.4,3.6);st.fake=null;st.fakeAt=st.round>=1&&Math.random()<.65?rnd(.5,st.wait-.4):-1;st.tongue=0;st.rt=0;st.ctongue=0;st.cpu=Math.max(.17,.36-st.round*.035+rnd(-.03,.03))},
  down(x,y,api){const st=this.st;
    if(st.ph==='wait'){st.ph='result';st.t=0;st.res.push({ms:600,foul:true});st.msg='フライング！ +600';st.msgC='#e2645a';S.bad();api.shake(10);st.round++;return}
    if(st.ph==='go'){const ms=st.t*1000;st.rt=ms;st.ph='result';st.tongue=1;this.squirt();api.hitstop(80);api.shake(6);
      const win=st.t<st.cpu;st.res.push({ms,win});if(win){st.win++;setTimeout(()=>{S.coin();S.pop(1.4)},70);api.burst(FLYX,FLYY,{c:['#fff','#fff1a0','#bfe6f5'],n:24,sp:320,shape:'star'});api.flash('#fff',.4)}else{st.ctongue=1}
      st.msg=Math.round(ms)+'ms '+(win?'かち！':'まけ…');st.msgC=win?'#f3c84b':'#cfd8e8';st.t=0;st.round++}},
  squirt(){S.noise(.12,{v:.3,f:2500,to:5000,q:1.2});S.tone(500,.08,{type:'sine',v:.15,to:1100})},
  key(k,api){if(k===' '||k==='Enter')this.down(0,0,api)},
  update(dt,api){const st=this.st;st.t+=dt;
    if(st.ph==='ready'){st.readyT-=dt;if(st.readyT<=0){this.startRound();AU.bgmStart({...this.bgm})}return}
    if(st.ph==='wait'){if(st.fakeAt>0&&st.t>st.fakeAt&&!st.fake){st.fake={kind:pick(['leaf','bubble']),t:0};S.tick()}
      if(st.fake)st.fake.t+=dt;
      if(st.t>=st.wait){st.ph='go';st.t=0;S.go();api.flash('#fff',.25);AU.bgmStop(true)}}
    else if(st.ph==='go'){if(st.t>st.cpu&&!st.ctongue){st.ctongue=1;this.squirt()}if(st.t>1.2){this.down(0,0,api)}}
    else if(st.ph==='result'){if(st.t>1.6){if(st.round>=ROUNDS){api.score=st.res.reduce((a,r)=>a+r.ms,0)/st.res.length;api.end()}else{this.startRound();AU.bgmStart({...this.bgm,seed:12+st.round})}}}
    st.tongue=Math.max(0,st.tongue-dt*1.5)},
  overText:false,
  draw(c,api){const st=this.st;
    const g=c.createLinearGradient(0,0,0,WATER);g.addColorStop(0,'#cfe3ec');g.addColorStop(1,'#e9f1df');c.fillStyle=g;c.fillRect(0,0,W,WATER);
    // 岸の草とぶらさがる枝
    D.path(c,c=>{c.moveTo(-10,60);c.quadraticCurveTo(140,40,230,90)},null,6);c.lineWidth=6;c.strokeStyle='#8a6f57';c.stroke();
    for(const[x,y]of[[60,58],[120,52],[180,64]])D.ellipse(c,x,y+10,14,8,'#8fbf78',2.5);
    // 水
    c.fillStyle='#9ccbe0';c.fillRect(0,WATER,W,H-WATER);c.fillStyle='#86b9d2';c.fillRect(0,WATER+150,W,H-WATER-150);
    c.lineWidth=4;c.strokeStyle=OL;c.beginPath();for(let x=0;x<=W;x+=6){const y=WATER+Math.sin(x*.05+api.t*2)*3;x?c.lineTo(x,y):c.moveTo(x,y)}c.stroke();
    c.globalAlpha=.5;for(let i=0;i<5;i++){c.lineWidth=2.5;c.strokeStyle='#d7eef6';c.beginPath();const x=(i*97+api.t*12)%W;c.moveTo(x,WATER+30+i*28);c.lineTo(x+30,WATER+30+i*28);c.stroke()}c.globalAlpha=1;
    // 光の玉
    const hitNow=st.ph==='result'&&!st.res[st.res.length-1]?.foul,lit=st.ph==='go'||hitNow?1:0;
    if(!(hitNow&&st.t>.12)){const bob=Math.sin(api.t*2)*4;this.orb(c,FLYX,FLYY+bob,24,lit);if(st.ph==='go')D.text(c,'！',FLYX,FLYY-70,90,'#e2645a','center',OL,10)}
    // フェイント
    if(st.fake){const f=st.fake,k=f.t;if(f.kind==='leaf'){c.save();c.translate(W/2+Math.sin(k*3)*60,90+k*240);c.rotate(Math.sin(k*4));D.ellipse(c,0,0,22,12,'#e8a54a',3);c.restore()}
      else if(k<1.2){const y=WATER+120-k*110;if(y>WATER-6){c.globalAlpha=.85;D.circle(c,W/2+Math.sin(k*9)*10,y,12+k*4,'#e6f6fb',3);c.globalAlpha=1}}}
    // 水鉄砲
    const last=st.res[st.res.length-1],k=Math.min(1,st.t*9);
    const mouth=(x,dir)=>[x+dir*Math.cos(-.95)*48,FY+Math.sin(-.95)*48];
    if(st.ph==='result'&&last&&!last.foul){const[mx,my]=last.win?mouth(PX,1):mouth(RX,-1);this.jet(c,mx,my,FLYX,FLYY,9,st.t<.5?k:0)}
    // テッポウウオ（水面から顔を出して玉をねらう）
    this.fish(c,PX,FY,110,-.95,'#f2d27a');
    c.save();c.translate(RX,FY);c.scale(-1,1);this.fish(c,0,0,110,-.95,'#b9c9d9');c.restore();
    D.text(c,'きみ',PX,FY+90,16,'#fff','center',OL,5);D.text(c,'ライバル',RX,FY+90,16,'#fff','center',OL,5);
    // ラウンド表示
    for(let i=0;i<ROUNDS;i++){const r=st.res[i],x=W/2-80+i*40;D.circle(c,x,124,13,r?(r.foul?'#e2645a':r.win?'#f3c84b':'#cfd8e8'):'#fffdf8',3);if(r)D.text(c,r.foul?'×':r.win?'○':'●',x,125,12,'#5b4d45')}
    if(st.ph==='ready')D.text(c,'玉が光ったらタップ',W/2,360,24,'#fff','center',OL,7);
    if(st.ph==='wait')D.text(c,'……',W/2,360,30,'#5b4d45');
    if(st.ph==='result')D.text(c,st.msg,W/2,360,32,st.msgC,'center',OL,8);
    if(api.state==='over'){D.text(c,'平均 '+Math.round(api.score)+'ms',W/2,410,36,'#fff','center',OL,9)}
  },
  __bot(api){const st=this.st;if(st.ph==='go'&&st.t>rnd(.18,.3))this.down(0,0,api)},
};
