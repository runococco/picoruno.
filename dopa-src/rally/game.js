/* ポンポンラリー：往復ボール。ラケット位置到達時のタップ判定。 */
const PY=600,WY=200;
const GAME={...META,sprites:['icon','ball','racket'],unit:'回',hudUnit:true,fullBleed:true,
  bgm:{bpm:126,root:62,scale:'major',prog:[1,5,4,5],seed:31,lead:'square',drums:'light',density:.5},
  ranks:[[0,'すかっ'],[10,'ラリー見習い'],[25,'ポンポン上手'],[50,'ラリーの達人'],[80,'止まらないラリー'],[120,'伝説のラケット']],
  shareText:(v,f)=>`ポンポンラリーで ${f}回 つづいた！`,
  icon(c,x,y,s){this.racket(c,x+s*.1,y+s*.2,s*.3);this.ball(c,x-s*.2,y-s*.2,s*.12)},
  racket(c,x,y,s){D.rrect(c,x-s*.12,y,s*.24,s*.9,s*.1,'#a67c52');D.ellipse(c,x,y-s*.35,s*.55,s*.5,'#e2645a');D.ellipse(c,x,y-s*.35,s*.4,s*.36,'#f2a5c0',0)},
  ball(c,x,y,r){D.circle(c,x,y,r,'#fbf7f0')},
  reset(api){this.st={y:PY-30,v:-500,n:0,dir:-1,dead:false,endT:0,t:0,sw:0,wait:0,spd:500};api.score=0},
  down(x,y,api){const st=this.st;if(st.dead||st.sw>0)return;st.sw=.25;const d=Math.abs(st.y-(PY-30));
    if(st.dir===1&&d<60){st.n++;api.score=st.n;const perfect=d<18;st.spd=Math.min(1300,500+st.n*20+(perfect?60:0));st.v=-st.spd;st.dir=-1;st.y=PY-30;
      api.combo=perfect?api.combo+1:0;S.pop(1+Math.min(st.n,40)*.015);api.burst(W/2,PY-30,{c:['#fff','#e2645a'],n:6,sp:140,r:3});
      api.float(W/2,PY-120,perfect?'ぴったり！':'ポン',{size:perfect?26:18,c:perfect?'#e2645a':'#5b4d45'});if(perfect)api.shake(2);if(st.n%10===0){S.fanfare();api.float(W/2,300,st.n+'回！',{size:34,c:'#e2645a'})}}
    else{this.miss(api,st.dir===1?'はやすぎ！':'すかっ')}},
  miss(api,txt){const st=this.st;st.dead=true;S.bad();api.shake(6);api.float(W/2,400,txt,{size:30,c:'#5b4d45'});api.combo=0},
  update(dt,api){const st=this.st;st.t+=dt;st.sw-=dt;if(st.dead){st.endT+=dt;if(st.endT>1)api.end();return}
    st.y+=st.v*dt;if(st.dir===-1&&st.y<=WY+14){st.y=WY+14;st.v=st.spd;st.dir=1;S.tap(.5)}
    if(st.dir===1&&st.y>PY+10)this.miss(api,'おそい…')},
  draw(c,api){const st=this.st;c.fillStyle='#e4f1ea';c.fillRect(0,api.top,W,api.bottom-api.top);c.fillStyle='#cfe3d6';c.fillRect(0,api.top,W,WY);c.fillStyle='#b8d2c3';c.fillRect(0,WY-6,W,6);
    c.setLineDash([6,10]);c.lineWidth=2;c.strokeStyle='#b8d2c3';c.beginPath();c.moveTo(W/2,WY);c.lineTo(W/2,PY);c.stroke();c.setLineDash([]);
    D.rrect(c,W/2-70,PY-20,140,8,4,'#e2645a',2);
    const r=14;D.ellipse(c,W/2,PY-8,r*1.2,r*.4,'rgba(90,77,69,.12)',0);this.ball(c,W/2+Math.sin(st.t*3)*6,st.y,r);
    c.save();c.translate(W/2+60,PY+10);c.rotate(st.sw>0?-.9:-.3);this.racket(c,0,0,60);c.restore();
    if(api.state==='play'&&st.n===0)D.text(c,'もどってきたらタップ！',W/2,PY+90,20,'#5b4d45')},
  __bot(api){const st=this.st;if(st.dir===1&&Math.abs(st.y-(PY-30))<st.spd*.04+10)this.down(0,0,api)},
};
