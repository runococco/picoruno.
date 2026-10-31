/* ぴょんぴょんマシュマロ：自動ジャンプで足場をのぼる縦スクロール。左右はつながっている。 */
const GR=1500,JV=-760;
const GAME={...META,sprites:['icon','mallow','plat'],unit:'m',hudUnit:true,fullBleed:true,comboHud:false,
  bgm:{bpm:138,root:64,scale:'major',prog:[1,4,5,4],seed:33,lead:'square',drums:'pop',density:.6},
  ranks:[[0,'ふもと'],[50,'木のてっぺん'],[150,'雲の上'],[300,'空のはて'],[500,'宇宙のいりぐち'],[800,'月まで']],
  shareText:(v,f)=>`ぴょんぴょんマシュマロで ${f}m のぼった！`,
  icon(c,x,y,s){c.save();c.translate(x,y);c.scale(s/150,s/150);this.plat(c,22,52,120,0);this.plat(c,-48,-48,80,3,1);this.mallow(c,22,14,64,1);c.restore()},
  mallow(c,x,y,s,sq){D.rrect(c,x-s*.42*(2-sq),y-s*.5*sq,s*.84*(2-sq),s*.95*sq,s*.3,'#fbf2f4');D.face(c,x,y-s*.05*sq+s*.1,s*.6)},
  plat(c,x,y,w,k,t=0){if(k===0){D.rrect(c,x-w/2,y-9,w,18,7,'#e3b47a',3);c.fillStyle='#b98450';for(let i=1;i<4;i++){c.beginPath();c.arc(x-w/2+i*w/4,y,2.2,0,7);c.fill()}}
    else if(k===1){D.rrect(c,x-w/2,y-9,w,18,7,'#a9d6e6',3)}// うごく
    else if(k===2){D.rrect(c,x-w/2,y-8,w,16,3,'#f4e2b4',3);c.strokeStyle='#d9bf8a';c.lineWidth=2;for(let i=1;i<5;i++){c.beginPath();c.moveTo(x-w/2+i*w/5,y-7);c.lineTo(x-w/2+i*w/5,y+7);c.stroke()}}
    if(k===3){D.rrect(c,x-w/2,y-9,w,18,7,'#e3b47a',3);const b=1-Math.min(1,t)*.4;D.rrect(c,x-15,y-9-22*b,30,22*b,8,'#f08a8a',3)}},
  reset(api){const st=this.st={x:W/2,y:560,vx:0,vy:JV,cam:0,top:0,p:[],tx:null,sq:1,maxH:0,kx:0,stars:[]};
    st.p.push({x:W/2,y:640,w:110,k:0});let y=640;while(y>-800){y-=rnd(60,100);st.p.push(this.mk(y,0))}api.score=0},
  mk(y,h){const lv=Math.min(1,h/6000),r=Math.random();let k=0;if(r<.12+lv*.25)k=1;else if(r<.2+lv*.35)k=2;else if(r<.26+lv*.36)k=3;
    return{x:rnd(50,W-50),y,w:rnd(70,96)-lv*18,k,vx:k===1?pick([-1,1])*rnd(50,90+lv*60):0,broke:-1,t:9}},
  down(x){this.st.tx=x},move(x){if(this.st.tx!==null)this.st.tx=x},up(){this.st.tx=null},
  key(k,api,d){if(k==='ArrowLeft')this.st.kx=-1;if(k==='ArrowRight')this.st.kx=1},keyUp(k){if(k==='ArrowLeft'||k==='ArrowRight')this.st.kx=0},
  update(dt,api){const st=this.st;
    let ax=st.tx!==null?clamp((st.tx-st.x)*14,-900,900):st.kx*700;st.vx+=(ax-st.vx)*Math.min(1,dt*10);if(st.tx===null&&!st.kx)st.vx*=1-dt*4;
    st.x+=st.vx*dt;if(st.x<-20)st.x+=W+40;if(st.x>W+20)st.x-=W+40;
    const oy=st.y;st.vy+=GR*dt;st.y+=st.vy*dt;st.sq+=(1-st.sq)*Math.min(1,dt*10);
    for(const p of st.p){if(p.k===1){p.x+=p.vx*dt;if(p.x<p.w/2||p.x>W-p.w/2)p.vx*=-1}p.t+=dt;if(p.broke>=0){p.broke+=dt;p.y+=p.broke*600*dt}}
    if(st.vy>0)for(const p of st.p){if(p.broke>=0)continue;if(oy+14<=p.y-8&&st.y+14>=p.y-8&&Math.abs(st.x-p.x)<p.w/2+14){
        if(p.k===2){p.broke=0;S.noise(.15,{v:.3,f:1500});api.burst(p.x,p.y-st.cam,{c:['#f4e2b4','#d9bf8a'],n:8,sp:120,shape:'s'});continue}
        st.y=p.y-22;st.vy=p.k===3?JV*1.65:JV;st.sq=.65;
        if(p.k===3){p.t=0;S.boing(1.3);api.burst(st.x,p.y-st.cam,{c:['#f08a8a','#fff'],n:12,sp:220});api.float(st.x,p.y-st.cam-40,'ぽよよーん！',{size:22,c:'#f08a8a'})}else S.boing(1+Math.random()*.1);break}}
    // カメラ
    const want=st.y-330;if(want<st.cam)st.cam=want;
    const h=Math.max(0,Math.round((560-st.y)/20));if(h>st.maxH){const step=Math.floor(h/50)>Math.floor(st.maxH/50);st.maxH=h;api.score=h;if(step&&h>0){S.coin(1.3);api.float(W/2,200,h+'m！',{size:30,c:'#f3c84b'})}}
    while(st.p.length&&st.p[0].y-st.cam>H+80)st.p.shift();
    let topY=Math.min(...st.p.map(p=>p.y));while(topY>st.cam-200){const lv=Math.min(1,-st.cam/6000);topY-=rnd(60,90+lv*60);st.p.push(this.mk(topY,-st.cam))}
    if(st.y-st.cam>H+40){S.bad();api.end()}},
  overText:'まっさかさま！',
  draw(c,api){const st=this.st,h=-st.cam;const sky=clamp(h/12000,0,1);
    c.fillStyle=`hsl(${210+sky*40},${55-sky*20}%,${92-sky*70}%)`;c.fillRect(0,api.top,W,api.bottom-api.top);
    // 雲・星の背景
    for(let i=0;i<10;i++){const y=((i*160-st.cam*.3)%1600+1600)%1600-200;if(sky<.6){c.globalAlpha=.7-sky;D.ellipse(c,(i*137)%W,y,60,22,'#fff',0);c.globalAlpha=1}else D.star(c,(i*137)%W,y,6,'#f4d66d',0)}
    c.save();c.translate(0,-st.cam);
    for(const p of st.p){if(p.y-st.cam<api.top-30||p.y-st.cam>api.bottom+30)continue;c.globalAlpha=p.broke>=0?Math.max(0,1-p.broke*2):1;this.plat(c,p.x,p.y,p.w,p.k,p.t*3);c.globalAlpha=1}
    const sq=st.sq,s2=2-sq;this.mallow(c,st.x,st.y+14,44,sq);if(st.x<30)this.mallow(c,st.x+W+40,st.y+14,44,sq);if(st.x>W-30)this.mallow(c,st.x-W-40,st.y+14,44,sq);
    c.restore()},
  __bot(api){const st=this.st;let best=null,bs=-1e9;for(const p of st.p){if(p.broke>=0||p.k===2)continue;const dy=st.y-p.y;if(dy<-10||dy>260)continue;const s=dy-Math.abs(p.x-st.x)*.4+(p.k===3?80:0);if(s>bs){bs=s;best=p}}
    if(st.vy>0){let lo=null;for(const p of st.p){if(p.broke>=0||p.k===2)continue;if(p.y>st.y&&p.y-st.y<300&&(!lo||Math.abs(p.x-st.x)<Math.abs(lo.x-st.x)))lo=p}if(lo)best=lo}
    st.tx=best?best.x:null},
};
