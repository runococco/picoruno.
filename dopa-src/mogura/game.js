/* もぐらぽこぽこ：3x3の穴。出現からの速さで採点。 */
const HOLES=[];for(let r=0;r<3;r++)for(let q=0;q<3;q++)HOLES.push({x:90+q*120,y:300+r*130});
const GAME={...META,sprites:['icon','mole'],unit:'点',time:30,fullBleed:true,
  bgm:{bpm:150,root:60,scale:'major',prog:[1,4,5,4],seed:9,lead:'square',drums:'four',density:.65},
  ranks:[[0,'すかすか'],[300,'もぐら見習い'],[700,'ぽこぽこ上手'],[1200,'もぐらたたきの達人'],[1800,'もぐらの天敵'],[2500,'伝説のハンマー']],
  shareText:(v,f)=>`もぐらぽこぽこで ${f}点！`,
  icon(c,x,y,s){D.ellipse(c,x,y+s*.3,s*.42,s*.14,'#5b4d45');this.mole(c,x,y+s*.3,s*.3,'n',1)},
  mole(c,x,y,s,k,up){const h=s*2.2*up;c.save();c.beginPath();c.rect(x-s*1.5,y-s*3,s*3,s*3+2);c.clip();const col=k==='gold'?'#f2c84b':'#a67c52';
    D.rrect(c,x-s*.75,y-h,s*1.5,h+s,s*.7,col);D.ellipse(c,x,y-h+s*.75,s*.38,s*.3,'#f1dcc0');D.circle(c,x,y-h+s*.6,s*.14,'#e2645a',2);D.face(c,x,y-h+s*.5,s*1.1);
    if(k==='helm')D.rrect(c,x-s*.7,y-h-s*.15,s*1.4,s*.55,s*.3,'#7fb2e0');c.restore()},
  reset(api){this.st={m:HOLES.map(()=>null),spawn:0,t:0,hits:0};api.score=0},
  down(x,y,api){const st=this.st;for(let i=0;i<9;i++){const m=st.m[i],h=HOLES[i];if(!m||m.up<.5||m.dead)continue;if(Math.abs(x-h.x)<48&&y>h.y-80&&y<h.y+20){
      if(m.k==='helm'&&!m.hit){m.hit=true;S.clink();api.float(h.x,h.y-80,'カン！',{size:20,c:'#7fb2e0'});api.shake(2);return}
      const fast=Math.max(0,1-m.age/1.2);const pts=(m.k==='gold'?150:50)+Math.round(fast*50);api.combo++;api.add(pts+Math.min(api.combo,10)*5);m.dead=true;m.up=0;st.hits++;
      S.thud();S.pop(1.1+Math.min(api.combo,20)*.02);api.burst(h.x,h.y-40,{c:[m.k==='gold'?'#f2c84b':'#a67c52','#fff'],n:8,sp:160,r:4});api.float(h.x,h.y-80,'+'+(pts+Math.min(api.combo,10)*5),{size:fast>.6?26:20,c:m.k==='gold'?'#f2c84b':'#fff'});
      if(m.k==='gold'){S.perfect();api.flash('#fff6c8',.3)}if(api.combo%10===0){S.fanfare();api.float(W/2,200,api.combo+'コンボ！',{size:32,c:'#f2c84b'})}return}}
    S.tap(.3);api.combo=0},
  update(dt,api){const st=this.st;st.t+=dt;const lv=Math.min(1,st.t/30);st.spawn-=dt;
    if(st.spawn<=0){st.spawn=rnd(.35,.7)-lv*.25;const free=[];st.m.forEach((m,i)=>{if(!m)free.push(i)});if(free.length){const i=pick(free);const r=Math.random();st.m[i]={k:r<.08?'gold':r<.22?'helm':'n',age:0,up:0,stay:rnd(.9,1.6)-lv*.5}}}
    for(let i=0;i<9;i++){const m=st.m[i];if(!m)continue;m.age+=dt;if(m.dead){m.gone=(m.gone||0)+dt;if(m.gone>.25)st.m[i]=null;continue}
      if(m.age<.2)m.up=m.age/.2;else if(m.age<m.stay)m.up=1;else m.up=Math.max(0,1-(m.age-m.stay)/.2);if(m.age>m.stay+.2){st.m[i]=null;if(m.k!=='helm')api.combo=0}}},
  draw(c,api){const st=this.st;c.fillStyle='#eef2dc';c.fillRect(0,api.top,W,api.bottom-api.top);c.fillStyle='#d7e1b8';c.fillRect(0,api.top,W,170);
    for(let i=0;i<9;i++){const h=HOLES[i];D.ellipse(c,h.x,h.y,46,16,'#5b4d45',0);const m=st.m[i];if(m&&m.up>0){this.mole(c,h.x,h.y,28,m.k,m.up);if(m.k==='helm'&&m.hit)D.text(c,'!',h.x+30,h.y-70,20,'#e2645a')}D.ellipse(c,h.x,h.y+4,48,16,'rgba(0,0,0,0)',3)}
    if(api.state==='play'&&st.t<2)D.text(c,'出てきたらタップ！',W/2,220,22,'#5b4d45')},
  __bot(api){const st=this.st;for(let i=0;i<9;i++){const m=st.m[i];if(m&&!m.dead&&m.up>=.6&&Math.random()<.6){this.down(HOLES[i].x,HOLES[i].y-30,api);return}}},
};
