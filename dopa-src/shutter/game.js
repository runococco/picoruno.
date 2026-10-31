/* シャッターチャンス：フレーム中央との距離で採点。 */
const N=20,FX=W/2,FY=400,FW=300,FH=220;
const ANI=[['#f2a24a','とり',1.0],['#c9a070','くま',.7],['#fbf7f0','うさぎ',1.3],['#9aa3ab','ねずみ',1.6],['#f2a5c0','ぶた',.8],['#9cc86a','かえる',1.2]];
const GAME={...META,sprites:['icon','ani'],unit:'点',fullBleed:true,
  bgm:{bpm:110,root:60,scale:'major',prog:[1,6,2,5],seed:5,lead:'triangle',drums:'light',density:.45},
  ranks:[[0,'ぶれぶれ'],[400,'カメラ見習い'],[900,'いい写真'],[1500,'シャッターの達人'],[2200,'どうぶつ写真家'],[2800,'伝説のカメラ']],
  shareText:(v,f)=>`シャッターチャンスで ${f}点！`,
  icon(c,x,y,s){D.rrect(c,x-s*.45,y-s*.28,s*.9,s*.6,s*.08,'#5b5560');D.rrect(c,x-s*.15,y-s*.38,s*.3,s*.12,s*.04,'#5b5560');D.circle(c,x,y+s*.02,s*.2,'#b9c3cc');D.circle(c,x,y+s*.02,s*.1,'#7fb2e0');D.circle(c,x+s*.32,y-s*.16,s*.04,'#e2645a')},
  ani(c,x,y,s,col){D.circle(c,x-s*.45,y-s*.45,s*.22,col);D.circle(c,x+s*.45,y-s*.45,s*.22,col);D.rrect(c,x-s*.6,y-s*.5,s*1.2,s*1.1,s*.4,col);D.face(c,x,y,s)},
  reset(api){this.st={n:0,a:null,wait:0,res:[],t:0,flash:0,spawn:.5};api.score=0},
  down(x,y,api){const st=this.st;const a=st.a;if(!a||a.shot||st.wait>0)return;a.shot=true;st.n++;st.flash=1;S.shutter();
    const d=Math.abs(a.x-FX);const inF=d<FW/2-20;let pts,txt;if(!inF){pts=0;txt='見切れた…'}else{const k=1-d/(FW/2);pts=Math.round((40+k*k*100)*a.sp);if(k>.9){txt='ベストショット！';pts+=50}else if(k>.7)txt='いい写真！';else txt='まあまあ'}
    if(pts>=120){api.combo++;pts+=Math.min(api.combo,5)*10}else api.combo=0;api.add(pts);st.res.push(pts);
    api.float(FX,FY-FH/2-50,txt+(pts?' +'+pts:''),{size:pts>=150?32:24,c:pts>=120?'#e2645a':'#5b4d45'});if(pts>=150){S.perfect();api.burst(FX,FY,{c:['#fff','#f2c84b'],n:14,sp:200,shape:'s'})}else if(pts>=90)S.good();else if(pts)S.coin();else S.bad();
    st.wait=1;a.frozen=true},
  update(dt,api){const st=this.st;st.t+=dt;st.flash=Math.max(0,st.flash-dt*3);
    if(st.wait>0){st.wait-=dt;if(st.wait<=0){st.a=null;if(st.n>=N)api.end();st.spawn=rnd(.3,.9)}return}
    if(!st.a){st.spawn-=dt;if(st.spawn<=0){const k=pick(ANI);const dir=Math.random()<.5?1:-1;const lv=Math.min(1,st.n/N);st.a={x:FX-dir*(FW/2+80),y:FY+rnd(-40,50),v:dir*(160+rnd(0,120)+lv*140)*k[2],col:k[0],sp:k[2],shot:false,size:rnd(28,40)}}return}
    const a=st.a;if(a.frozen)return;a.x+=a.v*dt;a.y+=Math.sin(st.t*8)*20*dt;if(Math.abs(a.x-FX)>FW/2+90){st.a=null;st.spawn=rnd(.3,.8);api.combo=0;api.float(FX,FY-FH/2-50,'にげられた…',{size:22,c:'#5b4d45'})}},
  draw(c,api){const st=this.st;c.fillStyle='#eef0e8';c.fillRect(0,api.top,W,api.bottom-api.top);c.fillStyle='#d8e6c8';c.fillRect(0,FY+FH/2+40,W,api.bottom-FY-FH/2-40);for(let i=0;i<5;i++)D.circle(c,60+i*80,FY+FH/2+50,30+(i%2)*10,'#b8d69c',2.5);
    const a=st.a;if(a){c.save();c.beginPath();c.rect(FX-FW/2-100,FY-FH/2-60,FW+200,FH+120);c.clip();this.ani(c,a.x,a.y,a.size,a.col);c.restore()}
    // frame
    c.lineWidth=6;c.strokeStyle=OL;c.strokeRect(FX-FW/2,FY-FH/2,FW,FH);c.lineWidth=2;c.strokeStyle='rgba(90,77,69,.35)';c.beginPath();c.moveTo(FX,FY-FH/2);c.lineTo(FX,FY+FH/2);c.moveTo(FX-FW/2,FY);c.lineTo(FX+FW/2,FY);c.stroke();
    c.lineWidth=3;c.strokeStyle='#e2645a';c.beginPath();c.arc(FX,FY,30,0,Math.PI*2);c.stroke();
    if(st.flash>0){c.fillStyle=`rgba(255,255,255,${st.flash*.9})`;c.fillRect(FX-FW/2,FY-FH/2,FW,FH)}
    D.text(c,st.n+'/'+N,FX,110,18,'#5b4d45');for(let i=0;i<N;i++)D.circle(c,FX-(N-1)*9+i*18,150,6,i<st.res.length?(st.res[i]>=120?'#e2645a':st.res[i]?'#fff':'#5b5560'):'#fff',2);
    if(api.state==='play'&&st.n===0)D.text(c,'ど真ん中でタップ！',FX,FY+FH/2+70,22,'#5b4d45')},
  __bot(api){const st=this.st;const a=st.a;if(!a||a.shot||st.wait>0)return;if(Math.abs(a.x+a.v*.03-FX)<Math.abs(a.v)*.03+6)this.down(0,0,api)},
};
