/* きのぼりダッシュ：左右タップ。次の段の枝と同じ側にいたら終了。 */
const SEG=70,TX=W/2;
const GAME={...META,sprites:['icon','koala'],unit:'m',hudUnit:true,fullBleed:true,comboHud:false,
  bgm:{bpm:150,root:60,scale:'major',prog:[1,4,5,4],seed:14,lead:'square',drums:'four',density:.65},
  ranks:[[0,'ゴツン'],[20,'きのぼり見習い'],[50,'トントン上手'],[100,'きのぼりの達人'],[200,'こずえの主'],[300,'伝説のコアラ']],
  shareText:(v,f)=>`きのぼりダッシュで ${f}m のぼった！`,
  icon(c,x,y,s){D.rrect(c,x-s*.12,y-s*.5,s*.24,s,s*.06,'#a67c52');D.rrect(c,x+s*.1,y-s*.2,s*.3,s*.1,s*.04,'#a67c52');D.circle(c,x+s*.4,y-s*.15,s*.12,'#9cc86a');this.koala(c,x-s*.3,y+s*.15,s*.18,1)},
  koala(c,x,y,s,dir){c.save();c.translate(x,y);c.scale(dir,1);D.circle(c,-s*.8,-s*.6,s*.42,'#9aa3ab');D.circle(c,s*.8,-s*.6,s*.42,'#9aa3ab');D.circle(c,-s*.8,-s*.6,s*.22,'#f2a5c0',0);D.circle(c,s*.8,-s*.6,s*.22,'#f2a5c0',0);
    D.rrect(c,-s*.9,-s*.9,s*1.8,s*2,s*.8,'#b4bcc3');D.ellipse(c,0,s*.05,s*.22,s*.3,'#5b4d45',0);D.face(c,0,-s*.25,s*1.5);c.restore()},
  reset(api){this.st={br:[],side:-1,n:0,gauge:1,dead:false,endT:0,t:0,anim:0,leaves:[]};api.score=0;for(let i=0;i<12;i++)this.addBr(i)},
  addBr(i){const st=this.st;const r=Math.random();st.br[i]=i<2?0:r<.4?-1:r<.8?1:0;if(i>=2&&st.br[i-1]!==0&&st.br[i]!==0&&st.br[i]!==st.br[i-1])st.br[i]=0},
  down(x,y,api){const st=this.st;if(st.dead)return;st.side=x<W/2?-1:1;st.br.shift();this.addBr(st.br.length);st.n++;api.score=st.n;st.anim=1;st.gauge=Math.min(1,st.gauge+.05);
    S.tap(.8+Math.min(st.n,50)*.006);api.burst(TX+st.side*30,500,{c:['#9cc86a','#fff'],n:3,sp:100,r:3});
    if(st.br[0]===st.side){st.dead=true;S.bad();S.thud();api.shake(10);api.float(W/2,300,'ゴツン！',{size:34,c:'#e2645a'});return}
    if(st.n%25===0){S.fanfare();api.float(W/2,250,st.n+'m！',{size:34,c:'#9cc86a'});api.flash('#fff',.2)}},
  update(dt,api){const st=this.st;st.t+=dt;st.anim=Math.max(0,st.anim-dt*8);if(st.dead){st.endT+=dt;if(st.endT>1)api.end();return}
    st.gauge-=dt*(.12+Math.min(st.n,150)*.0015);if(st.gauge<=0){st.dead=true;S.bad();api.float(W/2,300,'つかれた…',{size:30,c:'#5b4d45'})}},
  draw(c,api){const st=this.st;c.fillStyle='#e4f1ea';c.fillRect(0,api.top,W,api.bottom-api.top);for(let i=0;i<4;i++)D.ellipse(c,(i*150+st.t*8)%(W+120)-60,120+i*130,46,15,'#fff',0);
    c.fillStyle='#a67c52';c.fillRect(TX-36,api.top,72,api.bottom-api.top);c.strokeStyle=OL;c.lineWidth=3;c.strokeRect(TX-36,api.top-5,72,api.bottom-api.top+10);c.fillStyle='#8a6a48';for(let y=api.top+((st.anim*SEG)%SEG);y<api.bottom;y+=SEG)c.fillRect(TX-20,y,40,6);
    for(let i=0;i<10;i++){const b=st.br[i];if(!b)continue;const y=560-i*SEG+st.anim*SEG;D.rrect(c,b<0?TX-130:TX+30,y-10,100,20,8,'#a67c52');D.circle(c,b<0?TX-135:TX+135,y,26,'#9cc86a')}
    const kx=TX+st.side*70;this.koala(c,kx,560+(st.dead?20:0),28,-st.side);
    D.rrect(c,70,150,W-140,16,8,'#fff',3);D.rrect(c,72,152,(W-144)*Math.max(0,st.gauge),12,6,st.gauge<.3?'#e2645a':'#9cc86a',0);
    if(api.state==='play'&&st.n===0)D.text(c,'左右をタップでのぼる！',W/2,260,22,'#5b4d45')},
  __bot(api){const st=this.st;if(st.dead)return;const safe=st.br[1]===0?st.side:-st.br[1];if(st.br[0]===safe)return;this.down(safe<0?50:W-50,500,api)},
};
