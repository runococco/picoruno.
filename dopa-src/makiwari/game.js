/* ぴったりまきわり：往復するマーカーを赤ゾーンで止める。 */
const BX=60,BW=W-120,BY=250;
const GAME={...META,sprites:['icon','log'],unit:'本',hudUnit:true,fullBleed:true,
  bgm:{bpm:124,root:55,scale:'minor',prog:[1,6,7,1],seed:81,lead:'square',drums:'four',density:.55},
  ranks:[[0,'ミシッ'],[5,'まきわり見習い'],[15,'スパッと上手'],[30,'まきわりの達人'],[50,'きこりの親方'],[80,'伝説のおの']],
  shareText:(v,f)=>`ぴったりまきわりで ${f}本 われた！`,
  icon(c,x,y,s){this.log(c,x,y+s*.15,s*.42,0);c.save();c.translate(x+s*.15,y-s*.25);c.rotate(.5);D.rrect(c,-s*.04,-s*.1,s*.08,s*.5,s*.03,'#a67c52',2.5);D.rrect(c,-s*.2,-s*.2,s*.3,s*.18,s*.05,'#b9c3cc',2.5);c.restore()},
  log(c,x,y,r,split){if(!split){D.rrect(c,x-r,y-r*.55,r*2,r*1.1,r*.3,'#a67c52');D.ellipse(c,x,y-r*.55,r,r*.22,'#e8d8bd');D.face(c,x,y+r*.05,r*1.1);return}const g=split*r*.9;D.rrect(c,x-r-g,y-r*.55,r,r*1.1,r*.2,'#a67c52');D.rrect(c,x+g,y-r*.55,r,r*1.1,r*.2,'#a67c52');D.ellipse(c,x-r*.5-g,y-r*.55,r*.5,r*.18,'#e8d8bd');D.ellipse(c,x+r*.5+g,y-r*.55,r*.5,r*.18,'#e8d8bd')},
  reset(api){this.st={p:0,v:1.2,dir:1,n:0,miss:0,zone:.16,split:0,wait:0,t:0,endT:0,mood:'smile'};api.score=0},
  down(x,y,api){const st=this.st;if(st.wait>0||st.miss>=3)return;const d=Math.abs(st.p-.5);st.wait=.45;
    if(d<st.zone/2){st.n++;api.score=st.n;api.combo++;const perfect=d<.035;const pts=perfect?3:1;st.split=1;S.swish();S.thud();api.burst(W/2,BY+80,{c:['#e8d8bd','#a67c52'],n:10,sp:200,r:4,shape:'s'});
      api.float(W/2,BY-40,perfect?'ドまん中！':'スパッ',{size:perfect?32:24,c:perfect?'#e2645a':'#5b4d45'});if(perfect){api.flash('#fff',.25);S.perfect()}
      st.v=Math.min(3.4,1.2+st.n*.07);st.zone=Math.max(.09,.16-st.n*.002);if(st.n%10===0){S.fanfare();api.float(W/2,180,st.n+'本！',{size:34,c:'#c9a070'})}}
    else{st.miss++;api.combo=0;st.mood='hurt';S.bad();api.shake(7);api.float(W/2,BY-40,st.miss>=3?'おの が ぬけない…':'ミシッ…',{size:26,c:'#e2645a'})}},
  update(dt,api){const st=this.st;st.t+=dt;if(st.miss>=3){st.endT+=dt;if(st.endT>1)api.end();return}
    if(st.wait>0){st.wait-=dt;if(st.wait<=0){st.split=0;st.mood='smile';st.p=rnd(0,.2);st.dir=1}return}
    st.p+=st.v*st.dir*dt;if(st.p>1){st.p=1;st.dir=-1}if(st.p<0){st.p=0;st.dir=1}},
  draw(c,api){const st=this.st;c.fillStyle='#f3e9d8';c.fillRect(0,api.top,W,api.bottom-api.top);c.fillStyle='#e3d3bb';c.fillRect(0,BY+200,W,api.bottom-BY-200);
    D.rrect(c,W/2-80,BY+160,160,50,10,'#8a6a48');D.ellipse(c,W/2,BY+160,80,18,'#c9a070');
    const sp=st.split*(st.wait>0?1:0);this.log(c,W/2,BY+110,48,sp);
    // meter
    D.rrect(c,BX,BY-30,BW,26,13,'#fff',3);const zw=BW*st.zone;D.rrect(c,W/2-zw/2,BY-28,zw,22,10,'#e2645a',0);D.rrect(c,W/2-BW*.035,BY-26,BW*.07,18,6,'#f2c84b',0);
    const mx=BX+st.p*BW;D.poly(c,[[mx-10,BY-50],[mx+10,BY-50],[mx,BY-32]],'#5b4d45',0);c.lineWidth=3;c.strokeStyle=OL;c.beginPath();c.moveTo(mx,BY-30);c.lineTo(mx,BY-4);c.stroke();
    // axe
    const ax=sp?W/2:mx;const ay=sp?BY+60:BY+20;c.save();c.translate(ax,ay);c.rotate(sp?0:-.2);D.rrect(c,-5,-70,10,80,4,'#a67c52',2.5);D.poly(c,[[-6,-70],[22,-78],[26,-40],[-6,-44]],'#b9c3cc');c.restore();
    for(let i=0;i<3;i++)D.circle(c,W/2-30+i*30,150,9,i<3-st.miss?'#e2645a':'#e7e2d8',2.5);
    if(api.state==='play'&&st.n===0&&st.miss===0)D.text(c,'赤いところでタップ！',W/2,BY-80,20,'#5b4d45')},
  __bot(api){const st=this.st;if(st.wait>0)return;const nx=st.p+st.v*st.dir*.02;if(Math.abs(nx-.5)<st.zone/3.5||Math.abs(st.p-.5)<st.zone/3)this.down(0,0,api)},
};
