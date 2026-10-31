/* ギリギリブレーキ：横スクロールの車。減速して停止線までの距離で採点。 */
const CY=430;
const CARS=['#e2645a','#7fb2e0','#f2c84b','#9cc86a','#c49ae0'];
const GAME={...META,sprites:['icon','car'],unit:'点',fullBleed:true,
  bgm:{bpm:132,root:57,scale:'minor',prog:[1,7,6,5],seed:66,lead:'saw',drums:'four',density:.6},
  ranks:[[0,'ドカン'],[300,'ブレーキ見習い'],[600,'なかなかの運転'],[900,'ギリギリ職人'],[1200,'ブレーキの達人'],[1450,'伝説のドライバー']],
  shareText:(v,f)=>`ギリギリブレーキで ${f}点！`,
  icon(c,x,y,s){this.car(c,x,y,s*.4,'#e2645a');c.lineWidth=4;c.strokeStyle=OL;c.beginPath();c.moveTo(x+s*.42,y-s*.3);c.lineTo(x+s*.42,y+s*.35);c.stroke()},
  car(c,x,y,s,col,sq=0){c.save();c.translate(x,y);c.scale(1+sq*.15,1-sq*.1);D.rrect(c,-s*1.1,-s*.25,s*2.2,s*.7,s*.2,col);D.rrect(c,-s*.6,-s*.75,s*1.1,s*.6,s*.2,col);D.rrect(c,-s*.45,-s*.62,s*.8,s*.36,s*.1,'#dceaf2',2.5);
    D.circle(c,-s*.6,s*.45,s*.26,'#5b4d45',0);D.circle(c,s*.6,s*.45,s*.26,'#5b4d45',0);D.circle(c,-s*.6,s*.45,s*.1,'#b9c3cc',0);D.circle(c,s*.6,s*.45,s*.1,'#b9c3cc',0);D.circle(c,s*1.0,-s*.02,s*.1,'#f2c84b',2);c.restore()},
  reset(api){this.st={round:0,x:0,v:0,brake:false,line:0,wait:0,done:false,t:0,col:CARS[0],smoke:[],fin:false,run:false,road:0};api.score=0;this.next()},
  next(){const st=this.st;st.round++;st.col=CARS[(st.round-1)%CARS.length];st.v=rnd(420,620)+st.round*25;st.x=-80;st.line=rnd(240,360);st.dec=rnd(380,560);st.brake=false;st.done=false;st.wait=0;st.camera=0;st.run=true},
  down(){const st=this.st;if(st.done||st.fin)return;if(!st.brake){st.brake=true;S.noise(.25,{v:.3,f:900})}},
  up(){this.st.brake=false},
  update(dt,api){const st=this.st;st.t+=dt;if(st.fin)return;
    if(st.wait>0){st.wait-=dt;if(st.wait<=0){if(st.round>=10){st.fin=true;api.end()}else this.next()}return}
    // camera: car fixed at screen x when near line; world scrolls. Use world coordinate xw; line at world lineW
    if(st.brake&&st.v>0){st.v=Math.max(0,st.v-st.dec*dt);if(Math.random()<.5)st.smoke.push({x:st.x-30,y:CY+20,life:.5,r:rnd(5,10)})}
    st.x+=st.v*dt;st.road+=st.v*dt;
    for(let i=st.smoke.length-1;i>=0;i--){const s=st.smoke[i];s.life-=dt;s.x-=40*dt;s.y-=20*dt;if(s.life<=0)st.smoke.splice(i,1)}
    const lineW=1400;const front=st.x+45; // front bumper world
    if(!st.done){if(front>=lineW){st.done=true;st.over=true;const pts=0;api.combo=0;S.boom();api.shake(12);api.burst(W*.6,CY,{c:['#5b4d45','#e2645a'],n:14,sp:220});api.float(W/2,250,'こえた…0点',{size:30,c:'#e2645a'});st.wait=1.4;st.v=0}
      else if(st.v<=0){st.done=true;const d=lineW-front;let pts,txt;if(d<6){pts=150;txt='ギリギリ！'}else if(d<20){pts=120;txt='すごい！'}else if(d<50){pts=80;txt='いいね'}else if(d<110){pts=40;txt='まあまあ'}else{pts=10;txt='とおい…'}
        if(pts>=120){api.combo++;pts+=Math.min(api.combo,5)*10}else api.combo=0;api.add(pts);st.lastD=d;
        api.float(W/2,250,txt+' +'+pts,{size:pts>=150?34:26,c:pts>=120?'#7fb2e0':'#5b4d45'});if(pts>=150){S.perfect();api.flash('#fff',.3);api.burst(W*.6,CY,{c:['#7fb2e0','#f2c84b','#fff'],n:16,sp:240,shape:'s'})}else if(pts>=120)S.good();else S.coin();st.wait=1.4}
      else if(!st.brake&&st.v>0&&front>lineW-30){/* too late warning handled by overshoot */}}
  },
  draw(c,api){const st=this.st;c.fillStyle='#e8f0f4';c.fillRect(0,api.top,W,api.bottom-api.top);
    const lineW=1400;const camX=Math.min(st.x,lineW-W*.37); // camera follows car until line is at 72%
    const sx=x=>x-camX+W*.35;
    c.fillStyle='#d9d2c6';c.fillRect(0,CY+90,W,api.bottom-CY-90);c.fillStyle='#cfc6b8';for(let x=-((camX)%60);x<W;x+=60)c.fillRect(x,CY+90,2,api.bottom-CY-90);c.fillStyle='#a9b3bd';c.fillRect(0,CY-70,W,160);c.fillStyle='#fff';for(let x=-((camX)%80);x<W;x+=80)c.fillRect(x,CY+5,40,6);
    c.fillStyle='#cfe0b8';c.fillRect(0,api.top,W,CY-70);c.fillStyle='#8fb87a';for(let i=0;i<9;i++){const x=((i*140-camX*.4)%(W+140)+W+140)%(W+140)-70;D.ellipse(c,x,CY-100,36,30,'#9cc86a',2.5);D.rrect(c,x-5,CY-80,10,16,3,'#a67c52',2)}
    // stop line
    const lx=sx(lineW);if(lx>-40&&lx<W+40){c.fillStyle='#fff';c.fillRect(lx,CY-70,10,160);c.strokeStyle=OL;c.lineWidth=2.5;c.strokeRect(lx,CY-70,10,160);D.rrect(c,lx-30,CY-130,70,40,8,'#e2645a',2.5);D.text(c,'止',lx+5,CY-100,22,'#fff');c.lineWidth=3;c.strokeStyle=OL;c.beginPath();c.moveTo(lx+5,CY-90);c.lineTo(lx+5,CY-70);c.stroke()}
    for(const s of st.smoke)D.circle(c,sx(s.x),s.y,s.r*(1+(.5-s.life)),'rgba(255,255,255,.6)',0);
    this.car(c,sx(st.x),CY,30,st.col,st.brake&&st.v>0?1:0);
    if(st.done&&!st.over&&st.lastD!==undefined){D.text(c,'あと '+Math.round(st.lastD)+'cm',W/2,CY+120,20,'#5b4d45')}
    D.text(c,st.round+'/10',W/2,110,18,'#5b4d45');D.text(c,Math.round(st.v/5)+' km/h',W/2,140,22,'#5b4d45');
    if(api.state==='play'&&st.round===1&&!st.brake&&st.x<400)D.text(c,'おしてブレーキ！',W/2,CY+130,22,'#5b4d45')},
  __bot(api){const st=this.st;if(st.done||st.fin)return;const lineW=1400;const front=st.x+45;const stopD=st.v*st.v/(2*st.dec);if(lineW-front<=stopD+st.v*.07+2)this.down();else this.up()},
};
