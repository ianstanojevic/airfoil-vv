(function(){
"use strict";
/* Marks wear classes from CSS tokens — never resolved literals — so a theme
   switch after load repaints the charts along with everything else. */

var LOAD=[["7-15",32,41],["7-16",28,40],["7-17",24,40],["7-18",41,42],["7-19",35,41],["7-20",30,40],
["7-21",34,41],["7-22",29,40],["7-23",25,40],["7-24",21,40],["7-25",18,40],["7-26",16,40],
["7-27",25,41],["7-28",24,40],["7-29",34,42],["7-30",29,41],["7-31",53,44],["8-1",45,43],
["8-2",43,43],["8-3",45,43],["8-4",38,42],["8-5",48,44],["8-6",41,43],["8-7",35,42],
["8-8",30,41],["8-9",26,40],["8-10",22,40],["8-11",19,40]];

var ZONES=[
 ["Återhämtning","6:30–7:07","Konversationstempo. Ska kännas nästan för lätt.",0],
 ["Lugn distans","6:00–6:30","Grundpasset. Här ligger nästan hela 2.10.",1],
 ["Långpass / tävlingsfart","5:29–5:51","Snabbare än 2.10:s måltid 6:10.",0],
 ["Tröskel","4:56–5:14","Cirka 60 min maxtempo.",0],
 ["Intervall (VO2)","4:28–4:47","Kör programmets intervaller här.",0],
 ["Koordination / kort","4:04–4:22","60–300 m, avspänd snabbhet.",0]];

var WEEK0=[
 {wd:"tis",dn:11,k:"easy",today:1,ti:"Lugn distans",km:"3 km",
  m:"6:30–7:00/km. Kortare och lugnare än du tror behövs.",
  w:"Sex dagars uppehåll — första passet tillbaka ska vara nästan pinsamt lätt."},
 {wd:"ons",dn:12,k:"rest",ti:"Vila",km:"",m:"",w:""},
 {wd:"tors",dn:13,k:"easy",ti:"Lugn distans",km:"4 km",m:"6:15–6:45/km.",w:""},
 {wd:"fre",dn:14,k:"rest",ti:"Vila",km:"",m:"",w:""},
 {wd:"lör",dn:15,k:"easy",ti:"Lugn distans",km:"5 km",m:"6:15–6:45/km.",w:""},
 {wd:"sön",dn:16,k:"rest",ti:"Vila",km:"",m:"Programmet börjar i morgon.",w:""}];

var WEEK1=[
 {wd:"mån",dn:17,k:"rest",ti:"Vila",km:"",m:"",w:""},
 {wd:"tis",dn:18,k:"easy",ti:"Lugn distans",km:"4 km",
  m:"6:15–6:45/km + stretching 5–10 min.",
  w:"Programmet: 4 km med gånginslag. Spring hela."},
 {wd:"ons",dn:19,k:"rest",ti:"Vila",km:"",m:"",w:""},
 {wd:"tors",dn:20,k:"easy",ti:"Lugn distans",km:"4 km",m:"6:15–6:45/km + stretching.",w:""},
 {wd:"fre",dn:21,k:"rest",ti:"Vila",km:"",m:"",w:""},
 {wd:"lör",dn:22,k:"key",ti:"Långpass",km:"5 km",
  m:"6:15–6:45/km + stretching 10 min.",
  w:"Veckans enda pass som måste bli av. Halva ditt rekord — det ska kännas lätt."},
 {wd:"sön",dn:23,k:"rest",ti:"Vila",km:"",m:"",w:""}];

function el(t,c,x){var e=document.createElementNS("http://www.w3.org/2000/svg",t);
  if(c)e.setAttribute("class",c); if(x)for(var k in x)e.setAttribute(k,x[k]); return e;}
function txt(x,y,s,c,anc,sz){var t=el("text",c||"axis",{x:x,y:y});
  if(anc)t.setAttribute("text-anchor",anc); if(sz)t.setAttribute("font-size",sz);
  t.textContent=s; return t;}
function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(m){
  return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m];});}
function J(id){try{return JSON.parse(document.getElementById(id).textContent);}catch(e){return null;}}

