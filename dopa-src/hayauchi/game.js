/* カエルのはやうち：反応速度5本勝負。フェイント（葉・チョウ）あり。スコア=平均ms（フライングは+300ms） */
const PX=110,RX=W-110,FY=520,FLYX=W/2,FLYY=330,ROUNDS=5;
const GAME={...META,unit:'ミリ秒',hudUnit:false,lowerIsBetter:true,countdown:false,hud:false,
  fmt:v=>Math.round(v)+'',validScore:v=>v>0,
  bgm:{bpm:100,root:57,scale:'minor',prog:[1,1,6,5],seed:12,lead:'triangle',drums:'pop',density:.4},
  ranks:[[9999,'ねぼすけカエル'],[400,'ふつうのカエル'],[320,'すばやいカエル'],[260,'ハエ取り名人'],[220,'反射神経おばけ'],[185,'光の速さのベロ']],
  shareText:(v,f)=>`カエルのはやうち、平均 ${f}ミリ秒！`,
  icon(c,x,y,s){this.frog(c,x,y+s*.08,s*.6,1,0,'#7fbf6d');c.lineWidth=s*.035;c.strokeStyle='#e88e8e';c.lineCap='round';c.beginPath();c.moveTo(x+s*.05,y+s*.12);c.lineTo(x+s*.36,y-s*.28);c.stroke();this.fly(c,x+s*.38,y-s*.3,s*.08,0)},
  frog(c,x,y,s,dir,tongue,col){c.save();c.translate(x,y);c.scale(dir,1);
    D.ellipse(c,0,s*.1,s*.5,s*.36,col,Math.max(2,s*.035));D.circle(c,-s*.24,-s*.22,s*.15,col,Math.max(2,s*.035));D.circle(c,s*.24,-s*.22,s*.15,col,Math.max(2,s*.035));
    c.fillStyle=col;c.fillRect(-s*.3,-s*.14,s*.6,s*.1);
    D.ellipse(c,0,s*.24,s*.3,s*.15,'#e6f0c8',0);
    c.fillStyle='#1d1612';c.beginPath();c.arc(-s*.24,-s*.22,s*.055,0,7);c.arc(s*.24,-s*.22,s*.055,0,7);c.fill();
    c.fillStyle='rgba(240,150,140,.75)';c.beginPath();c.ellipse(-s*.32,s*.08,s*.07,s*.045,0,0,7);c.ellipse(s*.32,s*.08,s*.07,s*.045,0,0,7);c.fill();
    c.lineWidth=Math.max(1.5,s*.03);c.strokeStyle='#1d1612';c.beginPath();c.arc(0,-s*.02,s*.1,.2*Math.PI,.8*Math.PI);c.stroke();
    c.restore()},
  fly(c,x,y,s,t){c.save();c.translate(x,y);const w=Math.sin(t*60)*.4;D.ellipse(c,-s*.5,-s*.5,s*.5,s*.3,'#eef6fa',2,-.6+w);D.ellipse(c,s*.5,-s*.5,s*.5,s*.3,'#eef6fa',2,.6-w);D.circle(c,0,0,s*.55,'#4d4a48',2);c.fillStyle='#1d1612';c.beginPath();c.arc(-s*.2,-s*.1,s*.09,0,7);c.arc(s*.2,-s*.1,s*.09,0,7);c.fill();c.fillStyle='#8a8580';c.beginPath();c.arc(-s*.2,-s*.1,s*.13,0,7);c.arc(s*.2,-s*.1,s*.13,0,7);c.fill();c.fillStyle='#1d1612';c.beginPath();c.arc(-s*.2,-s*.1,s*.08,0,7);c.arc(s*.2,-s*.1,s*.08,0,7);c.fill();c.restore()},
  reset(api){this.st={round:0,ph:'ready',t:0,wait:0,times:[],res:[],fake:null,tongue:0,rt:0,cpu:0,win:0,msg:'',msgC:'#fff'};api.score=0;this.st.readyT=1.2},
  startRound(){const st=this.st;st.ph='wait';st.t=0;st.wait=rnd(1.4,3.6);st.fake=null;st.fakeAt=st.round>=1&&Math.random()<.65?rnd(.5,st.wait-.4):-1;st.tongue=0;st.rt=0;st.ctongue=0;st.cpu=Math.max(.17,.36-st.round*.035+rnd(-.03,.03))},
  down(x,y,api){const st=this.st;
    if(st.ph==='wait'){st.ph='result';st.t=0;st.res.push({ms:600,foul:true});st.msg='フライング！ +600';st.msgC='#e2645a';S.bad();api.shake(10);st.round++;return}
    if(st.ph==='go'){const ms=st.t*1000;st.rt=ms;st.ph='result';st.tongue=1;S.zap(1.3);S.pop();api.hitstop(80);api.shake(6);
      const win=st.t<st.cpu;st.res.push({ms,win});if(win){st.win++;S.coin();api.burst(FLYX,FLYY,{c:['#fff','#f3c84b'],n:20,sp:300,shape:'star'});api.flash('#fff',.4)}else{st.ctongue=1}
      st.msg=Math.round(ms)+'ms '+(win?'かち！':'まけ…');st.msgC=win?'#f3c84b':'#cfd8e8';st.t=0;st.round++}},
  key(k,api){if(k===' '||k==='Enter')this.down(0,0,api)},
  update(dt,api){const st=this.st;st.t+=dt;
    if(st.ph==='ready'){st.readyT-=dt;if(st.readyT<=0){this.startRound();AU.bgmStart({...this.bgm})}return}
    if(st.ph==='wait'){if(st.fakeAt>0&&st.t>st.fakeAt&&!st.fake){st.fake={kind:pick(['leaf','bfly']),t:0};S.tick()}
      if(st.fake)st.fake.t+=dt;
      if(st.t>=st.wait){st.ph='go';st.t=0;S.go();api.flash('#fff',.25);AU.bgmStop(true)}}
    else if(st.ph==='go'){if(st.t>st.cpu&&!st.ctongue){st.ctongue=1;S.zap(.9)}if(st.t>1.2){this.down(0,0,api)}}
    else if(st.ph==='result'){if(st.t>1.6){if(st.round>=ROUNDS){api.score=st.res.reduce((a,r)=>a+r.ms,0)/st.res.length;api.end()}else{this.startRound();AU.bgmStart({...this.bgm,seed:12+st.round})}}}
    st.tongue=Math.max(0,st.tongue-dt*1.5)},
  overText:false,
  draw(c,api){const st=this.st;c.fillStyle='#cfe3ec';c.fillRect(0,0,W,H);
    c.fillStyle='#a9cf9a';c.beginPath();c.ellipse(W/2,H,W,280,0,0,7);c.fill();
    D.ellipse(c,W/2,640,260,40,'#9cc7d8',0);
    for(const x of[PX,RX])D.ellipse(c,x,FY+56,86,24,'#7fb064',3.5);
    const go=st.ph==='go'||(st.ph==='result'&&!st.res[st.res.length-1]?.foul);
    // ハエ
    if(st.ph==='go'||(st.ph==='result'&&st.t<.15)){this.fly(c,FLYX,FLYY,26,api.t);if(st.ph==='go'){D.text(c,'！',FLYX,FLYY-80,90,'#e2645a','center',OL,10)}}
    else if(st.ph==='wait'){this.fly(c,FLYX+Math.sin(api.t*3)*140,FLYY-120+Math.sin(api.t*7)*30,20,api.t)}
    if(st.fake){const f=st.fake,k=f.t;if(f.kind==='leaf'){c.save();c.translate(W/2+Math.sin(k*3)*60,100+k*260);c.rotate(Math.sin(k*4));D.ellipse(c,0,0,22,12,'#e8a54a',3);c.restore()}
      else{c.save();c.translate(-30+k*260,260+Math.sin(k*8)*30);const w=Math.abs(Math.sin(k*20));D.ellipse(c,-10*w,0,14*w+2,18,'#f2b6cf',2.5);D.ellipse(c,10*w,0,14*w+2,18,'#f2b6cf',2.5);c.restore()}}
    // ベロ
    const tg=(sx,on,col)=>{if(!on)return;c.lineWidth=10;c.strokeStyle=col;c.lineCap='round';c.beginPath();c.moveTo(sx,FY-10);c.lineTo(lerp(sx,FLYX,Math.min(1,on*1.2)),lerp(FY-10,FLYY,Math.min(1,on*1.2)));c.stroke()};
    const last=st.res[st.res.length-1];
    if(st.ph==='result'&&last&&!last.foul){if(last.win)tg(PX,Math.min(1,st.t*8),'#e88e8e');else tg(RX,Math.min(1,st.t*8),'#e88e8e')}
    this.frog(c,PX,FY,120,1,0,'#7fbf6d');this.frog(c,RX,FY,120,-1,0,'#b3a36a');
    D.text(c,'きみ',PX,FY+100,16,'#4a3428');D.text(c,'ライバル',RX,FY+100,16,'#4a3428');
    // ラウンド表示
    for(let i=0;i<ROUNDS;i++){const r=st.res[i],x=W/2-80+i*40;D.circle(c,x,80,13,r?(r.foul?'#e2645a':r.win?'#f3c84b':'#cfd8e8'):'#fffdf8',3);if(r)D.text(c,r.foul?'×':r.win?'○':'●',x,81,12,'#4a3428')}
    if(st.ph==='ready')D.text(c,'「！」が出たらタップ',W/2,200,24,'#fff','center',OL,7);
    if(st.ph==='wait')D.text(c,'……',W/2,170,30,'#4a3428');
    if(st.ph==='result')D.text(c,st.msg,W/2,170,32,st.msgC,'center',OL,8);
    if(api.state==='over'){D.text(c,'平均 '+Math.round(api.score)+'ms',W/2,250,36,'#fff','center',OL,9)}
  },
  __bot(api){const st=this.st;if(st.ph==='go'&&st.t>rnd(.18,.3))this.down(0,0,api)},
};
