(function(){
"use strict";
/* Marks wear classes from CSS tokens — never resolved literals — so a theme
   switch after load repaints the charts along with everything else. */

var LOAD=[["7-15",32,41],["7-16",28,40],["7-17",24,40],["7-18",41,42],["7-19",35,41],["7-20",30,40],
["7-21",34,41],["7-22",29,40],["7-23",25,40],["7-24",21,40],["7-25",18,40],["7-26",16,40],
["7-27",25,41],["7-28",24,40],["7-29",34,42],["7-30",29,41],["7-31",53,44],["8-1",45,43],
["8-2",43,43],["8-3",45,43],["8-4",38,42],["8-5",48,44],["8-6",41,43],["8-7",35,42],
["8-8",30,41],["8-9",26,40],["8-10",22,40],["8-11",19,40],["8-12",16,40]];

var ZONES=[
 ["Återhämtning","6:30–7:07","Konversationstempo. Ska kännas nästan för lätt.",0],
 ["Lugn distans","6:00–6:30","Grundpasset. Här ligger nästan hela programmet.",1],
 ["Snabbdistans","5:29–5:51","Stegrad fart och snabbdistans.",0],
 ["Tröskel","4:56–5:14","Tröskelpassen från vecka 15.",0],
 ["Intervall (VO2)","4:28–4:47","Långa intervaller, 500 m och uppåt.",0],
 ["Koordination / kort","4:04–4:22","60–300 m, avspänd snabbhet.",0]];

var PHASES=[
 [1,4,"Grundvänjning","13 → 19 km","Tre pass i veckan. Styrka från vecka 2, koordinationslopp från vecka 4. Långpasset går 5 → 7,5 km."],
 [5,8,"Löpning i sträck","17 → 26 km","Gånginslagen försvinner. Första intervallerna, fartlek och snabbdistans. Långpasset når 9 km."],
 [9,14,"Långpass och styrka","22 → 34 km","Långpasset blir ett eget pass. Backlöpning och löpskolning in. Volymtoppen nås i vecka 13."],
 [15,18,"Tröskel och distans","26 → 34 km","Tröskelpass från vecka 15, långpass med fartökning från 17. Längsta passet, 18 km, ligger i vecka 18."],
 [19,20,"Nedtrappning","22 → måldag","Volymen ned, skärpan kvar. Lördag 26 december: 21,1 km."]];

var WEEK1=[
 {wd:"mån",dn:10,k:"rest",ti:"Vila",km:"",m:"",w:""},
 {wd:"tis",dn:11,k:"past",ti:"Lugn distans",km:"4 km",
  m:"Passerat — låg före beslutet att börja.",w:""},
 {wd:"ons",dn:12,k:"rest",today:1,ti:"Vila",km:"",m:"Idag. Ha klockan på dig i natt.",w:""},
 {wd:"tors",dn:13,k:"next",ti:"Lugn distans · första passet",km:"4 km",
  m:"6:15–6:45/km, cirka 26 min + stretching 5–10 min.",
  w:"Programmet anger gånginslag för nybörjare — spring hela, behåll distansen."},
 {wd:"fre",dn:14,k:"rest",ti:"Vila",km:"",m:"",w:""},
 {wd:"lör",dn:15,k:"key",ti:"Långpass",km:"5 km",
  m:"6:15–6:45/km + stretching 10 min.",
  w:"Veckans pass som måste bli av. Knappt halva ditt rekord — det ska kännas lätt."},
 {wd:"sön",dn:16,k:"rest",ti:"Vila",km:"",m:"Vecka 2 börjar i morgon.",w:""}];

function el(t,c,x){var e=document.createElementNS("http://www.w3.org/2000/svg",t);
  if(c)e.setAttribute("class",c); if(x)for(var k in x)e.setAttribute(k,x[k]); return e;}
function txt(x,y,s,c,anc,sz){var t=el("text",c||"axis",{x:x,y:y});
  if(anc)t.setAttribute("text-anchor",anc); if(sz)t.setAttribute("font-size",sz);
  t.textContent=s; return t;}
function sv(n){return String(n).replace(".",",");}
function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(m){
  return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m];});}
function J(id){var n=document.getElementById(id);
  try{return JSON.parse(n.textContent);}catch(e){return null;}}

var P=J("plan-data")||[];                    // [w, label, km, sess, long, days[]]
var KM=P.map(function(r){return r[2];});
var LG=P.map(function(r){return r[4];});
function phaseOf(w){for(var i=0;i<PHASES.length;i++) if(w>=PHASES[i][0]&&w<=PHASES[i][1]) return PHASES[i][2]; return "";}
function isLight(i){return i>0 && KM[i]<KM[i-1];}

