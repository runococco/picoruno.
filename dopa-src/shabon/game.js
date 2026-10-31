/* ギリギリしゃぼん玉：長押しでふくらませ、われる前にはなす。限界はかくれていて毎回ちがう。 */
const N=10,WX=W/2,WY=520,RY=432;
const GAME={...META,sprites:['icon','wand'],unit:'点',fullBleed:true,comboHud:false,
  bgm:{bpm:96,root:65,scale:'major',prog:[1,6,4,5],seed:21,lead:'triangle',drums:'pop',density:.42,stab:false},
  ranks:[[0,'パチン'],[300,'しゃぼん見習い'],[600,'ふわふわ職人'],[900,'ギリギリ上手'],[1200,'ドキドキの達人'],[1500,'しゃぼん玉の神']],
  shareText:(v,f)=>`ギリギリしゃぼん玉で ${f}点！`,
  icon(c,x,y,s){this.wand(c,x,y+s*.48,s*.75);this.bub(c,x,y-s*.24,s*.3,0,0);this.bub(c,x+s*.33,y-s*.38,s*.09,2,0)},
  bub(c,x,y,r,t,wob){const k=wob*Math.sin(t*40)*.06;c.save();c.translate(x,y);c.scale(1+k,1-k);
    c.globalAlpha=.32;c.fillStyle=`hsl(${(t*40)%360},70%,82%)`;c.beginPath();c.arc(0,0,r,0,7);c.fill();c.globalAlpha=1;
    c.lineWidth=Math.max(2.5,r*.03);c.strokeStyle=OL;c.beginPath();c.arc(0,0,r,0,7);c.stroke();
    
    D.face(c,0,r*.1,Math.min(46,r*.55),wob>.6?'o':'smile');c.restore()},
  wand(c,x,y,s){c.lineWidth=Math.max(4,s*.06);c.strokeStyle=OL;c.lineCap='round';c.beginPath();c.moveTo(x,y);c.lineTo(x,y-s*.5);c.stroke();c.lineWidth=Math.max(3,s*.05);c.strokeStyle='#f2a5c0';c.beginPath();c.moveTo(x,y);c.lineTo(x,y-s*.5);c.stroke();
    c.lineWidth=Math.max(5,s*.06);c.strokeStyle=OL;c.beginPath();c.arc(x,y-s*.62,s*.13,0,7);c.stroke();c.lineWidth=Math.max(3,s*.04);c.strokeStyle='#f2a5c0';c.stroke()},
  reset(api){this.st={n:0,r:0,blowing:false,lim:0,cur:null,fly:[],pops:[],res:[],t:0,wait:.4,best:0};this.next();api.score=0},
  next(){const st=this.st;st.r=12;st.lim=Math.random()<.15?rnd(35,70):Math.random()<.5?rnd(70,130):rnd(120,175);st.warn=st.lim-rnd(12,28)-(Math.random()<.2?20:0);st.fake=Math.random()<.25?rnd(40,st.lim-10):-1},
  down(x,y,api){const st=this.st;if(st.n>=N||st.wait>0)return;st.blowing=true;S.noise(.15,{v:.12,f:500})},
  up(x,y,api){const st=this.st;if(!st.blowing)return;st.blowing=false;if(st.r<16){return}
    const pts=Math.round(st.r*st.r/30);st.fly.push({x:WX,y:RY+8-st.r,r:st.r,vy:-60,vx:rnd(-30,30),t:st.t});st.res.push(pts);api.add(pts);st.n++;
    const near=st.r/st.lim;let msg='+'+pts;if(near>.92){msg='ギリギリ！ +'+pts;S.perfect();api.flash('#fff',.3)}else S.good();api.float(WX,RY-2*st.r-20,msg,{size:near>.92?32:26,c:near>.92?'#f3c84b':'#fff'});
    this.after(api)},
  key(k,api){if(k===' ')this.down(0,0,api)},keyUp(k,api){if(k===' ')this.up(0,0,api)},
  after(api){const st=this.st;st.wait=.6;if(st.n>=N){st.wait=99;st.endT=.9}else this.next()},
  pop(api){const st=this.st;st.blowing=false;st.pops.push({x:WX,y:RY+8-st.r,r:st.r,t:0});st.res.push(0);st.n++;S.pop(.6);S.noise(.2,{v:.5,f:3000});api.shake(8);api.float(WX,RY-st.r,'パチン！',{size:40,c:'#fff'});
    api.burst(WX,RY-st.r,{c:['#bfe3ee','#f2a5c0','#fff'],n:30,sp:st.r*4,r:4});this.after(api)},
  update(dt,api){const st=this.st;st.t+=dt;if(st.wait>0&&st.wait<50)st.wait-=dt;if(st.endT>0){st.endT-=dt;if(st.endT<=0){api.end();return}}
    if(st.blowing){const sp=40+st.r*.45;st.r+=sp*dt;if(Math.floor(st.r/8)!==Math.floor((st.r-sp*dt)/8))S.tone(300+st.r*4,.07,{type:'sine',v:.08});if(st.r>=st.lim){this.pop(api)}}
    for(const f of st.fly){f.vy-=20*dt;f.y+=f.vy*dt;f.x+=f.vx*dt+Math.sin(st.t*2+f.r)*20*dt}
    for(let i=st.pops.length-1;i>=0;i--){st.pops[i].t+=dt;if(st.pops[i].t>.4)st.pops.splice(i,1)}},
  wob(){const st=this.st;if(!st.blowing)return 0;let w=0;if(st.r>st.warn)w=clamp((st.r-st.warn)/(st.lim-st.warn),0,1);if(st.fake>0&&st.r>st.fake&&st.r<st.fake+15)w=Math.max(w,.7);return w},
  drawHud(c,api){const st=this.st;D.text(c,api.score+'点',W/2,46,32,'#fff','center',OL,8);for(let i=0;i<N;i++){const r=st.res[i],x=W/2-(N-1)*15+i*30;D.circle(c,x,92,10,r===undefined?'#fffdf8':r===0?'#c9bfb4':'#bfe3ee',2.5);if(r===0)D.text(c,'×',x,92,12,'#5b4d45')}},
  draw(c,api){const st=this.st;const g=c.createLinearGradient(0,api.top,0,api.bottom);g.addColorStop(0,'#cfe3f2');g.addColorStop(1,'#eef5f0');c.fillStyle=g;c.fillRect(0,api.top,W,api.bottom-api.top);
    c.fillStyle='#b7d69a';c.fillRect(0,640,W,api.bottom-640);D.ellipse(c,80,650,90,24,'#a7c98a',0);D.ellipse(c,340,655,120,28,'#a7c98a',0);
    for(const f of st.fly)if(f.y>api.top-f.r)this.bub(c,f.x,f.y,f.r,st.t+f.t,0);
    for(const p of st.pops){c.globalAlpha=1-p.t/.4;c.lineWidth=3;c.strokeStyle='#fff';c.beginPath();c.arc(p.x,p.y,p.r*(1+p.t*.8),0,7);c.stroke();c.globalAlpha=1}
    if(st.n<N&&(st.blowing||st.r>12))this.bub(c,WX+Math.sin(st.t*50)*this.wob()*4,RY+8-st.r,st.r,st.t,this.wob());
    this.wand(c,WX,WY+160,330);
    if(st.n===0&&!st.blowing&&api.state==='play')D.text(c,'おしてふくらませる→はなす',W/2,WY+30,18,'#5b4d45','center','#fffdf8',5)},
  __bot(api){const st=this.st;if(st.wait>0)return;if(!st.blowing){st.want=rnd(40,140);this.down(0,0,api)}else if(st.r>st.want)this.up(0,0,api)},
};
