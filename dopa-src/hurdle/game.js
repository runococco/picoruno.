/* ハードルダッシュ：横スクロールランナー。タップジャンプで障害物を越える。 */
const GY=560,PX=110;
const GAME={...META,sprites:['icon','usagi'],unit:'m',hudUnit:true,fullBleed:true,
  bgm:{bpm:160,root:62,scale:'major',prog:[1,5,6,4],seed:37,lead:'square',drums:'four',density:.65},
  ranks:[[0,'ころん'],[100,'かけっこ見習い'],[300,'ぴょんぴょん上手'],[600,'ハードルの達人'],[1000,'風のうさぎ'],[1500,'伝説のランナー']],
  shareText:(v,f)=>`ハードルダッシュで ${f}m はしった！`,
  icon(c,x,y,s){D.rrect(c,x+s*.1,y,s*.3,s*.08,3,'#e2645a');c.lineWidth=3;c.strokeStyle=OL;c.beginPath();c.moveTo(x+s*.12,y+s*.08);c.lineTo(x+s*.12,y+s*.4);c.moveTo(x+s*.38,y+s*.08);c.lineTo(x+s*.38,y+s*.4);c.stroke();this.usagi(c,x-s*.2,y-s*.1,s*.2,1)},
  usagi(c,x,y,s,run){c.save();c.translate(x,y);D.ellipse(c,-s*.35,-s*1.3,s*.2,s*.6,'#fbf7f0');D.ellipse(c,s*.35,-s*1.3,s*.2,s*.6,'#fbf7f0');D.ellipse(c,-s*.35,-s*1.3,s*.09,s*.4,'#f2a5c0',0);D.ellipse(c,s*.35,-s*1.3,s*.09,s*.4,'#f2a5c0',0);
    D.ellipse(c,0,0,s*.95,s*.85,'#fbf7f0');D.face(c,0,-s*.05,s*1.4);const k=Math.sin(run*20)*s*.3;D.ellipse(c,-s*.4,s*.9,s*.3,s*.16,'#fbf7f0',2.5);D.ellipse(c,s*.4+k,s*.9,s*.3,s*.16,'#fbf7f0',2.5);c.restore()},
  reset(api){this.st={x:0,v:260,jy:0,jv:0,hs:[],next:400,fall:0,miss:0,dead:false,endT:0,t:0};api.score=0},
  down(x,y,api){const st=this.st;if(st.dead||st.jy<0||st.fall>0)return;st.jv=-620;S.boing(1.1)},
  update(dt,api){const st=this.st;st.t+=dt;if(st.dead){st.endT+=dt;if(st.endT>1)api.end();return}
    if(st.fall>0){st.fall-=dt;return}
    st.x+=st.v*dt;api.score=Math.floor(st.x/20);st.v=Math.min(620,st.v+dt*9);
    st.jv+=1700*dt;st.jy+=st.jv*dt;if(st.jy>0){st.jy=0;st.jv=0}
    if(st.x+W>st.next){st.hs.push({x:st.next,h:rnd(40,70),hit:false});st.next+=rnd(260,520)+st.v*.3}
    for(const h of st.hs){if(h.hit||h.passed)continue;const sx=h.x-st.x;if(sx<PX+22&&sx>PX-26){if(-st.jy<h.h-6){h.hit=true;st.miss++;st.fall=.8;st.v=Math.max(260,st.v*.6);api.combo=0;S.thud();S.bad();api.shake(8);api.burst(PX,GY,{c:['#e2645a','#5b4d45'],n:10,sp:160});api.float(PX+40,GY-120,st.miss>=3?'ころん…おしまい':'ころん！',{size:26,c:'#e2645a'});if(st.miss>=3)st.dead=true}
        else if(sx<PX-20){h.passed=true;api.combo++;S.pop(1+Math.min(api.combo,20)*.02);api.float(PX+30,GY-130,'+1',{size:18,c:'#5b4d45'});if(api.combo%10===0){S.fanfare();api.float(W/2,250,api.combo+'連続！',{size:32,c:'#f2a24a'})}}}}
    st.hs=st.hs.filter(h=>h.x-st.x>-100)},
  draw(c,api){const st=this.st;c.fillStyle='#fdf3e3';c.fillRect(0,api.top,W,api.bottom-api.top);for(let i=0;i<4;i++)D.ellipse(c,((i*160-st.x*.15)%(W+120)+W+120)%(W+120)-60,120+i*80,46,15,'#fff',0);
    c.fillStyle='#e8a86b';c.fillRect(0,GY+20,W,api.bottom-GY-20);c.fillStyle='#d9955a';for(let x=-((st.x)%60);x<W;x+=60)c.fillRect(x,GY+40,30,4);c.fillStyle='#c9d7a0';c.fillRect(0,GY,W,20);
    for(const h of st.hs){const sx=h.x-st.x;if(sx<-60||sx>W+60)continue;const tilt=h.hit?.9:0;c.save();c.translate(sx,GY+16);c.rotate(tilt);D.rrect(c,-24,-h.h,48,10,4,'#e2645a');c.lineWidth=3;c.strokeStyle=OL;c.beginPath();c.moveTo(-18,-h.h+10);c.lineTo(-18,0);c.moveTo(18,-h.h+10);c.lineTo(18,0);c.stroke();c.restore()}
    const fy=GY-14+st.jy;if(st.jy<0)D.ellipse(c,PX,GY+10,30+st.jy*.1,8,'rgba(90,77,69,.15)',0);
    c.save();if(st.fall>0){c.translate(PX,GY);c.rotate(-1.2);c.translate(-PX,-GY)}this.usagi(c,PX,fy-22,30,st.t);c.restore();
    for(let i=0;i<3;i++)D.circle(c,W/2-30+i*30,150,9,i<3-st.miss?'#e2645a':'#e7e2d8',2.5);
    if(api.state==='play'&&st.x<200)D.text(c,'タップでジャンプ！',W/2,260,22,'#5b4d45')},
  __bot(api){const st=this.st;const h=st.hs.find(h=>!h.hit&&!h.passed&&h.x-st.x>PX);if(h&&h.x-st.x-PX<st.v*.32)this.down(0,0,api)},
};
