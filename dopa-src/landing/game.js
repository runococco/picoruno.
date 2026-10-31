/* そーっとちゃくりく：月面着陸。縦速度と横ずれを見て着地判定。 */
const GY=620;
const GAME={...META,sprites:['icon','ship'],unit:'回',hudUnit:true,fullBleed:true,comboHud:false,
  bgm:{bpm:90,root:57,scale:'minor',prog:[1,6,4,5],seed:93,lead:'triangle',drums:'none',density:.4,stab:false},
  ranks:[[0,'ドカン'],[1,'はじめての着地'],[3,'なかなかのパイロット'],[5,'着地の達人'],[8,'月の宇宙飛行士'],[12,'伝説のパイロット']],
  shareText:(v,f)=>`そーっとちゃくりくで ${f}回 着地した！`,
  icon(c,x,y,s){this.ship(c,x,y+s*.05,s*.5,.8,0);D.rrect(c,x-s*.35,y+s*.38,s*.7,s*.08,4,'#8a8392')},
  ship(c,x,y,s,th,tilt){c.save();c.translate(x,y);c.rotate(tilt);
    if(th>0){const f=s*(.4+th*.5+rnd(0,.15));D.poly(c,[[-s*.15,s*.35],[s*.15,s*.35],[0,s*.35+f]],'#f2a24a',2.5);D.poly(c,[[-s*.08,s*.35],[s*.08,s*.35],[0,s*.35+f*.6]],'#f4d66d',0)}
    c.lineWidth=4;c.strokeStyle=OL;c.beginPath();c.moveTo(-s*.25,s*.25);c.lineTo(-s*.42,s*.5);c.moveTo(s*.25,s*.25);c.lineTo(s*.42,s*.5);c.stroke();
    D.rrect(c,-s*.3,-s*.1,s*.6,s*.45,s*.12,'#b9c3cc');D.ellipse(c,0,-s*.2,s*.32,s*.35,'#fbf7f0');D.circle(c,0,-s*.22,s*.16,'#7fb2e0',3);D.face(c,0,-s*.2,s*.26);c.restore()},
  reset(api){this.st={lv:0,x:W/2,y:120,vx:0,vy:0,fuel:1,th:0,pad:{x:W/2,w:150},wait:0,tx:null,boom:0,t:0};api.score=0},
  next(){const st=this.st;st.x=rnd(100,W-100);st.y=100;st.vx=rnd(-30,30);st.vy=0;st.fuel=1;st.pad={x:rnd(90,W-90),w:Math.max(60,150-st.lv*12)};st.boom=0},
  down(x,y){this.st.th=1;this.st.tx=x;this.st.sx=x},move(x){const st=this.st;if(st.th)st.tx=x},up(){this.st.th=0;this.st.tx=null},
  key(k){const st=this.st;if(k===' ')st.th=1;if(k==='ArrowLeft')st.kx=-1;if(k==='ArrowRight')st.kx=1},keyUp(k){const st=this.st;if(k===' ')st.th=0;if(k==='ArrowLeft'||k==='ArrowRight')st.kx=0},
  update(dt,api){const st=this.st;st.t+=dt;if(st.wait>0){st.wait-=dt;if(st.wait<=0){if(st.dead){api.end();return}this.next()}return}
    const th=st.th&&st.fuel>0?1:0;if(th){st.fuel-=dt*.22;st.vy-=260*dt;if(Math.floor(st.t*20)%2===0)api.burst(st.x,st.y+30,{c:['#f2a24a','#f4d66d'],n:1,sp:80,r:3,g:-200,life:.3})}
    st.vy+=90*dt;if(st.tx!==null){const d=clamp((st.tx-st.sx)*2,-120,120);st.vx+=(d-st.vx)*dt*3}else if(st.kx)st.vx+=st.kx*150*dt;else st.vx*=1-dt;
    st.x+=st.vx*dt;st.y+=st.vy*dt;st.x=clamp(st.x,30,W-30);
    if(st.y>=GY-30){st.y=GY-30;const onPad=Math.abs(st.x-st.pad.x)<st.pad.w/2-10;const soft=st.vy<75;
      if(onPad&&soft){st.lv++;api.score=st.lv;st.wait=1.5;S.thud();S.fanfare();api.flash('#fff',.3);api.float(st.x,st.y-80,st.vy<35?'そーっと！完璧！':'着地！',{size:30,c:'#f3c84b'});api.burst(st.x,GY,{c:['#f4d66d','#fff'],n:14,shape:'star',sp:200})}
      else{st.dead=true;st.boom=1;st.wait=1.6;S.boom();api.shake(14);api.flash('#fff',.7);api.burst(st.x,st.y,{c:['#f2a24a','#f4d66d','#fff','#8a8392'],n:34,sp:320});api.float(st.x,st.y-80,onPad?'速すぎ！ドカン':'台からはずれた…',{size:30,c:'#fff'})}}},
  drawHud(c,api){const st=this.st;D.rrect(c,70,20,280,56,28,'#fffdf8',3.5);D.text(c,api.score+'回　速さ'+Math.round(Math.max(0,st.vy)),W/2,48,20,st.vy>=75?'#e2645a':'#5b4d45');
    D.rrect(c,110,86,200,12,6,'#fffdf8',2.5);const k=clamp(st.fuel,0,1);D.rrect(c,111,87,198*k,10,5,k<.3?'#e2645a':'#f2c84b',0);D.text(c,'燃料',90,92,13,'#fffdf8')},
  draw(c,api){const st=this.st;c.fillStyle='#2f2b45';c.fillRect(0,api.top,W,api.bottom-api.top);c.fillStyle='#e9e2f6';for(let i=0;i<40;i++)c.fillRect((i*97)%W,(i*173)%GY,2,2);
    D.circle(c,340,150,36,'#7fb2e0',3);
    c.fillStyle='#8a8392';c.beginPath();c.moveTo(0,GY);for(let x=0;x<=W;x+=30)c.lineTo(x,GY-Math.abs(Math.sin(x*.3))*18-(x>st.pad.x-st.pad.w/2-20&&x<st.pad.x+st.pad.w/2+20?0:0));c.lineTo(W,api.bottom);c.lineTo(0,api.bottom);c.fill();c.fillStyle='#6d6672';c.fillRect(0,GY+10,W,api.bottom-GY-10);
    D.rrect(c,st.pad.x-st.pad.w/2,GY-8,st.pad.w,14,5,'#f2c84b',3);for(let i=-1;i<=1;i++)D.circle(c,st.pad.x+i*st.pad.w*.35,GY-1,4,st.t%1<.5?'#e2645a':'#fbf7f0',0);
    if(!st.boom)this.ship(c,st.x,st.y,70,st.th&&st.fuel>0?1:0,clamp(st.vx*.003,-.3,.3));
    if(api.t<3&&api.state==='play')D.text(c,'おして噴射・左右にずらして移動',W/2,250,16,'#fff','center',OL,4)},
  __bot(api){const st=this.st;if(st.wait>0)return;const h=GY-30-st.y;st.th=(st.vy>Math.max(30,h*.5))?1:0;st.sx=st.x;st.tx=st.x+(st.pad.x-st.x)*.5-st.vx*.3},
};
