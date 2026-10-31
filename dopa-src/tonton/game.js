/* とんとんずもう：連打で押し合い。位置が端まで行ったら決着。 */
const GAME={...META,sprites:['icon','rikishi'],unit:'人ぬき',hudUnit:true,fullBleed:true,comboHud:false,
  bgm:{bpm:140,root:55,scale:'minor',prog:[1,1,4,5],seed:66,lead:'square',drums:'four',density:.6},
  ranks:[[0,'はっけよい'],[1,'初勝利'],[3,'三人ぬき'],[6,'小結'],[10,'大関'],[15,'横綱']],
  shareText:(v,f)=>`とんとんずもうで ${f}人ぬき！`,
  icon(c,x,y,s){D.ellipse(c,x,y+s*.3,s*.46,s*.14,'#d9c7a3');this.rikishi(c,x-s*.2,y+s*.1,s*.24,'#e2645a',1,0);this.rikishi(c,x+s*.2,y+s*.1,s*.24,'#7fb2e0',-1,0)},
  rikishi(c,x,y,s,col,dir,lean){c.save();c.translate(x,y);c.rotate(lean*dir*.3);c.scale(dir,1);
    D.poly(c,[[-s*.8,s*.9],[s*.8,s*.9],[s*.55,-s*.9],[-s*.55,-s*.9]],'#fbf7f0');D.rrect(c,-s*.8,s*.2,s*1.6,s*.35,s*.1,col);D.face(c,0,-s*.25,s*1.3,'smile');c.restore()},
  reset(api){this.st={pos:0,lv:0,wins:0,taps:0,tapT:0,rhythm:0,wait:0,over:false,t:0,lean:0,endT:0};api.score=0},
  down(x,y,api){const st=this.st;if(st.wait>0||st.over)return;const now=st.t;const gap=now-st.lastTap;st.lastTap=now;st.taps++;
    const good=gap>.08&&gap<.3;st.rhythm=good?Math.min(5,st.rhythm+1):Math.max(0,st.rhythm-2);const push=(5+st.rhythm*1.6)*(1-st.lv*.05);st.pos+=push;st.lean=1;S.tap(.6+Math.random()*.2);api.shake(1.5);
    if(st.rhythm>=5&&st.taps%6===0){api.float(W/2,290,'いいリズム！',{size:22,c:'#e2645a'})}},
  update(dt,api){const st=this.st;st.t+=dt;st.lean*=Math.pow(.01,dt);if(st.over){st.endT+=dt;if(st.endT>1.2)api.end();return}
    if(st.wait>0){st.wait-=dt;return}
    const idle=st.t-(st.lastTap||0);const pushBack=(20+st.lv*14)*(idle>.3?1.6:.55);st.pos-=pushBack*dt;
    if(st.pos>=100){st.wins++;st.lv++;api.score=st.wins;st.wait=1.2;st.pos=0;st.rhythm=0;S.fanfare();api.flash('#fff',.25);api.burst(W*.7,420,{c:['#7fb2e0','#fff'],n:14,sp:220,shape:'s'});api.float(W/2,250,st.wins+'人ぬき！',{size:32,c:'#e2645a'})}
    else if(st.pos<=-100){st.over=true;S.bad();api.shake(8);api.float(W/2,250,'ぱたん……まけ',{size:30,c:'#5b4d45'})}},
  draw(c,api){const st=this.st;c.fillStyle='#f7eedd';c.fillRect(0,api.top,W,api.bottom-api.top);
    D.rrect(c,40,300,W-80,260,24,'#d9c7a3',4);D.rrect(c,60,320,W-120,220,16,'#e8d8bd',0);c.lineWidth=3;c.strokeStyle=OL;c.beginPath();c.moveTo(W/2,330);c.lineTo(W/2,530);c.stroke();
    const k=st.pos/100;const mx=W/2+k*110;const fall=st.over?1:0;
    c.save();if(fall){c.translate(mx-40,430);c.rotate(-1.2);c.translate(-(mx-40),-430)}this.rikishi(c,mx-40,430,34,'#e2645a',1,st.lean);c.restore();
    this.rikishi(c,mx+40,430,34,'#7fb2e0',-1,st.lean*.5);
    D.rrect(c,70,200,W-140,22,11,'#fff',3);D.rrect(c,72,202,(W-144)*((k+1)/2),18,9,k>0?'#e2645a':'#7fb2e0',0);
    D.text(c,'あいて Lv.'+(st.lv+1),W/2,180,16,'#5b4d45');
    if(api.state==='play'&&st.wins===0&&st.taps<3)D.text(c,'タップ連打でトントン！',W/2,620,22,'#5b4d45')},
  __bot(api){const st=this.st;if(st.wait>0||st.over)return;if(!st.botT||st.t-st.botT>.15){st.botT=st.t;this.down(0,0,api)}},
};
