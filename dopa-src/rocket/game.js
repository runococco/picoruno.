/* 連打ロケット：10秒連打→タイミング発射→飛行演出。到達高度は指数関数で伸びる。 */
const MASH=10;
const SPOTS=[[0,'はっしゃ台'],[1,'ビルの上'],[10,'雲の上'],[100,'宇宙'],[400,'宇宙ステーション'],[36000,'静止衛星'],[384400,'月'],[7.8e7,'火星'],[6.3e8,'木星'],[4.5e9,'海王星'],[1e12,'太陽系の外'],[4e13,'となりの星'],[1e17,'銀河のはし']];
const GAME={...META,sprites:['icon','rocket'],unit:'km',hudUnit:false,comboHud:false,countdown:true,hud:false,
  fmt:v=>v>=1e8?(v/1e8).toFixed(1)+'億':v>=1e4?(v/1e4).toFixed(v>=1e6?0:1)+'万':Math.round(v).toLocaleString('ja-JP'),
  bgm:{bpm:168,root:60,scale:'major',prog:[1,5,6,4],seed:3,lead:'square',drums:'four',density:.75},
  ranks:SPOTS.map(([km,n])=>[km,n+'まで到達']),
  shareText:(v,f)=>`連打ロケットで ${f}km 飛んだ！${GAME.spot(v)}まで到達！`,
  spot(v){let s=SPOTS[0][1];for(const[k,n]of SPOTS)if(v>=k)s=n;return s},
  icon(c,x,y,s){c.save();c.translate(x,y);c.rotate(.5);this.rocket(c,0,0,s*.7,1);c.restore()},
  rocket(c,x,y,s,fire){c.save();c.translate(x,y);
    if(fire){const f=fire*(.8+Math.random()*.4);D.path(c,c=>{c.moveTo(-s*.14,s*.32);c.quadraticCurveTo(0,s*(.32+.5*f),s*.14,s*.32)},'#f6b04a',2.5);D.path(c,c=>{c.moveTo(-s*.07,s*.32);c.quadraticCurveTo(0,s*(.32+.28*f),s*.07,s*.32)},'#fbe08a',0)}
    D.path(c,c=>{c.moveTo(-s*.15,s*.1);c.lineTo(-s*.3,s*.34);c.lineTo(-s*.12,s*.3);c.closePath();c.moveTo(s*.15,s*.1);c.lineTo(s*.3,s*.34);c.lineTo(s*.12,s*.3);c.closePath()},'#e2645a',Math.max(2,s*.03));
    D.path(c,c=>{c.moveTo(0,-s*.5);c.bezierCurveTo(s*.28,-s*.25,s*.2,s*.2,s*.14,s*.33);c.lineTo(-s*.14,s*.33);c.bezierCurveTo(-s*.2,s*.2,-s*.28,-s*.25,0,-s*.5)},'#fffdf8',Math.max(2,s*.035));
    D.path(c,c=>{c.moveTo(0,-s*.5);c.bezierCurveTo(s*.12,-s*.4,s*.17,-s*.33,s*.19,-s*.28);c.lineTo(-s*.19,-s*.28);c.bezierCurveTo(-s*.17,-s*.33,-s*.12,-s*.4,0,-s*.5)},'#e2645a',Math.max(2,s*.03));
    D.face(c,0,-s*.06,s*.28,'smile');c.restore()},
  reset(api){this.st={ph:'mash',taps:0,rate:0,hist:[],gauge:0,gdir:1,mult:1,alt:0,final:0,ft:0,shakeR:0,stars:[...Array(60)].map(()=>[rnd(W),rnd(H),rnd(1,2.5)]),clouds:[...Array(8)].map((_,i)=>[rnd(W),i*120,rnd(40,80)])};api.score=0},
  tap(api){const st=this.st;
    if(st.ph==='mash'){st.taps++;st.hist.push(api.t);S.tap(1+Math.min(st.taps,120)/120);st.shakeR=4;
      api.burst(W/2+rnd(-30,30),560,{c:['#f6b04a','#fbe08a','#fff'],n:3,sp:140,r:5,g:-200,life:.4});
      if(st.taps%20===0){api.float(W/2,250,st.taps+'連打！',{size:30});S.combo(st.taps/10)}}
    else if(st.ph==='aim'){const d=Math.abs(st.gauge-.5);st.mult=d<.05?1.5:d<.15?1.3:d<.3?1.12:1;st.ph='fly';st.ft=0;
      st.final=Math.pow(2,st.taps*st.mult/8.5)-1;S.boom();api.shake(18);api.flash('#fff',.7);api.float(W/2,330,st.mult>=1.5?'パーフェクト発射！':st.mult>=1.3?'グッド発射！':'はっしゃ！',{size:34,c:st.mult>=1.5?'#f3c84b':'#fff'});AU.bgmStart({...this.bgm,bpm:190,seed:7})}},
  down(x,y,api){this.tap(api)},key(k,api){if(k===' '||k==='Enter')this.tap(api)},
  update(dt,api){const st=this.st;st.shakeR=Math.max(0,st.shakeR-dt*30);
    st.hist=st.hist.filter(t=>api.t-t<1);st.rate=st.hist.length;
    if(st.ph==='mash'){if(api.t>=MASH){st.ph='aim';st.t0=api.t;S.perfect()}}
    else if(st.ph==='aim'){st.gauge+=st.gdir*dt*1.6;if(st.gauge>1){st.gauge=1;st.gdir=-1}if(st.gauge<0){st.gauge=0;st.gdir=1}if(api.t-st.t0>4)this.tap(api)}
    else if(st.ph==='fly'){st.ft+=dt;const k=Math.min(1,st.ft/4.5),e=1-Math.pow(1-k,3);const prev=st.alt;st.alt=Math.pow(st.final+1,e)-1;api.score=st.alt;
      for(const[km,n]of SPOTS)if(km>0&&prev<km&&st.alt>=km){api.float(W/2,200,n+'！',{size:32,c:'#fff'});S.coin(1+Math.log10(km+1)*.06);api.flash('#fff',.2)}
      if(Math.random()<.5)api.burst(W/2+rnd(-8,8),470,{c:['#f6b04a','#fbe08a'],n:2,sp:80,r:6,g:600,life:.5});
      if(k>=1&&!st.done){st.done=true;api.score=st.final;S.fanfare();api.burst(W/2,360,{c:['#f3c84b','#fff','#e2645a','#8ec6e8'],n:70,sp:450,shape:'star',r:6});setTimeout(()=>api.end(),900)}}},
  overText:false,
  draw(c,api){const st=this.st,la=Math.log10(st.alt+1),sk=clamp(la/3,0,1);
    const top=`hsl(${lerp(205,235,sk)},${lerp(65,45,sk)}%,${lerp(84,10,sk)}%)`,bot=`hsl(${lerp(200,230,sk)},${lerp(60,40,sk)}%,${lerp(90,18,sk)}%)`;
    const g=c.createLinearGradient(0,0,0,H);g.addColorStop(0,top);g.addColorStop(1,bot);c.fillStyle=g;c.fillRect(0,0,W,H);
    const scroll=st.ph==='fly'?st.ft*900:0;
    if(sk>.3){c.globalAlpha=Math.min(1,(sk-.3)*2);for(const[x,y,r]of st.stars){c.fillStyle='#fff';c.beginPath();c.arc(x,(y+scroll*.2*r)%H,r,0,7);c.fill()}c.globalAlpha=1}
    if(la<2.2){c.globalAlpha=1-clamp((la-1.5)/.7,0,1);for(const[x,y,r]of st.clouds){const yy=((y+scroll*.8)%(H+200))-100;D.ellipse(c,x,yy,r,r*.4,'#fff',0)}c.globalAlpha=1}
    if(st.ph==='fly'){const ly=430+st.ft*500;if(ly<H+100){D.rrect(c,-20,ly+90,W+40,300,0,'#9ac98a',4);D.rrect(c,W/2-70,ly+60,140,30,6,'#bfb4a6',3.5)}
      if(st.alt>300000){const m=clamp((Math.log10(st.alt)-5.4)/.3,0,1);D.circle(c,W-90,140-60+m*60,60*m+1,'#f3ecd2',3.5);if(m>.5)D.face(c,W-90,140,60,'smile')}
      const wob=Math.sin(api.t*40)*2;this.rocket(c,W/2+wob,400,150,1.3)}
    else{D.rrect(c,-20,520,W+40,300,0,'#9ac98a',4);D.rrect(c,W/2-70,490,140,30,6,'#bfb4a6',3.5);
      const sx=rnd(-st.shakeR,st.shakeR),fuel=Math.min(1,st.taps/120);this.rocket(c,W/2+sx,410,150,st.ph==='aim'?.4:fuel*.4);
      // 燃料ゲージ
      D.rrect(c,30,180,24,300,12,'#fffdf8',3.5);const fh=296*fuel;if(fh>4)D.rrect(c,32,478-fh,20,fh,10,fuel>.8?'#e2645a':'#f6b04a',0);D.text(c,'燃料',42,500,14,'#5b4d45')}
    // HUD
    if(st.ph==='mash'&&api.state==='play'){const tl=Math.max(0,MASH-api.t);D.text(c,tl.toFixed(1),W/2,80,40,'#fff','center',OL,9);D.text(c,st.taps+' 連打',W/2,140,34,'#f3c84b','center',OL,8);D.text(c,'毎秒 '+st.rate+' 回',W/2,180,18,'#5b4d45');
      if(Math.sin(api.t*14)>0)D.text(c,'連打！',W/2,620,40,'#fff','center',OL,9)}
    if(st.ph==='aim'){D.text(c,'真ん中で タップ！',W/2,120,30,'#fff','center',OL,8);const gx=60,gw=W-120;D.rrect(c,gx,170,gw,30,15,'#fffdf8',3.5);c.fillStyle='#f3c84b';c.fillRect(gx+gw*.35,173,gw*.3,24);c.fillStyle='#e2645a';c.fillRect(gx+gw*.45,173,gw*.1,24);
      const px=gx+gw*st.gauge;D.poly(c,[[px,166],[px-10,150],[px+10,150]],'#5b4d45',2)}
    if(st.ph==='fly'){D.text(c,GAME.fmt(st.alt)+' km',W/2,90,40,'#fff','center',OL,9);D.text(c,'×'+st.mult+'  '+st.taps+'連打',W/2,140,18,'#fff','center',OL,5);if(st.done)D.text(c,GAME.spot(st.final)+'まで到達！',W/2,600,30,'#f3c84b','center',OL,8)}
  },
  __bot(api){const st=this.st;if(st.ph==='mash'&&Math.random()<.5)this.tap(api);if(st.ph==='aim'&&Math.abs(st.gauge-.5)<.06)this.tap(api)},
};
