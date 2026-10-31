/* だんごスネーク：なめらかに動くスネーク。頭はゆびの方向へ回る。 */
const AL=24,AT=150,AR=W-24,AB=H-30,SEG=19,COLS=['#f2a5b5','#fbf7f0','#9cc86a'];
const GAME={...META,sprites:['icon','dango'],unit:'こ',hudUnit:true,fullBleed:true,comboHud:false,
  bgm:{bpm:132,root:60,scale:'major',prog:[1,5,4,5],seed:91,lead:'square',drums:'four',density:.6},
  ranks:[[0,'ひとくち'],[10,'くしだんご'],[25,'だんご三兄弟の兄'],[45,'だんご列車'],[70,'だんご大行列'],[100,'だんごの竜']],
  shareText:(v,f)=>`だんごスネークで ${f}こ つなげた！`,
  icon(c,x,y,s){c.lineWidth=s*.04;c.strokeStyle='#c99a6a';c.beginPath();c.moveTo(x-s*.42,y+s*.3);c.lineTo(x+s*.4,y-s*.32);c.stroke();for(let i=0;i<3;i++)this.dango(c,x-s*.25+i*s*.22,y+s*.17-i*s*.17,s*.13,COLS[i],i===2)},
  dango(c,x,y,r,col,face){D.circle(c,x,y,r,col);if(face)D.face(c,x,y+r*.05,r*1.1)},
  reset(api){const st=this.st={hx:W/2,hy:H/2+60,a:-Math.PI/2,ta:-Math.PI/2,trail:[],len:4,food:[],t:0,fever:0,dead:false,tx:null};
    for(let i=0;i<120;i++)st.trail.push([st.hx,st.hy+i*3]);for(let i=0;i<5;i++)this.addFood();api.score=0},
  addFood(gold){const st=this.st;for(let t=0;t<40;t++){const x=rnd(AL+20,AR-20),y=rnd(AT+20,AB-20);if(dist(x,y,st.hx,st.hy)<80)continue;st.food.push({x,y,c:gold?'gold':rndi(0,2),t:0});return}},
  down(x,y){this.st.tx=[x,y]},move(x,y){if(this.st.tx)this.st.tx=[x,y]},up(){this.st.tx=null},
  key(k){const m={ArrowLeft:Math.PI,ArrowRight:0,ArrowUp:-Math.PI/2,ArrowDown:Math.PI/2}[k];if(m!==undefined){this.st.ta=m;this.st.tx=null}},
  segPos(i){const st=this.st,idx=Math.min(st.trail.length-1,Math.round(i*SEG/3));return st.trail[idx]},
  update(dt,api){const st=this.st;st.t+=dt;if(st.fever>0){st.fever-=dt;if(st.fever<=0){api.fever=false;api.bgmRate=1}}
    if(st.tx)st.ta=Math.atan2(st.tx[1]-st.hy,st.tx[0]-st.hx);
    let d=((st.ta-st.a+Math.PI*3)%(Math.PI*2))-Math.PI;st.a+=clamp(d,-6*dt,6*dt);
    const sp=(150+Math.min(st.len,80)*1.4)*(st.fever>0?1.35:1);
    const steps=Math.ceil(sp*dt/3);for(let s=0;s<steps;s++){st.hx+=Math.cos(st.a)*sp*dt/steps;st.hy+=Math.sin(st.a)*sp*dt/steps;st.trail.unshift([st.hx,st.hy])}
    const need=Math.round((st.len+2)*SEG/3)+4;if(st.trail.length>need)st.trail.length=need;
    // ぶつかり判定
    if(st.hx<AL+12||st.hx>AR-12||st.hy<AT+12||st.hy>AB-12){this.die(api);return}
    for(let i=4;i<st.len;i++){const p=this.segPos(i);if(p&&dist(p[0],p[1],st.hx,st.hy)<17){this.die(api);return}}
    for(let i=st.food.length-1;i>=0;i--){const f=st.food[i];f.t+=dt;if(dist(f.x,f.y,st.hx,st.hy)<26){st.food.splice(i,1);
        const n=st.fever>0?2:1;st.len+=1;api.add(n);api.combo++;S.pop(1+Math.min(api.combo,20)*.03);api.burst(f.x,f.y,{c:f.c==='gold'?['#f4d66d','#fff']:[COLS[f.c],'#fff'],n:10,sp:160});
        if(f.c==='gold'){st.fever=6;api.fever=true;api.bgmRate=1.2;S.perfect();api.flash('#fff6c8',.4);api.float(W/2,240,'フィーバー！×2',{size:34,c:'#f3c84b'})}else api.float(f.x,f.y-20,'+'+n,{size:20});
        this.addFood(Math.random()<.08&&st.fever<=0);if(st.food.length<4+Math.floor(st.len/15))this.addFood()}}},
  die(api){const st=this.st;st.dead=true;S.boom();api.shake(12);api.flash('#fff',.5);for(let i=0;i<st.len;i+=2){const p=this.segPos(i);if(p)api.burst(p[0],p[1],{c:COLS,n:4,sp:200})}api.end()},
  overText:'ゴツン！',
  draw(c,api){const st=this.st;c.fillStyle='#d6e3c0';c.fillRect(0,api.top,W,api.bottom-api.top);D.rrect(c,AL,AT,AR-AL,AB-AT,18,'#e8efd9',5);
    c.fillStyle='#dfe8cc';for(let x=AL+30;x<AR;x+=60)for(let y=AT+30;y<AB;y+=60)c.fillRect(x-1,y-1,3,3);
    for(const f of st.food){const b=1+Math.sin(f.t*6)*.08;if(f.c==='gold'){D.star(c,f.x,f.y,15*b,'#f4d66d',3)}else this.dango(c,f.x,f.y,11*b,COLS[f.c],false)}
    // くし（からだの芯）
    c.lineWidth=5;c.strokeStyle='#c99a6a';c.lineCap='round';c.beginPath();for(let i=0;i<st.len;i++){const p=this.segPos(i);if(!p)break;i?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1])}c.stroke();
    D.group(c,()=>{for(let i=st.len-1;i>=0;i--){const p=this.segPos(i);if(!p)continue;const r=i===0?20:15;D.circle(c,p[0],p[1],r,st.fever>0&&i>0?`hsl(${(st.t*300+i*25)%360},70%,80%)`:COLS[i%3])}});
    const h=this.segPos(0);c.save();c.translate(h[0],h[1]);c.rotate(st.a+Math.PI/2);D.face(c,0,-2,24,st.dead?'hurt':'smile');c.restore()},
  __bot(api){const st=this.st;let f=null,bd=1e9;for(const o of st.food){const d=dist(o.x,o.y,st.hx,st.hy);if(d<bd){bd=d;f=o}}
    let ta=f?Math.atan2(f.y-st.hy,f.x-st.hx):st.a;const look=(a)=>{const x=st.hx+Math.cos(a)*50,y=st.hy+Math.sin(a)*50;return x>AL+20&&x<AR-20&&y>AT+20&&y<AB-20};
    if(!look(ta))for(let k=1;k<8;k++){if(look(st.a+k*.4)){ta=st.a+k*.4;break}if(look(st.a-k*.4)){ta=st.a-k*.4;break}}st.ta=ta;st.tx=null},
};
