'use strict';
const R=window.RESEARCH_DATA, $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const n=(v,d=2)=>Number.isFinite(v)?Number(v).toFixed(d):'—';
const pct=v=>Number.isFinite(v)?(100*v).toFixed(1)+'%':'—';
const summary=(kind,scenario)=>R.summary.find(r=>r.kind===kind&&r.scenario===scenario);
const a=R.audit, day=summary('전체','wed14'), night=summary('전체','wed20'), sunday=summary('전체','sun14'), sw=summary('수영장','sun14'), swn=summary('수영장','wed20');
$('hero-total').textContent=a.primary;$('hero-open').textContent=night.open;
$('intro-finding').textContent=`서울시 등록 시설 ${a.primary}개를 비교한 결과, 수요일 저녁에도 ${night.open}개가 운영시간에 포함된다. 반면 일요일 수영장은 ${sw.total}개 중 ${sw.open}개만 시간표상 개방이 확인된다. 어떤 종목을 언제 이용하려는지에 따라 도시의 접근성이 달라진다.`;
$('finding-hours').textContent=`같은 ${a.primary}개 표본에서 수요일14시 ${day.open}개, 20시 ${night.open}개가 운영시간에 포함된다. 저녁의 확인된 개방 수는 낮의 ${pct(night.open/day.open)}이다. 저녁 ${night.unknown}개는 미확정이므로, 시간표상 개방 수의 범위는 ${night.open}~${night.open+night.unknown}개다. 일요일 전체는 ${sunday.open}~${sunday.open+sunday.unknown}개여서, 전체 종목에서 저녁보다 일요일이 반드시 더 불리하다고 단정할 수 없다.`;
$('finding-swim').textContent=`수영장 ${sw.total}개 중 수요일20시에는 ${swn.open}개가 운영시간 내다. 일요일14시에는 ${sw.open}개가 시간 내, ${sw.closed}개가 시간 외, ${sw.unknown}개가 확인 불가다. 미확정 시설을 모두 열려 있다고 가정해도 ${sw.open+sw.unknown}개로 평일 저녁보다 적다. 정기 휴관과 종목별 운영체계의 차이를 함께 살펴야 한다.`;
$('finding-corr').textContent=`427개 행정동에서 등록 밀도와 수요일20시 접근성의 Spearman 순위상관은 ${n(a.correlations.wed20.density_vs_access_spearman,3)}이다. 같은 거리 모형의 시간 미반영 접근성과 저녁 접근성은 ${n(a.correlations.wed20.potential_vs_access_spearman,3)}로 더 유사하다. 즉, 기본적인 입지 패턴은 상당 부분 유지되지만 시간 제약으로 일부 동네의 순위와 이용 기회가 달라진다.`;
const districtNight=R.districts.filter(x=>x.kind==='전체'&&x.scenario==='wed20');
const hi=[...districtNight].sort((x,y)=>y.access-x.access).slice(0,3),lo=[...districtNight].sort((x,y)=>x.access-y.access).slice(0,3);
$('place-notes').innerHTML=`<p><strong>어디가 높은가.</strong> 자치구의 격자 평균으로 보면 ${hi.map(x=>esc(x.district)+' '+n(x.access)).join(', ')}에서 수요일20시 접근성이 상대적으로 높다. 이는 해당 구 내부 시설 수뿐 아니라 인접 지역 시설의 기여도 반영한 값이다.</p><p><strong>어디가 낮은가.</strong> ${lo.map(x=>esc(x.district)+' '+n(x.access)).join(', ')}에서는 상대적으로 낮다. 이 값만으로 주민의 불편이나 시설 부족을 확정할 수 없다. 산지 등 비거주 공간의 비중과 등록 누락을 함께 검토해야 한다.</p>`;
$('case-table').innerHTML=R.case_studies.map(r=>`<tr><td>${esc(r.district)} ${esc(r.name)}</td><td>${r.n}</td><td>${n(r.area_km2)}</td><td>${n(r.density)}</td><td>${r.density_rank}</td><td>${n(r.access)}</td><td>${r.access_rank}</td><td>${pct(r.external_share)}</td></tr>`).join('');
$('case-interpretations').innerHTML=R.case_paragraphs.map(p=>`<article><h4>${esc(p.title)}</h4><img class="case-chart" src="figures/${esc(p.figure)}" alt="${esc(p.summary)}" loading="lazy"><p class="case-summary">${esc(p.summary)}</p><p class="fine">${esc(p.note)}</p><details class="case-detail"><summary>상세 해석과 한계</summary><p>${esc(p.text)}</p></details></article>`).join('');
$('flow').innerHTML=[`전체 ${a.source_total}행`,`공공 분류 ${a.public_total}행`,`6종 ${a.selected_rows}행`,`중복 정리 ${a.unique}개`,`휴관 ${a.closed_records}개 제외`,`운영 항목 중 좌표 누락·경계 밖 ${a.active_missing_outside}개 제외`,`좌표 의심 ${a.coordinate_flag_excluded.length}개 제외`,`분석 ${a.primary}개`].map(t=>`<span>${t}</span>`).join('');
$('sensitivity-text').textContent=`반감거리를1km로 바꾸거나 탐색 반경을1km로 줄였을 때 행정동의 저녁 접근성 순위상관은 각각 ${n(a.sensitivity[1].rank_corr_to_base,3)}, ${n(a.sensitivity[2].rank_corr_to_base,3)}이다. 24시간 표기 시설 ${a.listed24h}개를 제외하면 ${n(a.sensitivity[3].rank_corr_to_base,3)}, 과거 안내 문구가 있는 ${a.legacy}개를 제외하면 ${n(a.sensitivity[4].rank_corr_to_base,3)}이다. 모형과 표본 선택에 영향을 받는 결과임을 보여준다.`;
R.kinds.forEach(k=>$('kind').add(new Option(k,k)));
[...new Set(R.districts.map(x=>x.district))].sort().forEach(k=>$('district').add(new Option(k,k)));
const map=L.map('map',{scrollWheelZoom:true,minZoom:10,maxZoom:17}).setView([37.565,126.99],11);
map.attributionControl.setPrefix('Leaflet');map.attributionControl.addAttribution('경계: SGIS / vuski · 시설: 서울특별시');
let zones,markers=L.layerGroup().addTo(map),selected=null,current=new Map();
const colors=['#eeeeee','#d7d7d7','#b4b4b4','#8b8b8b','#616161','#353535'];
const titles={access:'운영시간 반영 접근성',potential:'시간 미반영 잠재 접근성',density:'등록 시설 밀도',open_density:'시간대별 개방 밀도',retention:'접근성 유지율',uncertainty:'확인 불가 시설의 접근성 기여'};
const captions={access:'거리 가중 시설 수. 미확정 시설은 기여에서 제외한 보수적 값이며, 시간표상 공급을 뜻한다.',potential:'시간 제한 없이 모든 분석 시설을 개방으로 둔 거리 가중 시설 수. 운영시간을 반영한 값과 같은 색상 기준이다.',density:'행정동 내부 등록 시설 수 ÷ 면적(km²). 시설이 없는 동도 이웃 동의 공급으로 접근성이 생길 수 있다.',open_density:'선택 시각에 운영시간에 포함되는 동 내부 시설 수 ÷ 면적(km²). 등록 밀도와 같은 색상 기준이다.',retention:'시간 반영 접근성 ÷ 시간 미반영 잠재 접근성. 100%에 가까울수록 등록된 주변 공급이 해당 시각에도 유지된다.',uncertainty:'미확정 시설을 모두 개방으로 둘 때 추가되는 거리 가중 시설 수. 실제 개방 시설을 뜻하지 않는다.'};
const value=r=>$('metric').value==='uncertainty'?r.access_upper-r.access:r[$('metric').value];
function updateDetail(){
 if(!selected||!current.has(selected))return;
 const r=current.get(selected),k=$('kind').value,s=$('scenario').value;
 $('detail-title').textContent=r.district+' '+r.name;
 $('detail-body').innerHTML=`<p>${esc(k)} · ${esc(R.scenarios[s])}</p><dl>${[['등록 시설',r.n+'개'],['운영시간 내',r.open+'개'],['시간 확인 불가',r.unknown+'개'],['등록 밀도',n(r.density)+'개/km²'],['잠재 접근성',n(r.potential)],['시간 반영 접근성',n(r.access)+'–'+n(r.access_upper)],['접근성 유지율',pct(r.retention)+'–'+pct(r.retention_upper)]].map(([t,v])=>`<div><dt>${t}</dt><dd>${v}</dd></div>`).join('')}</dl><p>시설 수는 동 내부 집계이다. 접근성에는 동 밖2km 이내 시설도 기여한다. ${r.n===0?'동 내부 시설이0개여도 접근성이0인 것은 아니다.':''}</p>`;
}
function render(){
 const k=$('kind').value,s=$('scenario').value,m=$('metric').value;
 const rows=R.metrics.filter(x=>x.kind===k&&x.scenario===s);current=new Map(rows.map(r=>[r.code,r]));
 const sum=summary(k,s);
 $('summary').innerHTML=[['등록 분석 표본',sum.total],['운영시간 내',sum.open],['운영시간 외',sum.closed],['확인 불가',sum.unknown]].map(([t,v])=>`<div class="stat"><small>${t}</small><strong>${v}</strong><span class="unit">개</span></div>`).join('');
 let scale;
 if(m==='retention')scale=1;
 else{
  const reference=m==='access'?'potential':m==='open_density'?'density':m;
  const values=R.metrics.filter(r=>r.kind===k&&(reference==='uncertainty'||r.scenario==='wed14')).map(r=>reference==='uncertainty'?r.access_upper-r.access:r[reference]).filter(Number.isFinite).sort((x,y)=>x-y);
  scale=values[Math.min(values.length-1,Math.floor(values.length*.98))]||1;
 }
 function color(v){return v===null||!Number.isFinite(v)?'#bdbdbd':v===0?'#ffffff':colors[Math.min(5,Math.floor(v/scale*6))];}
 if(zones)map.removeLayer(zones);
 zones=L.geoJSON(R.geo,{style:f=>({fillColor:color(value(current.get(f.properties.adm_cd))),fillOpacity:.96,color:f.properties.adm_cd===selected?'#df6029':'#fff',weight:f.properties.adm_cd===selected?2:0.5}),onEachFeature:(f,l)=>{
  const r=current.get(f.properties.adm_cd),v=value(r);l.bindTooltip(`${esc(r.district)} ${esc(r.name)}<br>${esc(titles[m])}: ${m==='retention'?pct(v):n(v)}`,{className:'tooltip',sticky:true});
  l.on('click',()=>{selected=r.code;zones.setStyle(f=>({weight:f.properties.adm_cd===selected?2:.5,color:f.properties.adm_cd===selected?'#df6029':'#fff'}));l.bringToFront();updateDetail();});
 }}).addTo(map);
 markers.clearLayers();
 if($('points').checked){R.facilities.filter(f=>f.eligible&&(k==='전체'||f.kind===k)).forEach(f=>{
  const status=f.status[s],state=status===1?'운영시간 내':status===0?'운영시간 외':'확인 불가';
  const marker=L.circleMarker([f.lat,f.lon],{radius:4,weight:1,color:'#ffffff',fillColor:status===1?'#df6029':status===0?'#bababa':'#454545',fillOpacity:1});
  marker.bindPopup(`<h4>${esc(f.name)}</h4><b>${esc(f.kind)} · ${state}</b><p>평일 ${esc(f.weekday)}<br>주말 ${esc(f.weekend)}</p><p>${esc(f.note||'별도 시간 안내 없음')}</p><p>사용료: ${esc(f.fee||'기재 없음')}<br>대관: ${esc(f.rental||'기재 없음')}</p><p>${esc(f.codingReason)}</p><a href="${esc(f.url)}" target="_blank" rel="noopener">공식 시설 상세 ↗</a><p>시간표상 판정이며 실제 예약 가능 여부는 별도 확인</p>`);markers.addLayer(marker);
 });}
 markers.bringToFront?.();
 const unit=m.includes('density')?'개/km²':m==='retention'?'%':'거리 가중 시설 수';
 $('legend').innerHTML=`<b>${esc(titles[m])}</b><div class="legend-colors">${colors.map(c=>`<i style="background:${c}"></i>`).join('')}</div><div class="legend-values"><span>0</span><span>${m==='retention'?'100%':n(scale)+' 이상'}</span></div><div>${unit} · ${m==='retention'?'회색: 분모0':'상위2% 색상 포화'}</div>`;
 $('metric-caption').textContent=captions[m];
 $('district-table').innerHTML=R.districts.filter(r=>r.kind===k&&r.scenario===s).sort((x,y)=>y.access-x.access).map(r=>`<tr><td>${esc(r.district)}</td><td>${r.n}</td><td>${r.open}</td><td>${r.unknown}</td><td>${n(r.density)}</td><td>${n(r.access)}</td><td>${n(r.access_upper)}</td></tr>`).join('');
 updateDetail();
}
['kind','scenario','metric','points'].forEach(id=>$(id).addEventListener('change',render));
$('district').addEventListener('change',()=>{const district=$('district').value;const features=R.geo.features.filter(f=>!district||f.properties.sggnm===district);map.fitBounds(L.geoJSON(features).getBounds(),{padding:[18,18],animate:!matchMedia('(prefers-reduced-motion:reduce)').matches});});
render();map.fitBounds(zones.getBounds(),{padding:[12,12]});