/* ---------- weekly volume ---------- */
(function(){
var svg=document.getElementById("c-vol"); if(!svg||!KM.length)return;
var W=420,H=158,L=26,R=8,T=12,B=32, iw=W-L-R, ih=H-T-B, n=KM.length, max=40;
var band=iw/n, bw=band*0.64;
function Y(v){return T+ih-v/max*ih;}
function Xc(i){return L+i*band+band/2;}
[0,10,20,30,40].forEach(function(g){
  svg.appendChild(el("line","gridline",{x1:L,x2:W-R,y1:Y(g),y2:Y(g)}));
  svg.appendChild(txt(L-5,Y(g)+3,g,"axis","end"));});
/* phase dividers */
PHASES.slice(1).forEach(function(p){
  var x=L+(p[0]-1)*band;
  svg.appendChild(el("line","divider",{x1:x,x2:x,y1:T,y2:T+ih}));});
KM.forEach(function(v,i){
  svg.appendChild(el("rect",isLight(i)?"bar-soft":"bar-data",
    {x:(Xc(i)-bw/2).toFixed(1),y:Y(v).toFixed(1),width:bw.toFixed(1),
     height:Math.max(2,ih-(Y(v)-T)).toFixed(1),rx:2}));});
svg.appendChild(el("line","zeroline",{x1:L,x2:W-R,y1:Y(0),y2:Y(0)}));
var pk=KM.indexOf(Math.max.apply(null,KM.slice(0,19)));
svg.appendChild(txt(Xc(pk),Y(KM[pk])-6,sv(KM[pk])+" km","axis halo lbl-data","middle",9.5));
svg.appendChild(txt(Xc(0),Y(KM[0])-6,sv(KM[0]),"axis halo lbl-data","middle",9.5));
[0,4,9,14,19].forEach(function(i){
  svg.appendChild(txt(Xc(i),H-14,"v"+(i+1),"axis","middle"));});
svg.appendChild(txt(L+iw/2,H-2,"veckovolym, km · streck = fasgräns","axis","middle"));
})();

/* ---------- long run ---------- */
(function(){
var svg=document.getElementById("c-long"); if(!svg||!LG.length)return;
var W=420,H=140,L=26,R=8,T=12,B=28, iw=W-L-R, ih=H-T-B, n=LG.length, max=24;
function X(i){return L+i*(iw/(n-1));}
function Y(v){return T+ih-v/max*ih;}
[0,5,10,15,20].forEach(function(g){
  svg.appendChild(el("line","gridline",{x1:L,x2:W-R,y1:Y(g),y2:Y(g)}));
  svg.appendChild(txt(L-5,Y(g)+3,g,"axis","end"));});
var pts=LG.map(function(v,i){return [X(i),Y(v)];});
svg.appendChild(el("path","area-agent",{d:"M"+pts[0][0]+" "+Y(0)+" "+
  pts.map(function(p){return "L"+p[0].toFixed(1)+" "+p[1].toFixed(1);}).join(" ")+
  " L"+pts[n-1][0]+" "+Y(0)+" Z"}));
svg.appendChild(el("path","ln ln-agent",{d:pts.map(function(p,i){
  return (i?"L":"M")+p[0].toFixed(1)+" "+p[1].toFixed(1);}).join(" ")}));
svg.appendChild(el("line","ref-crit",{x1:L,x2:W-R,y1:Y(10.8),y2:Y(10.8)}));
svg.appendChild(txt(W-R,Y(10.8)+11,"rekord i dag 10,8","axis halo lbl-crit","end"));
var rec=-1,peak=0,pi=0;
LG.forEach(function(v,i){if(rec<0&&v>10.8)rec=i; if(i<n-1&&v>peak){peak=v;pi=i;}});
[rec,pi,n-1].forEach(function(i){if(i>=0)
  svg.appendChild(el("circle","dot-agent cap",{cx:pts[i][0],cy:pts[i][1],r:4}));});
if(rec>=0)svg.appendChild(txt(X(rec),Y(LG[rec])-8,"v"+(rec+1)+" · rekord","axis halo lbl-agent","middle",9));
svg.appendChild(txt(X(pi),Y(peak)-8,sv(peak)+" km","axis halo lbl-agent","middle",9.5));
svg.appendChild(txt(X(n-1),Y(LG[n-1])+13,"21,1","axis halo lbl-agent","end",9.5));
[0,4,9,14,19].forEach(function(i){
  svg.appendChild(txt(X(i),H-14,"v"+(i+1),"axis",i===0?"start":(i===19?"end":"middle")));});
svg.appendChild(txt(L+iw/2,H-2,"långpassets längd, km","axis","middle"));
var step=0;
for(var i=1;i<n-1;i++) step=Math.max(step,LG[i]-LG[i-1]);
var t=document.getElementById("longtext");
if(t)t.innerHTML="Långpasset är passet som avgör halvmaran. Det går "+sv(LG[0])+" → "+sv(peak)+
  " km och passerar ditt nuvarande rekord på 10,8 km <strong>i vecka "+(rec+1)+"</strong>. "+
  "Största enskilda steget är "+sv(Math.round(step*10)/10)+" km — resten växer en kilometer i taget.";
})();

