const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:800,height:420}});
await p.goto('file://'+require('path').resolve(__dirname,'../../amashoppa.html'));await p.waitForTimeout(500);
await p.evaluate(()=>{const c=document.createElement('canvas');c.width=800;c.height=420;c.style.cssText='position:fixed;left:0;top:0;z-index:99;background:#fbefe6';document.body.appendChild(c);const x=c.getContext('2d');
for(let i=0;i<16;i++){__G.food(x,i,60+(i%8)*95,100+Math.floor(i/8)*200,80);D.text(x,i,60+(i%8)*95,180+Math.floor(i/8)*200,14)}});
await p.screenshot({path:'/tmp/claude-0/shots/foods.png'});await b.close()})();
