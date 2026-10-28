/* ねこのはやうち：反応速度5本勝負。池からとび出したさかなを先にねこパンチ。フェイント（葉っぱ・長ぐつ）あり。スコア=平均ms（フライングは+600ms） */
const PX=110,RX=W-110,FY=520,FLYX=W/2,FLYY=330,ROUNDS=5;
const GAME={...META,sprites:['icon','cat','fish','boot'],unit:'ミリ秒',hudUnit:false,lowerIsBetter:true,countdown:false,hud:false,
  fmt:v=>Math.round(v)+'',validScore:v=>v>0,
  bgm:{bpm:100,root:57,scale:'minor',prog:[1,1,6,5],seed:12,lead:'triangle',drums:'pop',density:.4},
  ranks:[[9999,'ねぼすけねこ'],[400,'ふつうのねこ'],[320,'すばやいねこ'],[260,'さかな取り名人'],[220,'反射神経おばけ'],[185,'光の速さのねこパンチ']],
  shareText:(v,f)=>`ねこのはやうち、平均 ${f}ミリ秒！`,
  icon(c,x,y,s){this.cat(c,x-s*.08,y+s*.14,s*.62,1,'#f2c98a');this.paw(c,x+s*.08,y+s*.05,x+s*.3,y-s*.24,s*.07,'#f2c98a');this.fish(c,x+s*.3,y-s*.3,s*.22,.4)},
  // ねこ：まるい体＋三角の耳。dir=-1で左向き
  cat(c,x,y,s,dir,col){c.save();c.translate(x,y);c.scale(dir,1);const lw=Math.max(2,s*.035);
    this.line(c,c=>{c.moveTo(s*.42,s*.3);c.quadraticCurveTo(s*.72,s*.2,s*.62,-s*.08)},s*.1,col,lw);
    D.ellipse(c,0,s*.22,s*.42,s*.3,col,lw);
    D.poly(c,[[-s*.36,-s*.3],[-s*.3,-s*.62],[-s*.08,-s*.42]],col,lw);D.poly(c,[[s*.36,-s*.3],[s*.3,-s*.62],[s*.08,-s*.42]],col,lw);
    D.ellipse(c,0,-s*.2,s*.4,s*.3,col,lw);
    if(D.mode!=='sil'){D.poly(c,[[-s*.31,-s*.38],[-s*.29,-s*.54],[-s*.17,-s*.44]],'#f3b0a8',0);D.poly(c,[[s*.31,-s*.38],[s*.29,-s*.54],[s*.17,-s*.44]],'#f3b0a8',0)}
    D.face(c,0,-s*.16,s*.5,'smile');c.restore()},
  // 太い線（しっぽ・うで）：外側だけ縁どり
  line(c,fn,w,col,lw){c.lineCap='round';c.lineJoin='round';
    if(D.mode!=='fill'){c.beginPath();fn(c);c.lineWidth=w+(D.mode==='sil'?lw*2.3:lw*2);c.strokeStyle=OL;c.stroke()}
    if(D.mode!=='sil'){c.beginPath();fn(c);c.lineWidth=w;c.strokeStyle=col;c.stroke()}},
  paw(c,x0,y0,x1,y1,r,col){this.line(c,c=>{c.moveTo(x0,y0);c.lineTo(x1,y1)},r*1.3,col,3);D.circle(c,x1,y1,r,col,3);
    if(D.mode!=='sil'){const a=Math.atan2(y1-y0,x1-x0);for(const k of[-1,0,1]){D.circle(c,x1+Math.cos(a+k*.7)*r*.55,y1+Math.sin(a+k*.7)*r*.55,r*.2,'#f3b0a8',0)}}},
  fish(c,x,y,s,rot){c.save();c.translate(x,y);c.rotate(rot||0);
    D.poly(c,[[s*.55,0],[s*1.0,-s*.38],[s*.95,s*.38]],'#7fb3d8',Math.max(2,s*.07));
    D.ellipse(c,0,0,s*.7,s*.42,'#9ccbe8',Math.max(2,s*.07));
    if(D.mode!=='sil'){c.fillStyle=OL;c.beginPath();c.arc(-s*.36,-s*.08,Math.max(1.2,s*.07),0,7);c.fill();c.lineWidth=Math.max(1,s*.05);c.strokeStyle=OL;c.beginPath();c.arc(s*.15,0,s*.25,-1,1);c.stroke()}
    c.restore()},
  boot(c,x,y,s,rot){c.save();c.translate(x,y);c.rotate(rot||0);D.path(c,c=>{c.moveTo(-s*.3,-s*.6);c.lineTo(s*.15,-s*.6);c.lineTo(s*.15,s*.1);c.lineTo(s*.55,s*.2);c.quadraticCurveTo(s*.65,s*.5,s*.4,s*.5);c.lineTo(-s*.3,s*.5);c.closePath()},'#e6c35c',Math.max(2,s*.07));c.restore()},
  reset(api){this.st={round:0,ph:'ready',t:0,wait:0,times:[],res:[],fake:null,tongue:0,rt:0,cpu:0,win:0,msg:'',msgC:'#fff'};api.score=0;this.st.readyT=1.2},
  startRound(){const st=this.st;st.ph='wait';st.t=0;st.wait=rnd(1.4,3.6);st.fake=null;st.fakeAt=st.round>=1&&Math.random()<.65?rnd(.5,st.wait-.4):-1;st.tongue=0;st.rt=0;st.ctongue=0;st.cpu=Math.max(.17,.36-st.round*.035+rnd(-.03,.03))},
  down(x,y,api){const st=this.st;
    if(st.ph==='wait'){st.ph='result';st.t=0;st.res.push({ms:600,foul:true});st.msg='フライング！ +600';st.msgC='#e2645a';S.bad();api.shake(10);st.round++;return}
    if(st.ph==='go'){const ms=st.t*1000;st.rt=ms;st.ph='result';st.tongue=1;S.swish();S.pop();api.hitstop(80);api.shake(6);
      const win=st.t<st.cpu;st.res.push({ms,win});if(win){st.win++;S.coin();api.burst(FLYX,FLYY,{c:['#fff','#f3c84b'],n:20,sp:300,shape:'star'});api.flash('#fff',.4)}else{st.ctongue=1}
      st.msg=Math.round(ms)+'ms '+(win?'かち！':'まけ…');st.msgC=win?'#f3c84b':'#cfd8e8';st.t=0;st.round++}},
  key(k,api){if(k===' '||k==='Enter')this.down(0,0,api)},
  update(dt,api){const st=this.st;st.t+=dt;
    if(st.ph==='ready'){st.readyT-=dt;if(st.readyT<=0){this.startRound();AU.bgmStart({...this.bgm})}return}
    if(st.ph==='wait'){if(st.fakeAt>0&&st.t>st.fakeAt&&!st.fake){st.fake={kind:pick(['leaf','boot']),t:0};S.tick()}
      if(st.fake)st.fake.t+=dt;
      if(st.t>=st.wait){st.ph='go';st.t=0;S.go();api.flash('#fff',.25);AU.bgmStop(true)}}
    else if(st.ph==='go'){if(st.t>st.cpu&&!st.ctongue){st.ctongue=1;S.swish()}if(st.t>1.2){this.down(0,0,api)}}
    else if(st.ph==='result'){if(st.t>1.6){if(st.round>=ROUNDS){api.score=st.res.reduce((a,r)=>a+r.ms,0)/st.res.length;api.end()}else{this.startRound();AU.bgmStart({...this.bgm,seed:12+st.round})}}}
    st.tongue=Math.max(0,st.tongue-dt*1.5)},
  overText:false,
  draw(c,api){const st=this.st;c.fillStyle='#cfe3ec';c.fillRect(0,0,W,H);
    c.fillStyle='#a9cf9a';c.beginPath();c.ellipse(W/2,H,W,280,0,0,7);c.fill();
    D.ellipse(c,W/2,640,260,40,'#9cc7d8',0);
    for(const x of[PX,RX])D.ellipse(c,x,FY+56,86,24,'#e7b2a8',3.5);
    const go=st.ph==='go'||(st.ph==='result'&&!st.res[st.res.length-1]?.foul);
    // さかな：待つあいだは池の中の影、「！」でとび出す
    if(st.ph==='go'||(st.ph==='result'&&st.t<.15)){const k=st.ph==='go'?Math.min(1,st.t*12):1;this.fish(c,FLYX,lerp(640,FLYY,ease.out(k)),40,Math.sin(api.t*20)*.15);if(st.ph==='go'){D.text(c,'！',FLYX,FLYY-80,90,'#e2645a','center',OL,10)}}
    else if(st.ph==='wait'||st.ph==='ready'){c.globalAlpha=.3;c.fillStyle=OL;c.beginPath();c.ellipse(W/2+Math.sin(api.t*1.3)*150,640+Math.sin(api.t*2.1)*8,26,10,0,0,7);c.fill();c.globalAlpha=1}
    if(st.fake){const f=st.fake,k=f.t;if(f.kind==='leaf'){c.save();c.translate(W/2+Math.sin(k*3)*60,100+k*260);c.rotate(Math.sin(k*4));D.ellipse(c,0,0,22,12,'#e8a54a',3);c.restore()}
      else{const by=640-Math.max(0,Math.sin(Math.min(Math.PI,k*3.2)))*170;if(k<1)this.boot(c,W/2+60,by,34,k*4)}}
    // ねこパンチ
    const tg=(sx,on,col)=>{if(!on)return;const k=Math.min(1,on*1.2);this.paw(c,sx,FY-10,lerp(sx,FLYX-(sx<FLYX?30:-30),k),lerp(FY-10,FLYY+10,k),16,col)};
    const last=st.res[st.res.length-1];
    this.cat(c,PX,FY,120,1,'#f2c98a');this.cat(c,RX,FY,120,-1,'#c9c3bd');
    if(st.ph==='result'&&last&&!last.foul){if(last.win)tg(PX+30,Math.min(1,st.t*8),'#f2c98a');else tg(RX-30,Math.min(1,st.t*8),'#c9c3bd')}
    D.text(c,'きみ',PX,FY+100,16,'#5b4d45');D.text(c,'ライバル',RX,FY+100,16,'#5b4d45');
    // ラウンド表示
    for(let i=0;i<ROUNDS;i++){const r=st.res[i],x=W/2-80+i*40;D.circle(c,x,80,13,r?(r.foul?'#e2645a':r.win?'#f3c84b':'#cfd8e8'):'#fffdf8',3);if(r)D.text(c,r.foul?'×':r.win?'○':'●',x,81,12,'#5b4d45')}
    if(st.ph==='ready')D.text(c,'「！」が出たらタップ',W/2,200,24,'#fff','center',OL,7);
    if(st.ph==='wait')D.text(c,'……',W/2,170,30,'#5b4d45');
    if(st.ph==='result')D.text(c,st.msg,W/2,170,32,st.msgC,'center',OL,8);
    if(api.state==='over'){D.text(c,'平均 '+Math.round(api.score)+'ms',W/2,250,36,'#fff','center',OL,9)}
  },
  __bot(api){const st=this.st;if(st.ph==='go'&&st.t>rnd(.18,.3))this.down(0,0,api)},
};
