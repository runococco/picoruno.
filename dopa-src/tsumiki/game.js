/* つみきタワー：横移動ブロックをタップで積む。重なり部分だけ残る。 */
const BH=34,BASEY=640;
const COLS=['#e2645a','#f2c84b','#7fb2e0','#9cc86a','#f2a5c0','#c49ae0','#f2a24a'];
const GAME={...META,sprites:['icon'],unit:'階',hudUnit:true,fullBleed:true,
  bgm:{bpm:112,root:60,scale:'major',prog:[1,5,6,4],seed:44,lead:'square',drums:'light',density:.5},
  ranks:[[0,'ぐらぐら'],[5,'つみき見習い'],[12,'なかなかの建築家'],[20,'タワーの達人'],[30,'雲の上の建築家'],[45,'伝説のつみき']],
  shareText:(v,f)=>`つみきタワーで ${f}階 つめた！`,
  icon(c,x,y,s){const w=[.9,.7,.8,.5];for(let i=0;i<4;i++)D.rrect(c,x-s*w[i]/2+(i%2?s*.05:-s*.03),y+s*.35-i*s*.2,s*w[i],s*.2,4,COLS[i])},
  reset(api){this.st={blocks:[{x:W/2-80,w:160,c:COLS[0]}],cur:null,n:0,drop:null,fall:[],t:0,dead:false,endT:0,scroll:0};api.score=0;this.spawn()},
  spawn(){const st=this.st;const top=st.blocks[st.blocks.length-1];const spd=160+Math.min(st.n,30)*9;const fromL=st.n%2===0;st.cur={x:fromL?-top.w:W,w:top.w,c:COLS[(st.n+1)%COLS.length],v:fromL?spd:-spd,y:BASEY-(st.blocks.length)*BH}},
  down(x,y,api){const st=this.st;const b=st.cur;if(!b||st.dead)return;const top=st.blocks[st.blocks.length-1];const l=Math.max(b.x,top.x),r=Math.min(b.x+b.w,top.x+top.w);const ov=r-l;
    if(ov<=4){st.dead=true;st.fall.push({x:b.x,w:b.w,y:b.y,c:b.c,vy:0,rot:0});st.cur=null;S.bad();api.shake(8);api.float(W/2,250,'おちた…',{size:30,c:'#5b4d45'});api.combo=0;return}
    const d=Math.abs(b.x-top.x);let nx=l,nw=ov;if(d<7){nx=top.x;nw=Math.min(top.w+12,160);api.combo++;S.perfect();api.flash('#fff',.2);api.float(W/2,b.y-40,'ぴったり！',{size:26,c:'#7fb2e0'});api.burst(W/2,b.y,{c:['#fff','#f2c84b'],n:10,sp:160,shape:'s'});if(nw>top.w)api.float(W/2,b.y-70,'太くなった！',{size:18,c:'#5b4d45'})}
    else{api.combo=0;S.thud();if(b.x<top.x)st.fall.push({x:b.x,w:top.x-b.x,y:b.y,c:b.c,vy:0,rot:-1});else st.fall.push({x:top.x+top.w,w:b.x+b.w-top.x-top.w,y:b.y,c:b.c,vy:0,rot:1})}
    st.blocks.push({x:nx,w:nw,c:b.c});st.n++;api.score=st.n;if(st.n%10===0){S.fanfare();api.float(W/2,200,st.n+'階！',{size:34,c:'#7fb2e0'})}this.spawn()},
  update(dt,api){const st=this.st;st.t+=dt;if(st.dead){st.endT+=dt;if(st.endT>1.2)api.end()}
    const b=st.cur;if(b){b.x+=b.v*dt;if(b.x<-b.w-10||b.x>W+10)b.v*=-1;if(b.x<-b.w-10)b.x=-b.w-10;if(b.x>W+10)b.x=W+10}
    for(const f of st.fall){f.vy+=1400*dt;f.y+=f.vy*dt;f.rot+=f.rot*2*dt}st.fall=st.fall.filter(f=>f.y<api.bottom+200);
    const target=Math.max(0,(st.blocks.length-6)*BH);st.scroll+=(target-st.scroll)*6*dt},
  draw(c,api){const st=this.st;c.fillStyle='#e4eef6';c.fillRect(0,api.top,W,api.bottom-api.top);for(let i=0;i<4;i++)D.ellipse(c,(i*150+st.t*8+st.scroll*.2)%(W+120)-60,130+i*90-((st.scroll*.3)%400),46,15,'#fff',0);
    c.save();c.translate(0,st.scroll);c.fillStyle='#c9d7e2';c.fillRect(0,BASEY+BH,W,api.bottom+400);c.fillStyle='#b7c7d4';c.fillRect(0,BASEY+BH,W,8);
    st.blocks.forEach((b,i)=>D.rrect(c,b.x,BASEY-i*BH,b.w,BH,6,b.c));
    for(const f of st.fall){c.save();c.translate(f.x+f.w/2,f.y+BH/2);c.rotate(f.rot*.5);D.rrect(c,-f.w/2,-BH/2,f.w,BH,6,f.c);c.restore()}
    const b=st.cur;if(b)D.rrect(c,b.x,b.y,b.w,BH,6,b.c);c.restore();
    if(api.state==='play'&&st.n===0)D.text(c,'タップでぽとん！',W/2,300,22,'#5b4d45')},
  __bot(api){const st=this.st;const b=st.cur;if(!b||st.dead)return;const top=st.blocks[st.blocks.length-1];if(Math.abs(b.x+b.v*.02-top.x)<Math.max(6,b.w*.12))this.down(0,0,api)},
};