var CMP=J("cmp-data")||{cmp5:[],curves:{}};
var P210=J("plan-data")||[];

/* ---------- comparison: 2.10 vs 1.40 vs your level ---------- */
(function(){
var svg=document.getElementById("c-cmp"); if(!svg||!CMP.curves["210"])return;
var W=420,H=168,L=26,R=8,T=12,B=30, iw=W-L-R, ih=H-T-B, n=20, max=65;
function X(i){return L+i*(iw/(n-1));}
function Y(v){return T+ih-v/max*ih;}
[0,20,40,60].forEach(function(g){
  svg.appendChild(el("line","gridline",{x1:L,x2:W-R,y1:Y(g),y2:Y(g)}));
  svg.appendChild(txt(L-5,Y(g)+3,g,"axis","end"));});
/* your current range: mean 7.4, best week 25.4 */
svg.appendChild(el("rect","band-crit",{x:L,y:Y(25.4),width:iw,height:Y(7.4)-Y(25.4)}));
svg.appendChild(el("line","ref-crit",{x1:L,x2:W-R,y1:Y(7.4),y2:Y(7.4)}));
function line(arr,cls){svg.appendChild(el("path",cls,{d:arr.map(function(v,i){
  return (i?"L":"M")+X(i).toFixed(1)+" "+Y(v).toFixed(1);}).join(" ")}));}
line(CMP.curves["140"],"ln-ref");
line(CMP.curves["210"],"ln ln-data");
svg.appendChild(el("circle","dot-data cap",{cx:X(19),cy:Y(CMP.curves["210"][19]),r:4}));
svg.appendChild(txt(L+3,Y(25.4)-4,"din bästa vecka 25,4","axis halo lbl-crit","start"));
svg.appendChild(txt(L+3,Y(7.4)+11,"ditt snitt 7,4","axis halo lbl-crit","start"));
svg.appendChild(txt(X(11),Y(CMP.curves["140"][11])-7,"1.40","axis halo","middle",10));
svg.appendChild(txt(X(11),Y(CMP.curves["210"][11])+13,"2.10","axis halo lbl-data","middle",10));
[0,4,9,14,19].forEach(function(i){
  svg.appendChild(txt(X(i),H-14,"v"+(i+1),"axis",i===0?"start":(i===19?"end":"middle")));});
svg.appendChild(txt(L+iw/2,H-2,"veckovolym, km","axis","middle"));
})();

