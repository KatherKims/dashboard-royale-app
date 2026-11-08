/* Local-only UI. Plans live in memory; every mutation is revalidated by Python. */
(() => {
'use strict';
const $=id=>document.getElementById(id), M=window.FloorMotion, NS='http://www.w3.org/2000/svg';
const money=n=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(n);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const colors=['#e5a0bc','#70d3d2','#ecbd62','#96c67a','#bcaff0','#f08e88','#71b9e9'];
const zoneNames={'Z-B40':'BACK FORTY','Z-BAR':'BAR ROW','Z-ENT':'MAIN ENTRANCE','Z-GAR':'GARAGE ENTRANCE','Z-HL':'HIGH LIMIT','Z-HTL':'HOTEL CORRIDOR','Z-PIT':'CENTER PIT'};
const zoneColors=Object.fromEntries(Object.keys(zoneNames).map((z,i)=>[z,colors[i]]));
let data,plan=[],result,day=1,revision=0,preview=null,previewAction=null,previewSerial=0;
let camera={x:0,y:0,scale:1},drag=null,baselineView=false,playing=null,ambient=true,agents=[],lastTime=0,nextRoute=0;
let dropdown=null,ghostRoutes=[],ghostStart=0,hoverGhost=false,slots=[],slotById={},machineById={};
let reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
const media=matchMedia('(prefers-reduced-motion: reduce)');
media.addEventListener('change',e=>{reduced=e.matches; if(reduced)ambient=false;});
let form={kind:'move',target:'',destination:'',proxy:'',cash:0,day:1,share:.5,retained:.5};
async function api(name,payload){
  const response=await fetch('/api/'+name,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const value=await response.json();if(!response.ok)throw new Error(value.error||'Unable to validate this request.');return value;
}
function toast(message){$('toast').textContent=message;$('toast').style.display='block';clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').style.display='none',6000);}
function node(tag,attrs={},parent){const e=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,v);if(parent)parent.append(e);return e;}
function text(x,y,value,size,fill,parent){const e=node('text',{x,y,fill,'font-size':size,'font-family':'monospace','font-weight':'bold'},parent);e.textContent=value;return e;}
function point(s){return {x:70+(s.x_m-8)*7,y:100+(s.y_m+4.1)*7};}
function slotPoint(id){return slotById[id];}
function currentLayout(){return baselineView?data.initial:result.days[day-1].layout;}
function changedTargets(){return new Set(result.actions.flatMap(a=>a.targets));}
function reservedSlots(){return new Set(result.actions.flatMap(a=>a.destination?[a.destination]:a.kind==='swap'?[data.slots.find(s=>s.machine_id===a.target).location_id,data.slots.find(s=>s.machine_id===a.other).location_id]:[]));}
function vacancies(activation=3){
  const layout=result.days[activation-1].layout,reserved=reservedSlots();
  return slots.filter(s=>!layout[s.location_id]&&!reserved.has(s.location_id)).map(s=>({value:s.location_id,label:s.location_id+' · '+zoneNames[s.zone_id]}));
}
function machineOptions(){const changed=changedTargets();return data.eligible.filter(m=>!changed.has(m)).map(m=>({value:m,label:m+' · '+machineById[m].theme}));}
function applyCamera(){ $('camera').setAttribute('transform',`translate(${camera.x},${camera.y}) scale(${camera.scale})`);$('stage').dataset.zoom=camera.scale.toFixed(4);}
function fit(zone){
  const candidates=zone?slots.filter(s=>s.zone_id===zone):slots;
  const minX=Math.min(...candidates.map(s=>s.x))-45,maxX=Math.max(...candidates.map(s=>s.x))+(zone?45:155);
  const minY=Math.min(...candidates.map(s=>s.y))-55,maxY=Math.max(...candidates.map(s=>s.y))+50;
  const w=innerWidth,h=innerHeight,scale=M.clamp(Math.min((w-80)/(maxX-minX),(h-190)/(maxY-minY)),.35,6);
  camera={scale,x:(w-(maxX+minX)*scale)/2,y:110+(h-200-(maxY-minY)*scale)/2-minY*scale};applyCamera();
}
function architecture(){
  const root=$('architecture');root.replaceChildren();
  node('rect',{x:10,y:20,width:1130,height:990,rx:10,fill:'#0e3432',stroke:'#b28b50','stroke-width':10},root);
  node('rect',{x:24,y:34,width:1102,height:960,fill:'url(#tiles)'},root);
  const groups=Object.keys(zoneNames);
  for(const z of groups){
    const ss=slots.filter(s=>s.zone_id===z);const x=Math.min(...ss.map(s=>s.x))-20,y=Math.min(...ss.map(s=>s.y))-38;
    const w=Math.max(...ss.map(s=>s.x))-x+20,h=Math.max(...ss.map(s=>s.y))-y+22;
    node('rect',{x:x+5,y:y+6,width:w,height:h,fill:'#061a25'},root);
    node('rect',{x,y,width:w,height:h,fill:'url(#carpet)',stroke:zoneColors[z],'stroke-width':4},root);
    node('rect',{x:x+5,y:y+5,width:w-10,height:18,fill:'#152d36',stroke:zoneColors[z]},root);
    text(x+10,y+18,zoneNames[z],9,zoneColors[z],root);
    // Striped threshold is decorative; cabinets retain exact supplied coordinates.
    node('path',{d:`M${x+w/2-16} ${y+h+1}h32`,stroke:zoneColors[z],'stroke-width':5,'stroke-dasharray':'5 3'},root);
  }
  const lounge=node('g',{},root);
  node('rect',{x:1007,y:400,width:108,height:250,fill:'#632948',stroke:'#ecad85','stroke-width':4},lounge);
  text(1018,424,'ACE LOUNGE',10,'#f2c17a',lounge);
  for(let i=0;i<3;i++){
    node('rect',{x:1025,y:450+i*60,width:70,height:17,fill:'#da879e',stroke:'#341b3b','stroke-width':4},lounge);
    node('rect',{x:1040,y:476+i*60,width:40,height:12,fill:'#c0a471',stroke:'#3a2933','stroke-width':3},lounge);
  }
  for(const [x,y] of [[36,50],[1105,50],[36,965],[1105,965]]){
    node('rect',{x:x-7,y:y+8,width:14,height:10,fill:'#ca9c61'},root);
    node('path',{d:`M${x-12} ${y}h24v8h-24zM${x-7} ${y-7}h14v7h-14z`,fill:'#75b478'},root);
  }
  text(430,978,'♠ THE GILDED ACE ♠',18,'#e5bb67',root);
  text(1014,680,'ARTWORK',9,'#a1b5a8',root);text(1014,694,'NOT TO SCALE',9,'#a1b5a8',root);
}
function renderSlots(){
  const root=$('slots'),layout=currentLayout(),changed=changedTargets();root.replaceChildren();
  for(const s of slots){
    const mid=layout[s.location_id],g=node('g',{transform:`translate(${s.x},${s.y})`,class:'slot '+(mid?'':'vacant ')+(changed.has(mid)||mid?.startsWith('NEW-')?'modified':''),tabindex:0,role:'button','aria-label':mid?`${mid}, ${machineById[mid]?.theme||'hypothetical addition'}, ${s.location_id}`:`Vacant ${s.location_id}`, 'data-slot':s.location_id,'data-machine':mid||''},root);
    node('rect',{x:-7,y:-11,width:14,height:26,fill:mid?'transparent':'#0c3c37',stroke:mid?'none':'#7cbb9a','stroke-dasharray':'2 2'},g);
    if(mid){node('use',{href:'#cabinet',color:mid.startsWith('NEW-')?'#fff7a4':zoneColors[s.zone_id],class:'pixel'},g);node('rect',{x:4,y:-13,width:4,height:4,class:'marker'},g);}
    else text(-3,5,'+',11,'#a4d9aa',g);
    node('rect',{x:-8,y:-12,width:16,height:28,class:'focusRing'},g);
    const title=node('title',{},g);title.textContent=mid?`${mid} · ${machineById[mid]?.theme||'What-if addition'}`:`Vacant ${s.location_id}`;
    g.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();if(mid)showMachine(mid);else showManage({destination:s.location_id});}if(e.key==='Escape')clearGhosts();});
    g.addEventListener('mouseenter',()=>{if(!mid&&!drag&&form.target&&!$('review').open)destinationGhost(s.location_id);});
    g.addEventListener('focus',()=>{if(!mid&&form.target&&!$('review').open)destinationGhost(s.location_id);});
    g.addEventListener('mouseleave',()=>{if(hoverGhost&&!$('review').open)clearGhosts();});
    g.addEventListener('blur',()=>{if(hoverGhost&&!$('review').open)clearGhosts();});
  }
  $('stage').dataset.day=String(day);$('stage').dataset.roster=String(Object.keys(layout).length);
}
function renderDay(){
  const row=result.days[day-1];$('day').value=day;$('dayLabel').textContent=String(day).padStart(2,'0')+' / 30';
  $('earningsDate').textContent=`JUL ${String(day).padStart(2,'0')} · EXPECTED GAMING EARNINGS`;
  $('earningsValue').textContent=money(baselineView?row.baseline:row.expected_gaming_earnings);
  $('layoutBadge').textContent=baselineView?'/ BASELINE · READ ONLY':'/ PROPOSED';renderSlots();
}
function stopPlayback(){if(playing)clearInterval(playing);playing=null;$('play').textContent='▶ Play';$('play').setAttribute('aria-label','Play July financial playback');}
function togglePlayback(){if(playing){stopPlayback();return;}if(day===30)day=1;renderDay();$('play').textContent='Ⅱ Pause';$('play').setAttribute('aria-label','Pause July financial playback');playing=setInterval(()=>{day++;renderDay();if(day>=30)stopPlayback();},1000);}
function openPanel(title,wide=false){closeDropdown();$('panelTitle').textContent=title;$('panel').classList.toggle('wide',wide);$('panelBody').replaceChildren();if(!$('panel').open)$('panel').show();}
function closePanel(){closeDropdown();$('panel').close();if(hoverGhost)clearGhosts();}
function selectField(container,label,value,options,onChange,onHover){
  const field=document.createElement('div');field.className='field';
  const lab=document.createElement('label');lab.textContent=label;field.append(lab);
  const button=document.createElement('button');button.className='selectButton';button.type='button';button.setAttribute('role','combobox');button.setAttribute('aria-label',label);button.setAttribute('aria-expanded','false');button.setAttribute('aria-controls','dropdownOptions');
  button.innerHTML=`<span>${esc(options.find(x=>x.value===value)?.label||'Choose…')}</span><span>▾</span>`;
  button.onclick=()=>openDropdown(button,options,onChange,onHover);field.append(button);container.append(field);return button;
}
function openDropdown(button,options,onChange,onHover){
  closeDropdown();dropdown={button,options,onChange,onHover,index:0,filtered:options};
  const box=$('dropdown'),rect=button.getBoundingClientRect();box.hidden=false;
  box.style.width=Math.min(Math.max(rect.width,280),innerWidth-16)+'px';
  box.style.left=Math.min(innerWidth-box.offsetWidth-8,Math.max(8,rect.left))+'px';
  box.style.top=Math.max(8,Math.min(rect.bottom+6,innerHeight-290))+'px';
  button.setAttribute('aria-expanded','true');$('dropdownSearch').value='';renderOptions();$('dropdownSearch').focus();
}
function renderOptions(){
  const d=dropdown;if(!d)return;const q=$('dropdownSearch').value.toLowerCase();d.filtered=d.options.filter(o=>o.label.toLowerCase().includes(q));d.index=M.clamp(d.index,0,Math.max(0,d.filtered.length-1));
  $('dropdownOptions').innerHTML=d.filtered.length?d.filtered.map((o,i)=>`<div id="opt-${i}" class="option" role="option" aria-selected="${i===d.index}" data-index="${i}">${esc(o.label)}</div>`).join(''):'<div class="note">No eligible options</div>';
  $('dropdownSearch').setAttribute('aria-activedescendant','opt-'+d.index);
  for(const el of $('dropdownOptions').children){el.onmouseenter=()=>{if(!el.dataset.index)return;d.index=Number(el.dataset.index);highlightOption();};el.onclick=()=>chooseOption(Number(el.dataset.index));}
  highlightOption();
}
function highlightOption(){if(!dropdown)return;for(const el of $('dropdownOptions').children)el.setAttribute('aria-selected',String(Number(el.dataset.index)===dropdown.index));const o=dropdown.filtered[dropdown.index];if(o&&dropdown.onHover)dropdown.onHover(o.value);}
function chooseOption(i){const d=dropdown,o=d?.filtered[i];if(!o)return;const callback=d.onChange;closeDropdown();callback(o.value);}
function closeDropdown(){if(dropdown){dropdown.button.setAttribute('aria-expanded','false');dropdown=null;}$('dropdown').hidden=true;if(hoverGhost&&!$('review').open)clearGhosts();}
$('dropdownSearch').oninput=()=>{dropdown.index=0;renderOptions();};
$('dropdownSearch').onkeydown=e=>{if(!dropdown)return;if(['ArrowDown','ArrowUp'].includes(e.key)){e.preventDefault();dropdown.index=M.clamp(dropdown.index+(e.key==='ArrowDown'?1:-1),0,dropdown.filtered.length-1);highlightOption();$('opt-'+dropdown.index)?.scrollIntoView({block:'nearest'});}if(e.key==='Enter'){e.preventDefault();chooseOption(dropdown.index);}if(e.key==='Escape'){e.preventDefault();e.stopPropagation();const b=dropdown.button;closeDropdown();b.focus();}};
document.addEventListener('pointerdown',e=>{if(dropdown&&!$('dropdown').contains(e.target)&&!dropdown.button.contains(e.target))closeDropdown();});
function inputField(container,label,key,min,max,step=1){const field=document.createElement('div');field.className='field';const id='field-'+key;field.innerHTML=`<label for="${id}">${esc(label)}</label><input id="${id}" type="number" min="${min}" max="${max}" step="${step}" value="${form[key]}">`;field.querySelector('input').oninput=e=>{form[key]=Number(e.target.value);};container.append(field);}
function showManage(patch={}){
  Object.assign(form,patch);openPanel('Manage the floor');const body=$('panelBody');
  body.innerHTML='<div class="shortcuts"><button data-kind="move">↗ Move</button><button data-kind="add">+ Add machine</button><button data-kind="remove">− Remove</button></div>';
  body.querySelectorAll('[data-kind]').forEach(b=>b.onclick=()=>showManage({kind:b.dataset.kind}));
  const kinds=[['move','Move machine'],['swap','Swap two machines'],['add','Add · what-if'],['remove','Remove · what-if'],['inspect','Inspect machine'],['lease','Leased replacement'],['maintenance','Manufacturer maintenance']].map(([value,label])=>({value,label}));
  selectField(body,'Change',form.kind,kinds,v=>showManage({kind:v}));
  const opts=machineOptions();if(form.kind!=='maintenance'&&!opts.some(x=>x.value===form.target))form.target=opts[0]?.value||'';
  if(form.kind==='maintenance'){
    const manufacturers=[...new Set(data.eligible.map(m=>machineById[m].manufacturer))].sort().map(value=>({value,label:value}));
    if(!manufacturers.some(x=>x.value===form.target))form.target=manufacturers[0].value;
    selectField(body,'Manufacturer',form.target,manufacturers,v=>showManage({target:v}));
  }else if(form.kind==='add'){
    const proxies=data.eligible.map(value=>({value,label:value+' · '+machineById[value].theme}));if(!form.proxy)form.proxy=proxies[0].value;
    selectField(body,'Performance proxy',form.proxy,proxies,v=>showManage({proxy:v}));
  }else selectField(body,'Machine / game',form.target,opts,v=>showManage({target:v}));
  if(form.kind==='swap')selectField(body,'Swap with',form.other,opts.filter(x=>x.value!==form.target),v=>showManage({other:v}));
  if(['add','remove'].includes(form.kind)){
    inputField(body,'July cash cost ($) · paid upfront','cash',0,100000);
    inputField(body,'Activation day · July 1–30','day',1,30);
    inputField(body,form.kind==='add'?'Incremental play share (0–1)':'Play retained elsewhere (0–1)','share',0,1,.05);
  }else inputField(body,'Retained incremental play · mode (0.1–1)','retained',.1,1,.05);
  if(['move','add'].includes(form.kind)){
    // Removal-dependent slots are included at the entered activation boundary.
    const options=vacancies(form.kind==='move'?3:M.clamp(Math.round(form.day),1,30));
    if(!options.some(o=>o.value===form.destination))form.destination=options[0]?.value||'';
    selectField(body,'Destination slot',form.destination,options,v=>{form.destination=v;showManage();},destinationGhost);
    if(!options.length)body.insertAdjacentHTML('beforeend','<p class="note">No legal vacancy at activation. Queue a removal first or choose swap.</p>');
    const mini=document.createElement('div');mini.id='destinationMini';body.append(mini);
    if(form.kind==='add')$('field-day').onchange=()=>showManage();
  }
  const review=document.createElement('button');review.className='full gold';review.textContent='Review change →';body.append(review);
  review.onclick=()=>{
    const a={id:'change-'+crypto.randomUUID().slice(0,12),kind:form.kind};
    if(form.kind==='add')Object.assign(a,{proxy:form.proxy,destination:form.destination,cash:form.cash,day:form.day,share:form.share});
    else if(form.kind==='remove')Object.assign(a,{target:form.target,cash:form.cash,day:form.day,share:form.share});
    else {Object.assign(a,{target:form.target,retained:form.retained});if(form.kind==='move')a.destination=form.destination;if(form.kind==='swap')a.other=form.other;}
    openReview(a);
  };
  body.insertAdjacentHTML('beforeend','<div class="minorLinks"><button id="planButton">Plan drawer</button><button id="suggestButton">Suggested changes</button></div><details id="viewControls"><summary>View controls</summary><div id="views"></div></details>');
  $('planButton').onclick=showPlan;$('suggestButton').onclick=showSuggestions;
  const views=$('views');selectField(views,'Zone focus','all',[{value:'all',label:'Whole floor'},...Object.keys(zoneNames).map(value=>({value,label:zoneNames[value]}))],v=>fit(v==='all'?null:v));
  views.insertAdjacentHTML('beforeend','<div class="minorLinks"><button id="zoomOut" aria-label="Zoom out">−</button><button id="zoomIn" aria-label="Zoom in">+</button><button id="fit">Fit</button></div>');
  $('zoomOut').onclick=()=>zoom(.8);$('zoomIn').onclick=()=>zoom(1.25);$('fit').onclick=()=>fit();
  selectField(views,'Layout',baselineView?'baseline':'proposed',[{value:'proposed',label:'Proposed layout'},{value:'baseline',label:'Baseline · read only'}],v=>{baselineView=v==='baseline';renderDay();showManage();});
  views.insertAdjacentHTML('beforeend',`<div class="field"><label><input id="ambientToggle" type="checkbox" ${ambient?'checked':''}> Ambient guests ${reduced?'(reduced motion)':''}</label></div><p class="note">Synthetic data. Guests are decorative, not a customer model. Supplied coordinates; illustrated rooms are not a surveyed building. Refresh resets your plan.</p>`);
  $('ambientToggle').onchange=e=>{ambient=e.target.checked&&!reduced;if(reduced){e.target.checked=false;toast('Ambient motion is disabled by your reduced-motion preference.');}};
}
function zoom(f){camera=M.zoomAt(camera,{x:innerWidth/2,y:innerHeight/2},f);applyCamera();}
function showMachine(mid){
  openPanel(mid+' · specifications');const m=machineById[mid];
  if(!m){const a=plan.find(a=>'NEW-'+a.id===mid);$('panelBody').innerHTML=`<p>What-if addition · proxy ${esc(a?.proxy)}</p><p class="note">No invented cabinet specifications. To change this addition, undo it in the plan and create a new one.</p><button id="newPlan">Open plan</button>`;$('newPlan').onclick=showPlan;return;}
  form.target=mid;
  $('panelBody').innerHTML=`<div class="kv"><span>Theme</span><span>${esc(m.theme)}</span><span>Configuration (July 1)</span><span>${esc(m.config_id||"Not supplied")}</span><span>Manufacturer</span><span>${esc(m.manufacturer)}</span><span>Ownership / lease</span><span>${esc(m.lease_class)}</span><span>Installed</span><span>${esc(m.install_date?.slice(0,10))}</span><span>Availability · Jan–Jun</span><span>${(m.availability*100).toFixed(2)}%</span><span>Expected / available hour</span><span>${money(m.theo_per_hour)}</span><span>Actual house win</span><span>${money(m.house_win_usd)}</span><span>Expected house win</span><span>${money(m.theo_usd)}</span><span>Payout gap / SD</span><span>${m.standardized_gap.toFixed(2)}</span></div><p class="note">Historical synthetic data; earnings before operating costs. A payout gap is an investigation lead, not proof of a defect. No cabinet model, denomination or game rules are inferred.</p><button id="machineAction" class="gold full">Review an action</button>`;
  $('machineAction').onclick=()=>showManage({target:mid});
}
function showEarnings(){
  openPanel('Earnings · July '+String(day).padStart(2,'0'));const r=result.days[day-1];
  $('panelBody').innerHTML=`<div class="kv"><span>Baseline expected gaming earnings</span><span>${money(r.baseline)}</span><span>Proposed expected gaming earnings</span><span>${money(r.expected_gaming_earnings)}</span><span>Cash paid so far</span><span>${money(r.cash_paid)}</span><span>Planned downtime opportunity</span><span>${money(r.downtime_opportunity)}</span><span>Incremental net impact</span><span>${money(r.mean)}</span><span>10th–90th net</span><span>${money(r.p10)} / ${money(r.p90)}</span><span>Conditional chance positive</span><span>${(r.probability_positive*100).toFixed(1)}%</span></div><p class="note">Cumulative modeled July results, not observed earnings. Expected gaming earnings are before action cash costs and baseline operating costs. Net impact is relative to the unchanged forecast; neither is total business profit.</p><details><summary>Cash timing & model</summary><p class="note">Catalogue upfront costs are paid on July 1; lease daily costs begin on activation. What-if cash is paid upfront. Benefits and planned downtime begin at activation. Day 30 reconciles to the shared 1,000-draw decision engine.</p></details>`;
}
function showPlan(){
  openPanel('Your July plan');const body=$('panelBody');body.innerHTML=`<div class="miniStats"><article><small>COMMITTED CASH</small><strong>${money(result.cash_committed)}</strong></article><article><small>EXPECTED NET IMPACT</small><strong>${money(result.summary.mean)}</strong></article></div><p class="note">${money(result.remaining_budget)} remaining · maximum three action types</p>`;
  if(!plan.length)body.insertAdjacentHTML('beforeend','<p>Keep budget. Your floor is unchanged.</p>');
  for(const a of result.actions){
    const item=document.createElement('div');item.className='planItem';item.innerHTML=`<button aria-label="Undo ${esc(a.id)}">Undo</button><strong>${esc(a.kind.toUpperCase())}</strong><br>${esc(a.target||a.proxy)} ${a.other?'↔ '+esc(a.other):a.destination?'→ '+esc(a.destination):''}<br>July ${a.day} · ${money(a.cost)} cash`;
    item.querySelector('button').onclick=async()=>{try{const old=revision;const value=await api('undo',{plan,action_id:a.id});if(old!==revision)return;acceptPlan(value);showPlan();}catch(e){toast(e.message+' Undo dependent arrivals first.');}};body.append(item);
  }
  body.insertAdjacentHTML('beforeend','<div class="minorLinks"><button id="addAnother">Add change</button><button id="exportPlan">Export plan + daily CSV</button></div><p class="note">Plan lives only in this tab. Refresh resets it; an export is a manual local download.</p>');
  $('addAnother').onclick=()=>showManage();$('exportPlan').onclick=exportPlan;
}
function download(name,body,type){const url=URL.createObjectURL(new Blob([body],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),500);}
function exportPlan(){download('aceiq-plan.json',JSON.stringify({model:data.model,plan,result},null,2),'application/json');const fields=['day','date','baseline','expected_gaming_earnings','cash_paid','daily_cash','downtime_opportunity','mean','p10','p90','probability_positive','machine_count'];download('aceiq-july-playback.csv',fields.join(',')+'\n'+result.days.map(r=>fields.map(k=>r[k]).join(',')).join('\n'),'text/csv');}
async function showSuggestions(){
  openPanel('Suggested changes',true);const body=$('panelBody'),old=revision;body.innerHTML='<p class="loading">Comparing eligible actions with your current plan…</p>';
  try{
    const value=await api('suggestions',{plan});if(old!==revision||!$('panel').open||$('panelTitle').textContent!=='Suggested changes')return;
    if(value.plan_id!==result.plan_id)return;
    body.innerHTML='<p class="note">Incremental expected July net versus your current plan · same seeded forecast and action model</p><div class="suggestionGrid" id="suggestionGrid"></div>';
    if(!value.suggestions.length)body.insertAdjacentHTML('beforeend','<h3>Keep the current plan.</h3><p>No individually feasible positive-net action was found in this search.</p>');
    value.suggestions.forEach((s,i)=>{const card=document.createElement('article');card.className='suggestion';const label=machineById[s.action.target]?.theme||`${s.affected} eligible machines`;card.innerHTML=`<span class="rank">0${i+1} / ${esc(s.action.kind.toUpperCase())}</span><h3>${esc(s.action.target)}</h3><span class="note">${esc(label)}</span><strong>${money(s.marginal.mean)}</strong><small>EXPECTED INCREMENTAL NET</small><p>${money(s.cost)} cash · July ${s.day}<br><span class="note">10–90%: ${money(s.marginal.p10)} to ${money(s.marginal.p90)}</span></p><button class="gold">Review change</button>`;card.querySelector('button').onclick=()=>{if(old!==revision){toast('Plan changed. Refresh suggestions.');return;}openReview({...s.action,id:'change-'+crypto.randomUUID().slice(0,12)});};$('suggestionGrid').append(card);});
    body.insertAdjacentHTML('beforeend',`<details><summary>Search scope & assumptions</summary><p class="note">${esc(value.scope)} Evaluated ${value.searched} candidates before feasibility filtering. Effects are assumed; probabilities are conditional. Review never applies an action automatically.</p></details>`);
  }catch(e){body.innerHTML=`<p class="error">${esc(e.message)}</p>`;}
}
function actionRoutes(a){
  const find=m=>slots.find(s=>data.initial[s.location_id]===m);
  if(a.kind==='swap'){const p=find(a.target),q=find(a.other);return p&&q?M.pairedRoutes(p,q):[];}
  if(a.kind==='move'){const p=find(a.target),q=slotById[a.destination];return p&&q?[M.route(p,q)]:[];}
  if(a.kind==='add'){const q=slotById[a.destination];return q?[M.route({x:q.x,y:q.y-45},q)]:[];}
  return [];
}
function clearGhosts(){ghostRoutes=[];hoverGhost=false;$('ghosts').replaceChildren();if($('destinationMini'))$('destinationMini').replaceChildren();}
function setGhosts(routes){
  ghostRoutes=routes;ghostStart=performance.now();const root=$('ghosts');root.replaceChildren();
  routes.forEach((r,i)=>{node('path',{d:`M${r[0].x} ${r[0].y}Q${r[1].x} ${r[1].y} ${r[2].x} ${r[2].y}`,class:'route',stroke:colors[i]},root);node('use',{href:'#cabinet',id:'ghost-'+i,class:'ghost',color:colors[i],transform:`translate(${r[2].x},${r[2].y})`},root);});
}
function miniPreview(routes,container){
  if(!container)return;container.replaceChildren();if(!routes.length)return;
  const ps=routes.flat(),x=Math.min(...ps.map(p=>p.x))-25,y=Math.min(...ps.map(p=>p.y))-25,w=Math.max(...ps.map(p=>p.x))-x+25,h=Math.max(...ps.map(p=>p.y))-y+25;
  const svg=node('svg',{viewBox:`${x} ${y} ${Math.max(w,60)} ${Math.max(h,60)}`,class:'previewMap','aria-label':'Illustrative relocation preview'},container);
  const unit=Math.max(1,Math.max(h/130,w/400));
  routes.forEach((r,i)=>{node('path',{d:`M${r[0].x} ${r[0].y}Q${r[1].x} ${r[1].y} ${r[2].x} ${r[2].y}`,class:'route',stroke:colors[i],'vector-effect':'non-scaling-stroke'},svg);node('circle',{cx:r[0].x,cy:r[0].y,r:5*unit,fill:'none',stroke:colors[i]},svg);node('rect',{x:-5*unit,y:-8*unit,width:10*unit,height:16*unit,fill:colors[i],class:'miniGhost','data-route':i,transform:`translate(${r[2].x},${r[2].y})`},svg);});
}
function destinationGhost(destination){
  if(baselineView||drag||$('review').open)return;const a={kind:form.kind==='add'?'add':'move',target:form.target,destination};const routes=actionRoutes(a);setGhosts(routes);hoverGhost=true;miniPreview(routes,$('destinationMini'));
}
async function openReview(action){
  if(baselineView){toast('Switch View controls to Proposed layout before editing. Baseline is read-only.');return;}
  closeDropdown();stopPlayback();clearGhosts();preview=null;previewAction=action;const serial=++previewSerial,old=revision;
  $('reviewTitle').textContent=action.kind==='swap'?`${action.target} ↔ ${action.other}`:action.target||'Add machine';
  $('reviewBody').innerHTML=`<p>${esc(action.destination?'Destination '+action.destination:action.kind==='maintenance'?'Manufacturer sweep':action.kind==='swap'?'Exchange the two original positions':action.kind==='add'?'Hypothetical addition':'Review '+action.kind)}</p><div id="miniPreview"></div><p class="loading">Validating plan and estimating impact…</p>`;
  $('confirm').disabled=true;$('confirm').textContent='Getting estimate…';if(!$('review').open)$('review').showModal();
  const routes=actionRoutes(action);setGhosts(routes);miniPreview(routes,$('miniPreview'));
  try{
    const value=await api('preview',{plan,action});if(serial!==previewSerial||old!==revision||!$('review').open)return;preview=value;
    const a=value.actions.at(-1);$('reviewBody').innerHTML=`<p>${esc(action.destination?'→ '+action.destination:action.kind==='swap'?'Two machines · one atomic change':a.assumption.slice(0,70))}<br><span class="note">Activates July ${a.day}, 2025 · preview only</span></p><div id="miniPreview"></div><div class="miniStats"><article><small>INCREMENTAL JULY NET</small><strong>${money(value.marginal.mean)}</strong></article><article><small>ADDITIONAL CASH</small><strong>${money(value.additional_cash)}</strong></article></div><details><summary>See details & assumptions</summary><div class="kv"><span>Full-plan expected gaming earnings</span><span>${money(value.summary.expected_gaming_earnings)}</span><span>Unchanged baseline earnings</span><span>${money(value.summary.baseline)}</span><span>Full-plan incremental net after costs</span><span>${money(value.summary.mean)}</span><span>Marginal net · 10–90%</span><span>${money(value.marginal.p10)} / ${money(value.marginal.p90)}</span><span>Marginal chance positive</span><span>${(100*value.marginal.probability_positive).toFixed(1)}%</span><span>July 30 machine count</span><span>${value.summary.machine_count}</span><span>Target / proxy</span><span>${esc(action.target||action.proxy)} ${esc(action.other||'')}</span></div><p class="note">Supplied configuration: ${esc(machineById[action.target]?.config_id||"proxy / group scope")}${action.other?" / "+esc(machineById[action.other]?.config_id):""}. ${esc(a.assumption)} Net is relative to the current plan. Gaming earnings exclude action cash and baseline operating costs; this is not total profit. Routes illustrate relocation, not physical transport. Swap keeps both identities and configurations.</p></details>`;
    miniPreview(routes,$('miniPreview'));$('confirm').disabled=false;$('confirm').textContent='Confirm '+action.kind;
  }catch(e){if(serial!==previewSerial)return;$('reviewBody').insertAdjacentHTML('beforeend',`<p class="error">${esc(e.message)}</p>`);clearGhosts();$('confirm').textContent='Invalid change';}
}
function cancelReview(){previewSerial++;preview=null;previewAction=null;clearGhosts();$('review').close();}
function acceptPlan(value){plan=value.plan;result=value;revision++;previewSerial++;preview=null;clearGhosts();renderDay();}
$('confirm').onclick=async()=>{
  if(!preview||!previewAction)return;const serial=previewSerial,old=revision;$('confirm').disabled=true;
  try{const value=await api('confirm',{plan,action:previewAction,estimate_id:preview.estimate_id});if(serial!==previewSerial||old!==revision)return;acceptPlan(value);$('review').close();closePanel();toast('Plan updated. Layout changes at the activation date.');}
  catch(e){toast(e.message);$('confirm').disabled=false;}
};
$('cancelReview').onclick=cancelReview;$('closeReview').onclick=cancelReview;
$('review').addEventListener('cancel',e=>{e.preventDefault();cancelReview();});
function localPoint(e){const r=$('floor').getBoundingClientRect();return {x:e.clientX-r.left,y:e.clientY-r.top};}
function finishDrag(cancel=false,event=null){
  const d=drag;if(!d)return;drag=null;document.documentElement.classList.remove('floor-dragging');document.body.classList.remove('floor-dragging');
  if($('floor').hasPointerCapture(d.pointer))$('floor').releasePointerCapture(d.pointer);
  document.querySelectorAll('.legal').forEach(x=>x.classList.remove('legal'));
  $('ghosts').replaceChildren();ghostRoutes=[];
  if(cancel)return;
  if(!d.moved){if(d.machine)showMachine(d.machine);return;}
  if(!d.machine||!event)return;
  const target=M.dropTarget(M.worldPoint(camera,localPoint(event)),slots,12);
  if(!target||target.location_id===d.slot)return;
  const occupant=currentLayout()[target.location_id],changed=changedTargets();
  if(occupant){
    if(!data.eligible.includes(occupant)||changed.has(occupant)||occupant.startsWith('NEW-')){toast('This machine is already modified or not eligible for a swap.');return;}
    openReview({id:'swap-'+crypto.randomUUID().slice(0,12),kind:'swap',target:d.machine,other:occupant});
  }else if(vacancies().some(v=>v.value===target.location_id))openReview({id:'move-'+crypto.randomUUID().slice(0,12),kind:'move',target:d.machine,destination:target.location_id});
  else toast('This destination is reserved or unavailable at activation.');
}
$('floor').addEventListener('pointerdown',e=>{
  if(e.button!==0||$('review').open)return;
  const tile=e.target.closest('[data-slot]'),mid=tile?.dataset.machine;
  if(mid&&(baselineView||changedTargets().has(mid)||!data.eligible.includes(mid))){showMachine(mid);return;}
  e.preventDefault();window.getSelection()?.removeAllRanges();stopPlayback();closeDropdown();clearGhosts();
  document.documentElement.classList.add('floor-dragging');document.body.classList.add('floor-dragging');
  const p=localPoint(e);drag={pointer:e.pointerId,start:p,camera:{...camera},machine:mid||null,slot:tile?.dataset.slot,moved:false};
  $('floor').setPointerCapture(e.pointerId);
  $('stage').dataset.dragChecks='0';$('stage').dataset.dragSelection='';
  if(mid){for(const v of vacancies())document.querySelector(`[data-slot="${v.value}"]`)?.classList.add('legal');node('use',{href:'#cabinet',id:'dragGhost',color:'#fff0a3',transform:`translate(${M.worldPoint(camera,p).x},${M.worldPoint(camera,p).y})`},$('ghosts'));}
});
$('floor').addEventListener('pointermove',e=>{
  if(!drag||drag.pointer!==e.pointerId)return;e.preventDefault();const p=localPoint(e),dx=p.x-drag.start.x,dy=p.y-drag.start.y;if(Math.hypot(dx,dy)>4)drag.moved=true;
  if(drag.machine){const w=M.worldPoint(camera,p);$('dragGhost')?.setAttribute('transform',`translate(${w.x},${w.y})`);}
  else {camera={...drag.camera,x:drag.camera.x+dx,y:drag.camera.y+dy};applyCamera();}
  // Record actual held-pointer evidence, including crossing overlay labels.
  const hit=document.elementFromPoint(e.clientX,e.clientY);$('stage').dataset.dragCursor=hit?getComputedStyle(hit).cursor:'';
  $('stage').dataset.dragMachineCursor=getComputedStyle(document.querySelector('.slot')).cursor;
  $('stage').dataset.dragOverlayCursor=getComputedStyle($('earningsButton')).cursor;
  $('stage').dataset.dragSelection=String(window.getSelection());$('stage').dataset.dragChecks=String(Number($('stage').dataset.dragChecks)+1);
});
$('floor').addEventListener('pointerup',e=>finishDrag(false,e));
$('floor').addEventListener('pointercancel',()=>finishDrag(true));
$('floor').addEventListener('lostpointercapture',()=>finishDrag(true));
document.addEventListener('selectstart',e=>{if(drag)e.preventDefault();},true);
document.addEventListener('dragstart',e=>{if(drag||$('floor').contains(e.target))e.preventDefault();},true);
document.addEventListener('keydown',e=>{if(e.key==='Escape'){finishDrag(true);if($('review').open)cancelReview();else if(dropdown)closeDropdown();else closePanel();clearGhosts();}});
$('floor').addEventListener('wheel',e=>{if(e.ctrlKey||e.metaKey)return;e.preventDefault();camera=M.zoomAt(camera,localPoint(e),Math.exp(-e.deltaY*.001));applyCamera();},{passive:false});
function seedGuests(){
  agents=[];$('guests').replaceChildren();let seed=42;const random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
  const obstacles=slots.map(s=>({...s,w:12,h:23}));
  for(let i=0;i<28;i++){
    let p;do{p={x:Math.round((40+random()*950)/8)*8,y:Math.round((60+random()*900)/8)*8};}while(M.blocked(p,obstacles,2));
    const sprite=node('use',{href:'#person',color:colors[i%colors.length],transform:`translate(${p.x},${p.y})`,class:'pixel'},$('guests'));
    agents.push({p,sprite,route:[],wait:i*150,index:i});
  }
}
function animate(time){
  const dt=Math.min(40,time-lastTime||16);lastTime=time;
  if(ghostRoutes.length){const t=reduced?1:((time-ghostStart)%2200)/2200;ghostRoutes.forEach((r,i)=>{const p=M.onRoute(r,t);$('ghost-'+i)?.setAttribute('transform',`translate(${p.x},${p.y})`);document.querySelectorAll(`.miniGhost[data-route="${i}"]`).forEach(g=>g.setAttribute('transform',`translate(${p.x},${p.y})`));});}
  if(ambient&&!reduced&&data){
    const obstacles=slots.filter(s=>currentLayout()[s.location_id]).map(s=>({...s,w:12,h:23}));
    for(const a of agents){
      if(a.wait>0){a.wait-=dt;continue;}
      if(!a.route.length&&time>nextRoute){
        const occupied=slots.filter(s=>currentLayout()[s.location_id]);const target=occupied[(a.index*41+Math.floor(time/3000))%occupied.length];
        if(target){a.route=M.walkRoute(a.p,{x:target.x,y:target.y+26},obstacles,{x:30,y:45,w:1080,h:940});a.sprite.dataset.state='walking';}nextRoute=time+85;
        if(!a.route.length)a.wait=1000;continue;
      }
      if(a.route.length){const q=a.route[0],dist=Math.hypot(q.x-a.p.x,q.y-a.p.y),step=dt*.022;
        if(dist<=step){a.p={...q};a.route.shift();if(!a.route.length){a.wait=2500+a.index*70;a.sprite.dataset.state='playing';}}
        else {const p={x:a.p.x+(q.x-a.p.x)*step/dist,y:a.p.y+(q.y-a.p.y)*step/dist};if(!M.blocked(p,obstacles,2))a.p=p;else{a.route=[];a.wait=500;}}
        a.sprite.setAttribute('transform',`translate(${a.p.x},${a.p.y})`);
      }
    }
  }requestAnimationFrame(animate);
}
$('manageButton').onclick=()=>showManage();$('closePanel').onclick=closePanel;$('earningsButton').onclick=showEarnings;$('play').onclick=togglePlayback;
$('day').oninput=e=>{stopPlayback();day=Number(e.target.value);renderDay();};
if(sessionStorage.getItem('aceiq-hint-dismissed'))$('hint').hidden=true;
$('dismissHint').onclick=()=>{$('hint').hidden=true;sessionStorage.setItem('aceiq-hint-dismissed','1');};
window.addEventListener('resize',()=>{closeDropdown();fit();});
fetch('/api/bootstrap').then(r=>{if(!r.ok)throw new Error('Floor server unavailable');return r.json();}).then(value=>{
  data=value;result=data.result;slots=data.slots.map(s=>({...s,...point(s)}));slotById=Object.fromEntries(slots.map(s=>[s.location_id,s]));machineById=Object.fromEntries(data.machines.map(m=>[m.machine_id,m]));form.target=data.eligible[0];ambient=!reduced;
  architecture();fit();renderDay();seedGuests();requestAnimationFrame(animate);$('stage').dataset.ready='true';
}).catch(e=>toast(e.message));
})();
