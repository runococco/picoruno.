/* きんぎょすくい：押している間ポイが水中。離すと上にいる金魚をすくう。紙の耐久がある。 */
const PR=46,BX=W/2,BY=625;
const GAME={...META,sprites:['icon','fish','bowl'],unit:'ひき',hudUnit:true,comboHud:false,fullBleed:true,
  bgm:{bpm:96,root:62,scale:'major',prog:[1,6,4,5],seed:12,lead:'triangle',drums:'pop',density:.45,stab:false},
  ranks:[[0,'ぽちゃん'],[3,'すくい見習い'],[7,'夜店のじょうれん'],[12,'すくいの達人'],[18,'きんぎょ名人'],[26,'夏まつりの伝説']],
  shareText:(v,f)=>`きんぎょすくいで ${f}ひき すくった！`,
  icon(c,x,y,s){D.ellipse(c,x,y+s*.08,s*.46,s*.32,'#8ccbdb');this.fish(c,x-s*.18,y+s*.14,s*.3,-.3,0,0);this.fish(c,x+s*.2,y+s*.18,s*.22,3.4,2,1);this.poi(c,x+s*.1,y-s*.12,s*.22,1,0,true)},
  // k:0 あか 1 くろでめきん 2 きん
  fish(c,x,y,s,ang,k,sw){c.save();c.translate(x,y);c.rotate(ang);const col=k===1?'#8a8392':k===2?'#f2c84b':'#e86a4a',lw=Math.max(2,s*.09),w=Math.sin(sw)*.35;
    D.group(c,()=>{c.save();c.translate(-s*.45,0);c.rotate(w);D.path(c,c=>{c.moveTo(0,0);c.quadraticCurveTo(-s*.5,-s*.55,-s*.65,-s*.3);c.quadraticCurveTo(-s*.35,0,-s*.65,s*.3);c.quadraticCurveTo(-s*.5,s*.55,0,0)},k===1?'#9a93a2':col,lw);c.restore();
      D.ellipse(c,0,0,s*.55,s*.34,col,lw);if(k===1){D.circle(c,s*.28,-s*.25,s*.12,col,lw);D.circle(c,s*.28,s*.25,s*.12,col,lw)}});
    c.fillStyle=OL;c.beginPath();c.arc(s*.3,-s*.14,s*.06,0,7);c.arc(s*.3,s*.14,s*.06,0,7);c.fill();c.restore()},
  poi(c,x,y,r,dur,tear,sub){c.save();c.translate(x,y);c.rotate(.5);D.rrect(c,-r*.12,r*.95,r*.24,r*1.3,r*.1,'#f2a5c0',3);c.restore();
    c.lineWidth=5;c.strokeStyle='#f2a5c0';c.beginPath();c.arc(x,y,r,0,7);c.stroke();
    if(!tear){c.globalAlpha=sub?.45:.85;c.fillStyle='#fbfaf6';c.beginPath();c.arc(x,y,r-3,0,7);c.fill();c.globalAlpha=1;
      if(dur<.6){c.strokeStyle='#c9bfb4';c.lineWidth=1.5;c.beginPath();const n=Math.floor((1-dur)*6);for(let i=0;i<n;i++){const a=i*2.1;c.moveTo(x+Math.cos(a)*r*.15,y+Math.sin(a)*r*.15);c.lineTo(x+Math.cos(a+.3)*r*.7,y+Math.sin(a+.3)*r*.7)}c.stroke()}}
    else{c.strokeStyle='#fbfaf6';c.lineWidth=3;c.beginPath();for(let i=0;i<5;i++){const a=i*1.3;c.moveTo(x+Math.cos(a)*r,y+Math.sin(a)*r);c.lineTo(x+Math.cos(a)*r*.6,y+Math.sin(a)*r*.6)}c.stroke()}
    D.circle(c,x,y,r+3,null,3)},
  bowl(c,x,y,s){D.path(c,c=>{c.moveTo(x-s,y-s*.25);c.quadraticCurveTo(x-s,y+s*.5,x,y+s*.5);c.quadraticCurveTo(x+s,y+s*.5,x+s,y-s*.25);c.closePath()},'#fbfaf6');D.ellipse(c,x,y-s*.25,s,s*.22,'#bfe3ee')},
  newFish(edge){const k=Math.random()<.08?2:Math.random()<.2?1:0;const s=k===1?rnd(34,42):k===2?28:rnd(22,32);
    return{x:edge?pick([-30,W+30]):rnd(60,W-60),y:rnd(170,540),a:rnd(7),v:rnd(30,60),s,k,sw:rnd(7),turn:0,flee:0}},
  reset(api){this.st={f:[],px:W/2,py:420,down:false,dur:1,poi:3,tear:0,lx:W/2,ly:420,caught:[],bowl:0,splash:[]};for(let i=0;i<14;i++)this.st.f.push(this.newFish());api.score=0},
  down(x,y,api){const st=this.st;if(st.tear>0)return;st.down=true;st.px=x;st.py=y-30;st.lx=st.px;st.ly=st.py;S.noise(.2,{v:.2,f:600,type:'lowpass'});st.splash.push({x:st.px,y:st.py,t:0})},
  move(x,y){const st=this.st;st.px=x;st.py=y-30},
  up(x,y,api){const st=this.st;if(!st.down||st.tear>0)return;st.down=false;
    const got=st.f.filter(f=>dist(f.x,f.y,st.px,st.py)<PR*.82);
    let w=0;for(const f of got)w+=f.k===1?.35:f.s/100;
    st.dur-=w*rnd(.6,1.1);st.splash.push({x:st.px,y:st.py,t:0});S.noise(.25,{v:.3,f:1200,to:400});
    if(st.dur<=0||(!got.length&&st.dur<.08)){this.tearPoi(api);if(got.length)api.float(st.px,st.py-60,'にげられた…',{size:22});return}
    if(got.length){for(const f of got){st.f.splice(st.f.indexOf(f),1);st.caught.push({x:f.x,y:f.y,k:f.k,s:f.s,t:0,sx:f.x,sy:f.y});st.f.push(this.newFish(true))}
      const n=got.reduce((a,f)=>a+(f.k===2?5:f.k===1?3:1),0);api.add(n);
      if(got.length>=2){S.perfect();api.float(st.px,st.py-60,got.length+'ひき同時！',{size:28,c:'#f3c84b'})}else S.good();
      if(got.some(f=>f.k===2)){api.flash('#fff6c8',.4);S.fanfare()}api.burst(st.px,st.py,{c:['#bfe3ee','#fff'],n:14,sp:200})}},
  tearPoi(api){const st=this.st;st.tear=1.2;st.down=false;st.poi--;S.bad();api.shake(6);api.float(st.px,st.py-50,'やぶれた！',{size:28,c:'#fff'})},
  update(dt,api){const st=this.st;
    if(st.down&&st.tear<=0){const sp=dist(st.px,st.py,st.lx,st.ly)/Math.max(dt,.001);st.dur-=(Math.max(0,sp-180)/5000+.006)*dt*6;st.lx=st.px;st.ly=st.py;if(st.dur<=0)this.tearPoi(api)}
    if(st.tear>0){st.tear-=dt;if(st.tear<=0){if(st.poi<=0){api.end();return}st.dur=1;S.coin()}}
    for(const f of st.f){f.sw+=dt*(6+f.v*.05);f.turn-=dt;if(f.turn<=0){f.turn=rnd(1,3);f.ta=f.a+rnd(-1.4,1.4)}
      const near=st.down&&dist(f.x,f.y,st.px,st.py)<PR*1.6;
      if(near){f.flee+=dt;const a=Math.atan2(f.y-st.py,f.x-st.px);if(f.flee>(f.k===2?.3:.7))f.ta=a}else f.flee=Math.max(0,f.flee-dt);
      if(f.x<40)f.ta=0;if(f.x>W-40)f.ta=Math.PI;if(f.y<170)f.ta=Math.PI/2;if(f.y>540)f.ta=-Math.PI/2;
      let d=((f.ta-f.a+Math.PI*3)%(Math.PI*2))-Math.PI;f.a+=d*Math.min(1,dt*2.5);const v=f.v*(near&&f.flee>.5?2.4:1)*(st.down&&dist(f.x,f.y,st.px,st.py)<PR?.25:1);
      f.x+=Math.cos(f.a)*v*dt;f.y+=Math.sin(f.a)*v*dt}
    for(let i=st.caught.length-1;i>=0;i--){const c=st.caught[i];c.t+=dt*1.6;const k=Math.min(1,c.t);c.x=lerp(c.sx,BX+rnd(-4,4),k);c.y=lerp(c.sy,BY,k)-Math.sin(k*Math.PI)*120;if(c.t>=1){st.caught.splice(i,1);st.bowl++;S.pop(1.3);api.burst(BX,BY-20,{c:['#bfe3ee','#fff'],n:8,sp:120})}}
    for(let i=st.splash.length-1;i>=0;i--){st.splash[i].t+=dt;if(st.splash[i].t>.6)st.splash.splice(i,1)}},
  drawHud(c,api){const st=this.st;D.rrect(c,70,20,280,56,28,'#fffdf8',3.5);D.text(c,api.score+'ひき',150,48,26,'#5b4d45');
    for(let i=0;i<3;i++){c.globalAlpha=i<st.poi?1:.25;c.lineWidth=3;c.strokeStyle='#f2a5c0';c.beginPath();c.arc(250+i*34,48,11,0,7);c.stroke();c.globalAlpha=1}
    const k=clamp(st.dur,0,1);D.rrect(c,110,86,200,12,6,'#fffdf8',2.5);if(st.tear<=0)D.rrect(c,111,87,198*k,10,5,k<.3?'#e2645a':'#8cc7d6',0)},
  draw(c,api){const st=this.st;c.fillStyle='#c98a5b';c.fillRect(0,api.top,W,api.bottom-api.top);D.rrect(c,12,130,W-24,440,30,'#8ccbdb',5);c.save();c.beginPath();c.roundRect?c.roundRect(14,132,W-28,436,28):c.rect(14,132,W-28,436);c.clip();
    c.fillStyle='#7dbfd0';for(let i=0;i<6;i++){c.beginPath();c.ellipse(80+i*60,200+((i*97)%300),30,6,0,0,7);c.fill()}
    for(const f of st.f)this.fish(c,f.x,f.y,f.s,f.a,f.k,f.sw);c.restore();
    for(const s of st.splash){c.globalAlpha=1-s.t/.6;c.strokeStyle='#fff';c.lineWidth=3;c.beginPath();c.ellipse(s.x,s.y,PR*(1+s.t*1.5),PR*.5*(1+s.t*1.5),0,0,7);c.stroke();c.globalAlpha=1}
    if(api.state==='play'||st.tear>0){const off=st.down?0:-14;this.poi(c,st.px,st.py+off,PR,st.dur,st.tear>0,st.down)}
    this.bowl(c,BX,BY,70);
    for(const f of st.caught)this.fish(c,f.x,f.y,f.s*.8,-Math.PI/2,f.k,f.t*20);
    D.text(c,'×'+st.bowl,BX+100,BY,24,'#fffdf8','center',OL,6)},
  __bot(api){const st=this.st;if(st.tear>0)return;if(!st.down){const f=pick(st.f.filter(f=>f.x>40&&f.x<W-40));if(f){st.tg=f;this.down(f.x+rnd(-60,60),f.y+30+rnd(-60,60),api)}}
    else{const f=st.tg;if(!f||!st.f.includes(f)){this.up(0,0,api);return}const d=dist(f.x,f.y,st.px,st.py);this.move(lerp(st.px,f.x,.12),lerp(st.py,f.y,.12)+30*0+30);if(d<14)this.up(0,0,api)}},
};
