// アクセス数を数える（GoatCounter。Cookie なし・個人を特定しない）。
// どのページが見られたかと、どこから来たか（X・検索など）だけを送る。
(function(){
// 自分の端末を数えないとき: #nocount をつけて 1 回開く（#count で元に戻す）。ブラウザごとに保存。
var h=location.hash;try{if(h=="#nocount"){localStorage.setItem("skipgc","t");alert("このブラウザからのアクセスは数えないようにしました。")}else if(h=="#count"){localStorage.removeItem("skipgc");alert("このブラウザからのアクセスを数えるようにしました。")}if(localStorage.getItem("skipgc")=="t")return}catch(_){}
if(location.hostname!="picoruno.com"||navigator.webdriver)return;
function go(){var P=new URLSearchParams(location.search);["ref","utm_source","utm_medium","utm_campaign"].forEach(function(k){P.delete(k)});var s=P.toString();
var q={p:location.pathname+(s?"?"+s:""),t:document.title,r:document.referrer,q:location.search,s:[screen.width,screen.height,devicePixelRatio||1].join(","),rnd:Math.random().toString(36).slice(2)};
new Image().src="https://picoruno.goatcounter.com/count?"+Object.keys(q).map(function(k){return k+"="+encodeURIComponent(q[k])}).join("&")}
if(document.visibilityState=="prerender")document.addEventListener("visibilitychange",function v(){if(document.visibilityState!="prerender"){document.removeEventListener("visibilitychange",v);go()}});else go();
})();
