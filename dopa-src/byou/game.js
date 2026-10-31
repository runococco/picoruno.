/* ぴったり10びょう：10秒を体内時計で止める。 */
const GAME={...META,sprites:['icon','clock'],unit:'点',fullBleed:true,comboHud:false,
  bgm:{bpm:60,root:60,scale:'major',prog:[1,4,1,5],seed:12,lead:'triangle',drums:'none',density:.3,stab:false},
  ranks:[[0,'体内時計ゆるゆる'],[300,'時計見習い'],[600,'なかなか正確'],[900,'体内時計の達人'],[1200,'人間ストップウォッチ'],[1450,'伝説の10秒']],
  shareText:(v,f)=>`ぴったり10びょうで ${f}点！いちばん近かったのは ${(GAME.st&&GAME.st.best!==undefined)?GAME.st.best.toFixed(2)+'秒':'？'}`,
  icon(c,x,y,s){this.clock(c,x,y,s*.42,10,true)},
  clock(c,x,y,r,sec,showFace){D.circle(c,x,y,r,'#fbf7f0');D.circle(c,x,y+r*.0,r*.85,'#fff',0);for(let i=0;i<12;i++){const a=i*Math.PI/6;D.circle(c,x+Math.cos(a)*r*.72,y+Math.sin(a)*r*.72,i%3?r*.03:r*.05,'#5b4d45',0)}
    D.rrect(c,x-r*.12,y-r*1.12,r*.24,r*.18,r*.05,'#e2645a',2.5);
    const a=sec/60*Math.PI*2-Math.PI/2;c.lineWidth=Math.max(2,r*.07);c.strokeStyle='#e2645a';c.lineCap='round';c.beginPath();c.moveTo(x,y);c.lineTo(x+Math.cos(a)*r*.62,y+Math.sin(a)*r*.62);c.stroke();D.circle(c,x,y,r*.07,'#5b4d45',0);
    if(showFace)D.face(c,x,y+r*.3,r*.9)},
  reset(api){this.st={n:0,run:false,t:0,wait:0,res:[],best:undefined,tt:0};api.score=0},
  down(x,y,api){const st=this.st;if(st.wait>0||st.n>=10)return;
    if(!st.run){st.run=true;st.t=0;S.tick();return}
    st.run=false;st.n++;const d=Math.abs(st.t-10);if(st.best===undefined||d<Math.abs(st.best-10))st.best=st.t;let pts,txt;
    if(d<.02){pts=150;txt='ぴったり！！'}else if(d<.1){pts=120;txt='すごい！'}else if(d<.3){pts=80;txt='おしい！'}else if(d<.7){pts=40;txt='まあまあ'}else{pts=10;txt='ずれてる…'}
    api.add(pts);st.res.push(st.t);st.wait=1.6;st.last=st.t;
    api.float(W/2,250,txt+' +'+pts,{size:pts>=120?32:26,c:pts>=120?'#9cc86a':'#5b4d45',vy:-20,life:1.2});if(pts>=150){S.perfect();api.flash('#fff',.3);api.burst(W/2,400,{c:['#9cc86a','#f2c84b','#fff'],n:18,sp:240,shape:'s'})}else if(pts>=120)S.good();else if(pts>=80)S.coin();else S.bad()},
  update(dt,api){const st=this.st;st.tt+=dt;if(st.run){st.t+=dt;if(st.t>20){this.down(0,0,api)}}
    if(st.wait>0){st.wait-=dt;if(st.wait<=0&&st.n>=10)api.end()}},
  draw(c,api){const st=this.st;c.fillStyle='#eef0e8';c.fillRect(0,api.top,W,api.bottom-api.top);
    const hide=st.run&&st.t>3;this.clock(c,W/2,400,120,st.run?st.t:(st.last||0),false);
    if(hide){D.circle(c,W/2,400,124,'#dfe3d6',3);D.text(c,'？',W/2,415,60,'#5b4d45')}
    const txt=st.run?(hide?'…':st.t.toFixed(2)):(st.last!==undefined?st.last.toFixed(2):'0.00');D.rrect(c,W/2-90,560,180,56,14,'#fff',3);D.text(c,txt+' 秒',W/2,598,30,'#5b4d45');
    D.text(c,st.n+'/10',W/2,110,18,'#5b4d45');
    if(api.state==='play'){if(!st.run&&st.wait<=0&&st.n<10)D.text(c,st.n===0?'タップでスタート':'もう一回',W/2,200,22,'#5b4d45');else if(st.run&&st.t<3)D.text(c,'10.00秒でタップ！',W/2,200,22,'#5b4d45')}
    for(let i=0;i<st.res.length;i++){const d=Math.abs(st.res[i]-10);D.circle(c,W/2-99+i*22,150,8,d<.1?'#9cc86a':d<.3?'#f2c84b':'#e2645a',2.5)}},
  __bot(api){const st=this.st;if(st.wait>0||st.n>=10)return;if(!st.run){if(Math.random()<.3)this.down(0,0,api)}else if(st.t>=9.9+Math.random()*.3)this.down(0,0,api)},
};