/* ---------- 2.10 long run ---------- */
(function(){
var svg=document.getElementById("c-long"); if(!svg||!CMP.curves.long210)return;
var A=CMP.curves.long210, W=420,H=140,L=26,R=8,T=12,B=28, iw=W-L-R, ih=H-T-B, n=A.length, max=24;
function X(i){return L+i*(iw/(n-1));}
function Y(v){return T+ih-v/max*ih;}
[0,5,10,15,20].forEach(function(g){
  svg.appendChild(el("line","gridline",{x1:L,x2:W-R,y1:Y(g),y2:Y(g)}));
  svg.appendChild(txt(L-5,Y(g)+3,g,"axis","end"));});
var pts=A.map(function(v,i){return [X(i),Y(v)];});
svg.appendChild(el("path","area-agent",{d:"M"+pts[0][0]+" "+Y(0)+" "+
  pts.map(function(p){return "L"+p[0].toFixed(1)+" "+p[1].toFixed(1);}).join(" ")+
  " L"+pts[n-1][0]+" "+Y(0)+" Z"}));
svg.appendChild(el("path","ln ln-agent",{d:pts.map(function(p,i){
  return (i?"L":"M")+p[0].toFixed(1)+" "+p[1].toFixed(1);}).join(" ")}));
svg.appendChild(el("line","ref-crit",{x1:L,x2:W-R,y1:Y(10.8),y2:Y(10.8)}));
svg.appendChild(txt(W-R,Y(10.8)+11,"rekord i dag 10,8","axis halo lbl-crit","end"));
var rec=-1, peak=0, pi=0;
A.forEach(function(v,i){if(rec<0&&v>10.8)rec=i; if(i<n-1&&v>peak){peak=v;pi=i;}});
[rec,pi,n-1].forEach(function(i){if(i>=0)
  svg.appendChild(el("circle","dot-agent cap",{cx:pts[i][0],cy:pts[i][1],r:4}));});
if(rec>=0)svg.appendChild(txt(X(rec),Y(A[rec])-8,"v"+(rec+1)+" · rekord","axis halo lbl-agent","middle",9));
svg.appendChild(txt(X(pi),Y(peak)-8,peak+" km","axis halo lbl-agent","middle",9.5));
svg.appendChild(txt(X(n-1),Y(A[n-1])+13,"21,1","axis halo lbl-agent","end",9.5));
[0,4,9,14,19].forEach(function(i){
  svg.appendChild(txt(X(i),H-14,"v"+(i+1),"axis",i===0?"start":(i===19?"end":"middle")));});
svg.appendChild(txt(L+iw/2,H-2,"långpassets längd, km","axis","middle"));
var t=document.getElementById("longtext");
if(t)t.innerHTML="Långpasset går 5 → "+peak+" km och passerar ditt nuvarande rekord på 10,8 km "+
  "<strong>i vecka "+(rec+1)+"</strong>. Sista steget är måldagen: 21,1 km.";
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
[0,9,17,27].forEach(function(i){
  svg.appendChild(txt(X(i),H-6,LOAD[i][0].replace("-","/"),"axis",i===0?"start":(i===27?"end":"middle")));});
var lastL=LOAD[LOAD.length-1];
svg.appendChild(txt(X(27)-7,Y(lastL[1])+4,lastL[1],"axis halo lbl-data","end",10.5));
svg.appendChild(txt(X(27)-7,Y(lastL[2])-7,lastL[2],"axis halo lbl-agent","end",10.5));
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
days("week0",WEEK0); days("week1",WEEK1);

/* ---------- zones + comparison table ---------- */
(function(){
var z=document.getElementById("zones");
if(z)z.innerHTML=ZONES.map(function(r){
  return '<div class="zone'+(r[3]?" z-race":"")+'"><span class="zone-n">'+esc(r[0])+
    '</span><span class="zone-p">'+esc(r[1])+' /km</span>'+
    '<span class="zone-d">'+esc(r[2])+'</span></div>';}).join("");
var t=document.getElementById("cmptbl");
if(t)t.innerHTML=CMP.cmp5.map(function(r){
  return '<tr'+(r[0]==="2.10"?' class="hi"':'')+'><td class="em">'+esc(r[0])+
    '</td><td>'+esc(r[1])+'</td><td>'+r[3]+'</td><td>'+r[5]+'</td><td>'+r[6]+
    '</td><td>'+r[2]+'</td></tr>';}).join("");
})();

/* ---------- full 2.10 plan ---------- */
(function(){
var host=document.getElementById("plan210"); if(!host||!P210.length)return;
host.style.display="flex"; host.style.flexDirection="column"; host.style.gap="14px";
host.innerHTML=P210.map(function(w){
  return '<div class="wk"><div class="wk-h"><span class="wk-t">Vecka '+w[0]+' · '+esc(w[1])+
    '</span><span class="wk-n">'+w[2]+' km · '+w[3]+' pass</span></div><div class="wk-d">'+
    w[5].map(function(d){
      var rest=d[2]==="Vila";
      return '<div class="wk-r'+(rest?" rest":"")+'"><span class="a">'+esc(d[0])+
        '</span><span class="b">'+esc(d[1])+'</span><span class="c">'+esc(d[2])+'</span></div>';
    }).join("")+'</div></div>';}).join("");
})();

/* ---------- countdown ---------- */
(function(){
var n=document.getElementById("cd-n"); if(!n)return;
var s=new Date(2026,7,17), now=new Date();
var d=Math.round((s-new Date(now.getFullYear(),now.getMonth(),now.getDate()))/864e5);
if(!(d>0)){n.textContent="1"; n.parentNode.querySelector("span").innerHTML="vecka<br>igång"; return;}
n.textContent=d;
})();
})();
