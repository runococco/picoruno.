/* ふうせんフワリ：Flappy 系。障害物＝上下のえんぴつ。ニアミスでボーナス。 */
const BX=120,BR=24,PW=56;
const PCOL=['#e2645a','#5fb4c4','#f2c14e','#7cb35f','#9a83c9'];
const GAME={...META,unit:'点',
  bgm:{bpm:120,root:65,scale:'major',prog:[1,6,4,5],seed:31,lead:'triangle',drums:'pop',density:.55},
  ranks:[[0,'しぼんだふうせん'],[5,'ふわふわ初心者'],[15,'そよ風ライダー'],[30,'空の散歩名人'],[50,'えんぴつよけの達人'],[80,'ふうせんの神']],
  shareText:(v,f)=>`ふうせんフワリで ${f}点！`,
  icon(c,x,y,s){this.balloon(c,x,y-s*.06,s*.3,0,1);this.pencil(c,x+s*.3,y+s*.5,s*.14,s*.5,0,true)},
  balloon(c,x,y,r,tilt,sc=1){c.save();c.translate(x,y);c.rotate(tilt);c.strokeStyle=OL;c.lineWidth=2;c.beginPath();c.moveTo(0,r*1.05);c.quadraticCurveTo(r*.3,r*1.6,0,r*2.1);c.stroke();
    D.poly(c,[[0,r*.92],[-r*.18,r*1.12],[r*.18,r*1.12]],'#e68aa7',2.5);D.ellipse(c,0,0,r*sc,r*1.05/sc,'#f3a6bd',Math.max(2,r*.13));D.face(c,0,r*.1,r*1.1,'smile');c.restore()},
  pencil(c,x,y,w,len,col,up){c.save();c.translate(x,y);if(!up)c.scale(1,-1);
    // up=true: 先が上をむく
    D.rrect(c,-w/2,-len+w*1.1,w,len,4,PCOL[col||0],3);
    D.poly(c,[[-w/2,-len+w*1.1],[w/2,-len+w*1.1],[0,-len-w*.2]],'#f3d9b0',3);D.poly(c,[[-w*.17,-len+w*.2],[w*.17,-len+w*.2],[0,-len-w*.2]],'#4a3428',0);c.restore()},
  reset(api){this.st={y:330,vy:0,obs:[],stars:[],t:0,next:.8,speed:170,pop:0,tilt:0,sq:1};api.score=0},
  flap(api){const st=this.st;st.vy=-370;st.sq=1.25;S.boing(1.6);api.burst(BX-10,st.y+BR,{c:['#fff'],n:3,sp:80,r:4,g:0,life:.3})},
  down(x,y,api){this.flap(api)},key(k,api){if(k===' '||k==='ArrowUp')this.flap(api)},
  update(dt,api){const st=this.st;st.t+=dt;st.speed=Math.min(290,170+api.score*3);
    st.vy=Math.min(560,st.vy+1150*dt);st.y+=st.vy*dt;st.tilt=clamp(st.vy/1400,-.3,.35);st.sq=lerp(st.sq,1,1-Math.pow(.001,dt));
    st.next-=dt;if(st.next<=0){st.next=Math.max(1.05,1.55-api.score*.012);const gap=Math.max(150,205-api.score*1.5),cy=rnd(150+gap/2,H-130-gap/2);st.obs.push({x:W+40,cy,gap,col:rndi(0,4),col2:rndi(0,4),passed:false,near:0});
      if(Math.random()<.45)st.stars.push({x:W+40+rnd(90,140),y:rnd(170,H-170),got:false})}
    for(const o of st.obs){o.x-=st.speed*dt;
      if(!o.passed&&o.x+PW/2<BX-BR){o.passed=true;let p=1;const m=Math.min(st.y-BR-(o.cy-o.gap/2),(o.cy+o.gap/2)-(st.y+BR));if(m<16){p++;api.float(BX,st.y-50,'ギリギリ！+2',{c:'#f3c84b',size:24});S.perfect();api.combo++}else{api.combo=0;S.coin()}api.score+=p;if(api.score%10===0)api.flash('#fff',.25)}
      if(Math.abs(o.x-BX)<PW/2+BR-6){const top=o.cy-o.gap/2,bot=o.cy+o.gap/2;if(st.y-BR+6<top||st.y+BR-6>bot)return this.die(api)}}
    for(const s of st.stars){s.x-=st.speed*dt;if(!s.got&&dist(s.x,s.y,BX,st.y)<BR+16){s.got=true;api.score+=3;S.coin(1.3);api.burst(s.x,s.y,{c:['#f3c84b','#fff'],n:12,sp:200,shape:'star',r:4});api.float(s.x,s.y-24,'+3',{size:24,c:'#f3c84b'})}}
    st.obs=st.obs.filter(o=>o.x>-80);st.stars=st.stars.filter(s=>s.x>-40&&!s.got);
    if(st.y>H-60-BR||st.y<20)this.die(api)},
  die(api){const st=this.st;st.pop=1;S.boom();S.pop(.6);api.shake(14);api.flash('#fff',.6);api.burst(BX,st.y,{c:['#f3a6bd','#fff'],n:24,sp:380,shape:'s',r:6});api.end()},
  overText:'パン！',
  draw(c,api){const st=this.st;c.fillStyle=this.bg;c.fillRect(0,0,W,H);
    const off=(st.t*30)%480;for(let i=0;i<4;i++){const x=i*160-off*.5;D.ellipse(c,x+80,140+(i%2)*80,56,20,'#fff',0)}
    for(let i=0;i<5;i++){const x=((i*130-st.t*60)%650+650)%650-100;D.ellipse(c,x,H-40,110,70,'#bfe0c4',0)}
    D.rrect(c,-20,H-60,W+40,100,0,'#a9d39a',3.5);
    for(const o of st.obs){this.pencil(c,o.x,H-60+10,PW,H-60-(o.cy+o.gap/2)+10,o.col,true);this.pencil(c,o.x,-10,PW,o.cy-o.gap/2+10,o.col2,false)}
    for(const s of st.stars)D.star(c,s.x,s.y,15,'#f3c84b',3,api.t*2);
    if(!st.pop)this.balloon(c,BX,st.y,BR,st.tilt,st.sq);
  },
  __bot(api){const st=this.st;const o=st.obs.find(o=>o.x+PW/2>BX-BR);const ty=o?o.cy+12:H/2;if(st.y>ty&&st.vy>-50)this.flap(api)},
};
