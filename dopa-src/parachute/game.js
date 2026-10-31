/* パラシュートぴったり：落下中に左右移動。風でドリフト。 */
const GY=600,N=10;
const GAME={...META,sprites:['icon','chute'],unit:'点',fullBleed:true,comboHud:false,
  bgm:{bpm:100,root:62,scale:'major',prog:[1,6,4,5],seed:77,lead:'triangle',drums:'pop',density:.45},
  ranks:[[0,'ふきとばされ'],[150,'ちゃくち見習い'],[300,'ふわふわ上手'],[450,'風よみの達人'],[600,'ぴったりマスター'],[750,'空の神']],
  shareText:(v,f)=>`パラシュートぴったりで ${f}点！`,
  icon(c,x,y,s){this.chute(c,x,y,s*.5,0);},
  chute(c,x,y,s,sw){c.save();c.translate(x,y);c.rotate(sw*.2);c.lineWidth=2.5;c.strokeStyle=OL;for(const dx of[-s*.4,0,s*.4]){c.beginPath();c.moveTo(dx,-s*.45);c.lineTo(0,s*.25);c.stroke()}
    D.path(c,c=>{c.arc(0,-s*.45,s*.5,Math.PI,0);c.lineTo(s*.5,-s*.4);for(let i=0;i<4;i++){const x0=s*.5-i*s*.25;c.quadraticCurveTo(x0-s*.125,-s*.3,x0-s*.25,-s*.4)}c.closePath()},'#f2a24a');
    c.fillStyle='#fbf7f0';for(let i=0;i<4;i+=2){c.beginPath();c.moveTo(s*.5-i*s*.25,-s*.42);c.lineTo(s*.5-(i+1)*s*.25,-s*.42);c.lineTo(s*.5-(i+1)*s*.25,-s*.9+Math.abs(s*.5-(i+1)*s*.25)*.9);c.fill()}
    D.rrect(c,-s*.16,s*.2,s*.32,s*.3,s*.1,'#e3b47a');D.face(c,0,s*.35,s*.28);c.restore()},
  reset(api){this.st={n:0,x:W/2,y:-60,tx:W/2,wind:0,target:W/2,res:[],wait:0,t:0,falling:true,kx:0};this.next();api.score=0},
  next(){const st=this.st;st.y=-60;st.x=rnd(80,W-80);st.tx=st.x;st.target=rnd(70,W-70);st.wind=rnd(-1,1)*(.4+st.n*.1);st.falling=true},
  down(x){this.st.tx=x},move(x){this.st.tx=x},up(){},
  key(k){if(k==='ArrowLeft')this.st.kx=-1;if(k==='ArrowRight')this.st.kx=1},keyUp(k){if(k==='ArrowLeft'||k==='ArrowRight')this.st.kx=0},
  update(dt,api){const st=this.st;st.t+=dt;if(st.wait>0){st.wait-=dt;if(st.wait<=0){if(st.n>=N){api.end();return}this.next()}return}
    if(st.kx)st.tx=st.x+st.kx*120;
    const want=clamp(st.tx-st.x,-160,160);st.x+=want*dt*2+st.wind*90*dt;st.x=clamp(st.x,30,W-30);st.y+=(110+st.n*8)*dt;
    if(st.y>=GY){st.falling=false;st.n++;const d=Math.abs(st.x-st.target);const pts=d<8?100:d<20?70:d<40?40:d<70?20:d<110?10:0;api.add(pts);st.res.push(pts);st.wait=1.1;S.thud();
      if(pts>=70){S.perfect();api.flash('#fff',.3);api.burst(st.x,GY,{c:['#f4d66d','#fff'],n:16,shape:'star',sp:200})}else if(pts)S.good();else S.bad();
      api.float(st.x,GY-80,pts===100?'ぴったり！ +100':pts?'+'+pts:'はずれ…',{size:pts===100?30:22,c:pts>=70?'#f3c84b':'#fff'});api.burst(st.x,GY+10,{c:'#d9c7aa',n:6,sp:100,r:3})}},
  drawHud(c,api){const st=this.st;D.rrect(c,70,20,280,56,28,'#fffdf8',3.5);D.text(c,api.score+'点　'+st.n+'/'+N+'回',W/2,48,22,'#5b4d45');
    D.rrect(c,130,88,160,40,20,'#fffdf8',3);D.text(c,'かぜ',165,108,15,'#8e8077');const w=st.wind;if(Math.abs(w)<.05)D.text(c,'なし',235,108,17,'#5b4d45');else{D.text(c,Math.abs(w).toFixed(1),250,108,17,'#5b4d45');const ax=208,dir=Math.sign(w);c.lineWidth=4;c.strokeStyle='#6fa6c9';c.lineCap='round';c.beginPath();c.moveTo(ax-12*dir,108);c.lineTo(ax+12*dir,108);c.lineTo(ax+4*dir,101);c.moveTo(ax+12*dir,108);c.lineTo(ax+4*dir,115);c.stroke()}},
  draw(c,api){const st=this.st;const g=c.createLinearGradient(0,api.top,0,GY);g.addColorStop(0,'#cfe3f2');g.addColorStop(1,'#eef5f9');c.fillStyle=g;c.fillRect(0,api.top,W,GY-api.top);
    for(let i=0;i<6;i++)D.ellipse(c,((i*131+st.t*st.wind*60)%(W+120)+W+120)%(W+120)-60,150+i*70,48,16,'#fff',0);
    c.fillStyle='#9cc86a';c.fillRect(0,GY,W,api.bottom-GY);
    for(const[r,col]of[[110,'#7fb2e0'],[70,'#fbf7f0'],[40,'#e2645a'],[12,'#fbf7f0']])D.ellipse(c,st.target,GY+6,r,r*.22,col,2.5);
    if(st.falling||st.wait>0)this.chute(c,st.x,st.y,80,Math.sin(st.t*3)*(st.falling?1:0));
    if(api.t<3&&api.state==='play')D.text(c,'ゆびで左右にうごかす',W/2,GY+70,16,'#5b4d45','center','#fffdf8',5)},
  __bot(api){const st=this.st;const left=(GY-st.y)/(110+st.n*8);st.tx=st.target-st.wind*90*left},
};