/* ---------- load ---------- */
(function(){
var svg=document.getElementById("c-load"); if(!svg)return;
var W=420,H=130,L=26,R=8,T=10,B=20, iw=W-L-R, ih=H-T-B, max=60;
function X(i){return L+i*(iw/(LOAD.length-1));}
function Y(v){return T+ih-v/max*ih;}
[0,20,40,60].forEach(function(g){
  svg.appendChild(el("line","gridline",{x1:L,x2:W-R,y1:Y(g),y2:Y(g)}));
  svg.appendChild(txt(L-5,Y(g)+3,g,"axis","end"));});
function path(idx,kind){
  svg.appendChild(el("path","ln ln-"+kind,{d:LOAD.map(function(r,i){
    return (i?"L":"M")+X(i).toFixed(1)+" "+Y(r[idx]).toFixed(1);}).join(" ")}));
  var last=LOAD.length-1;
  svg.appendChild(el("circle","dot-"+kind+" cap",{cx:X(last),cy:Y(LOAD[last][idx]),r:4}));}
path(2,"agent"); path(1,"data");
[0,9,17,28].forEach(function(i){
  svg.appendChild(txt(X(i),H-6,LOAD[i][0].replace("-","/"),"axis",i===0?"start":(i===28?"end":"middle")));});
var lastL=LOAD[LOAD.length-1];
svg.appendChild(txt(X(28)-7,Y(lastL[1])+4,lastL[1],"axis halo lbl-data","end",10.5));
svg.appendChild(txt(X(28)-7,Y(lastL[2])-7,lastL[2],"axis halo lbl-agent","end",10.5));
})();

/* ---------- day lists ---------- */
function days(host,arr){
  var h=document.getElementById(host); if(!h)return;
  h.innerHTML=arr.map(function(d){
    return '<div class="day d-'+d.k+(d.today?" d-today":"")+'">'+
      '<div class="day-d"><span class="wd">'+esc(d.wd)+'</span><span class="dn">'+d.dn+'</span></div>'+
      '<div class="day-c"><div class="day-top"><span class="day-t">'+esc(d.ti)+'</span>'+
      (d.km?'<span class="day-km">'+esc(d.km)+'</span>':'')+'</div>'+
      (d.m?'<span class="day-m">'+esc(d.m)+'</span>':'')+
      (d.w?'<span class="day-why">'+esc(d.w)+'</span>':'')+'</div></div>';}).join("");}
days("week1",WEEK1);

/* ---------- phases + zones ---------- */
(function(){
var f=document.getElementById("phases");
if(f)f.innerHTML=PHASES.map(function(p){
  return '<div class="phase"><div class="phase-h"><span class="phase-n">Vecka '+p[0]+
    (p[1]>p[0]?"–"+p[1]:"")+'</span><span class="phase-t">'+esc(p[2])+
    '</span><span class="phase-k">'+esc(p[3])+'</span></div>'+
    '<span class="phase-d">'+esc(p[4])+'</span></div>';}).join("");
var z=document.getElementById("zones");
if(z)z.innerHTML=ZONES.map(function(r){
  return '<div class="zone'+(r[3]?" z-race":"")+'"><span class="zone-n">'+esc(r[0])+
    '</span><span class="zone-p">'+esc(r[1])+' /km</span>'+
    '<span class="zone-d">'+esc(r[2])+'</span></div>';}).join("");
})();

/* ---------- full program ---------- */
(function(){
var host=document.getElementById("plan210"); if(!host||!P.length)return;
var html="", cur=null;
P.forEach(function(w,i){
  var ph=phaseOf(w[0]);
  if(ph!==cur){cur=ph; html+='<div class="phase-bar">'+esc(ph)+'</div>';}
  html+='<div class="wk'+(isLight(i)?" wk-light":"")+'">'+
    '<div class="wk-h"><span class="wk-t">Vecka '+w[0]+' · '+esc(w[1])+'</span>'+
    '<span class="wk-n">'+w[2]+' km · '+w[3]+' pass</span></div><div class="wk-d">'+
    w[5].map(function(d){
      var rest=d[2]==="Vila";
      return '<div class="wk-r'+(rest?" rest":"")+'"><span class="a">'+esc(d[0])+
        '</span><span class="b">'+esc(d[1])+'</span><span class="c">'+esc(d[2])+'</span></div>';
    }).join("")+'</div></div>';});
host.innerHTML=html;
})();

/* ---------- countdown to goal day ---------- */
(function(){
var n=document.getElementById("cd-n"); if(!n)return;
var g=new Date(2026,11,26), now=new Date();
var d=Math.round((g-new Date(now.getFullYear(),now.getMonth(),now.getDate()))/864e5);
n.textContent=d>0?d:0;
})();
})();
