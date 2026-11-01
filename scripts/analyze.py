"""Spatial analysis from frozen public source files; no network or API key needed."""
from pathlib import Path
from collections import Counter, defaultdict
import csv, hashlib, json, re, sys
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point
from schedules import SCENARIOS, scenario_states, clean
from collect import KINDS
from case_studies import build as build_cases, make_charts as make_case_charts

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed';DIST=ROOT/'dist'

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')

def records(frame):
    return json.loads(frame.to_json(orient='records',force_ascii=False))

def csvout(name,frame):
    frame.to_csv(OUT/name,index=False,encoding='utf-8-sig')
    frame.to_csv(DIST/'downloads'/name,index=False,encoding='utf-8-sig')

def main():
    for p in [OUT,DIST/'data',DIST/'figures',DIST/'downloads']:p.mkdir(parents=True,exist_ok=True)
    raw=json.loads((ROOT/'data/raw/seoul_sports_20261031.json').read_text(encoding='utf-8'))['DATA']
    coords={r['id']:r for r in json.loads((ROOT/'data/raw/coordinates.json').read_text(encoding='utf-8'))}
    selected=[r for r in raw if r['bk_cd_name']=='공공체육시설' and r['ft_kind_name'] in KINDS]
    # Same name (whitespace removed), type and address identifies duplicate records.
    groups=defaultdict(list)
    for r in selected:
        key=tuple(re.sub(r'\s+','',str(r[k] or '')) for k in ['ft_title','ft_kind_name','ft_addr'])
        groups[key].append(r)
    fs=[];duplicates=[]
    for group in groups.values():
        r=sorted(group,key=lambda x:x['ft_idx'])[0]
        vals,reason=scenario_states(r)
        if len(group)>1:
            other=[scenario_states(x)[0] for x in group]
            vals=[a if all(b[i]==a for b in other) else -1 for i,a in enumerate(vals)]
            duplicates.append({'kept':r['ft_idx'],'ids':[x['ft_idx'] for x in group],'name':r['ft_title'],'rule':'같은 종목·공백제거 시설명·주소, 작은 ID 유지; 시각 판정 충돌은 확인 불가'})
        c=coords.get(r['ft_idx'],{}).get('coordinates')
        fs.append({'id':r['ft_idx'],'name':r['ft_title'],'kind':r['ft_kind_name'],'sourceDistrict':r['ar_cd_name'] if r['ar_cd_name']=='중구' else r['ar_cd_name']+'구',
                   'address':r['ft_addr'],'state':r['ft_operation_name'],'lon':c[0] if c else None,'lat':c[1] if c else None,
                   'weekday':clean(r['ft_wd_time']),'weekend':clean(r['ft_we_time']),'note':clean(r['ft_info_time']),
                   'fee':clean(r['ft_money']),'rental':r['rt_cd_name'],'url':coords.get(r['ft_idx'],{}).get('url'),
                   'status':dict(zip(SCENARIOS,vals)),'codingReason':reason,
                   'legacy':bool(re.search(r'코로나|방역|21\.11|2021|2025년 이후',str(r))),
                   'listed24h':'00:00~24:00' in clean(r['ft_wd_time']),
                   'free':clean(r['ft_money']) in ['무료','무료 개방','무료개방'],
                   'sourceIds':[x['ft_idx'] for x in group]})
    dong=gpd.read_file(ROOT/'data/boundaries/seoul_admdong_20261001.geojson').sort_values('adm_cd').reset_index(drop=True)
    district=gpd.read_file(ROOT/'data/boundaries/seoul_districts_20261001.geojson').sort_values('sgg').reset_index(drop=True)
    dg=dong.to_crs(5179);dong['area_km2']=dg.area/1e6
    valid=[i for i,f in enumerate(fs) if f['lat'] is not None and 33<f['lat']<39 and 124<f['lon']<132]
    pts=gpd.GeoDataFrame({'fid':valid},geometry=[Point(fs[i]['lon'],fs[i]['lat']) for i in valid],crs=4326)
    join=gpd.sjoin(pts,dong[['adm_cd','adm_nm','sggnm','geometry']],how='left',predicate='intersects').sort_values(['fid','adm_cd']).drop_duplicates('fid')
    for f in fs:f.update(dong=None,district=None,eligible=False,coordinateFlag='좌표 미확인 또는 서울 경계 밖')
    for rr in join.itertuples():
        f=fs[rr.fid]
        if isinstance(rr.adm_cd,str):
            flag='원자료 구·좌표 기반 구 불일치' if f['sourceDistrict']!=rr.sggnm else ''
            if f['id']==1153:flag='증산동 주소이나 진관동 시설 좌표와40m: 좌표 재확인 필요'
            f.update(dong=rr.adm_cd,dongName=rr.adm_nm.split()[-1],district=rr.sggnm,eligible=f['state']=='운영' and not flag,coordinateFlag=flag)
    # No forced snapping: missing/outside coordinates stay excluded and audited.
    primary=[f for f in fs if f['eligible']]
    minx,miny,maxx,maxy=dg.total_bounds;size=500
    xy=[(x,y) for y in np.arange(np.floor(miny/size)*size+size/2,maxy,size) for x in np.arange(np.floor(minx/size)*size+size/2,maxx,size)]
    grid=gpd.GeoDataFrame(geometry=[Point(*p) for p in xy],crs=5179)
    grid=gpd.sjoin(grid,dg[['adm_cd','sggnm','geometry']],how='inner',predicate='within').sort_values('adm_cd')
    grid=grid.loc[~grid.index.duplicated()].reset_index(drop=True)
    missing=set(dong.adm_cd)-set(grid.adm_cd)
    if missing:
        extra=dg[dg.adm_cd.isin(missing)][['adm_cd','sggnm','geometry']].copy();extra.geometry=extra.representative_point()
        grid=gpd.GeoDataFrame(pd.concat([grid[['adm_cd','sggnm','geometry']],extra],ignore_index=True),crs=5179)
    fp=gpd.GeoSeries([Point(f['lon'],f['lat']) for f in primary],crs=4326).to_crs(5179)
    fxy=np.array([(p.x,p.y) for p in fp]);gxy=np.array([(p.x,p.y) for p in grid.geometry])
    distances=np.sqrt(((gxy[:,None,:]-fxy[None,:,:])**2).sum(axis=2))
    kernel=2.0**(-distances/500)*(distances<=2000)
    W=np.vstack([kernel[(grid.adm_cd==c).to_numpy()].mean(axis=0) for c in dong.adm_cd])
    fn=np.array([f['dong'] for f in primary]); fk=np.array([f['kind'] for f in primary])
    states=np.array([[f['status'][s] for s in SCENARIOS] for f in primary])
    metrics=[];summary=[];district_metrics=[]
    for kind in ['전체']+KINDS:
        sel=np.ones(len(primary),dtype=bool) if kind=='전체' else fk==kind
        potential=W@sel.astype(float)
        for si,key in enumerate(SCENARIOS):
            op=sel&(states[:,si]==1);un=sel&(states[:,si]==-1)
            acc=W@op.astype(float);upper=W@(op|un).astype(float)
            total=int(sel.sum());opened=int(op.sum());unknown=int(un.sum())
            summary.append({'kind':kind,'scenario':key,'label':SCENARIOS[key][0],'total':total,'open':opened,'unknown':unknown,'closed':total-opened-unknown})
            for i,r in dong.iterrows():
                local=fn==r.adm_cd;n=int((local&sel).sum());o=int((local&op).sum());u=int((local&un).sum())
                metrics.append({'code':r.adm_cd,'district':r.sggnm,'name':r.adm_nm.split()[-1],'kind':kind,'scenario':key,'n':n,'open':o,'unknown':u,'area_km2':r.area_km2,
                                'density':n/r.area_km2,'open_density':o/r.area_km2,'potential':float(potential[i]),'access':float(acc[i]),'access_upper':float(upper[i]),
                                'retention':float(acc[i]/potential[i]) if potential[i]>0 else None,'retention_upper':float(upper[i]/potential[i]) if potential[i]>0 else None,
                                'grid_n':int((grid.adm_cd==r.adm_cd).sum())})
            for r in district.itertuples():
                mask=(grid.sggnm==r.sggnm).to_numpy();local=np.array([f['district']==r.sggnm for f in primary]);area=float(gpd.GeoSeries([r.geometry],crs=4326).to_crs(5179).area.iloc[0]/1e6)
                n=int((local&sel).sum());o=int((local&op).sum());u=int((local&un).sum())
                b=float((kernel[mask]@sel.astype(float)).mean());a=float((kernel[mask]@op.astype(float)).mean());hi=float((kernel[mask]@(op|un).astype(float)).mean())
                district_metrics.append({'district':r.sggnm,'kind':kind,'scenario':key,'n':n,'open':o,'unknown':u,'density':n/area,'open_density':o/area,'potential':b,'access':a,'access_upper':hi,'retention':a/b if b else None})
    df=pd.DataFrame(metrics);dd=pd.DataFrame(district_metrics);ss=pd.DataFrame(summary)
    evening=df[(df.kind=='전체')&(df.scenario=='wed20')].copy()
    positive=evening.potential>0;med=float(evening.loc[positive,'potential'].median())
    def policy(r):
        if r.potential==0:return '등록 공급 부재·자료 확인'
        if r.potential<med:return '공급·입지 추가 조사'
        if r.retention_upper<.5:return '운영시간 개선 후보'
        if r.retention<.5:return '시간정보 확인 우선'
        return '상대적 유지'
    evening['policy']=evening.apply(policy,axis=1)
    csvout('dong_metrics.csv',df);csvout('district_metrics.csv',dd);csvout('scenario_counts.csv',ss);csvout('policy_candidates.csv',evening)
    flat=[]
    for f in fs:flat.append({**{k:v for k,v in f.items() if k not in ['status','sourceIds']},'sourceIds':','.join(map(str,f['sourceIds'])),**f['status']})
    csvout('facility_audit.csv',pd.DataFrame(flat))
    corrs={}
    base=evening[['code','density','potential']].set_index('code')
    for key in SCENARIOS:
        t=df[(df.kind=='전체')&(df.scenario==key)].set_index('code')
        corrs[key]={'density_vs_access_spearman':float(t.density.corr(t.access,method='spearman')),'potential_vs_access_spearman':float(t.potential.corr(t.access,method='spearman'))}
    sensitivity=[]
    for name,half,cut,sel in [('기본',500,2000,np.ones(len(primary),bool)),('거리감쇠1000m',1000,2000,np.ones(len(primary),bool)),('반경1000m',500,1000,np.ones(len(primary),bool)),('24시간 표기 제외',500,2000,np.array([not f['listed24h'] for f in primary])),('과거 안내문구 제외',500,2000,np.array([not f['legacy'] for f in primary]))]:
        kk=2.0**(-distances/half)*(distances<=cut);v=kk@(sel&(states[:,1]==1)).astype(float)
        av=np.array([v[(grid.adm_cd==c).to_numpy()].mean() for c in dong.adm_cd])
        sensitivity.append({'case':name,'n':int(sel.sum()),'wed20_open':int((sel&(states[:,1]==1)).sum()),'mean_grid_access':float(v.mean()),'rank_corr_to_base':float(pd.Series(av).corr(pd.Series(evening.access.to_numpy()),method='spearman'))})
    csvout('sensitivity.csv',pd.DataFrame(sensitivity))
    near=[]
    for i,a in enumerate(primary):
        for j in range(i):
            b=primary[j]
            if a['kind']==b['kind'] and np.linalg.norm(fxy[i]-fxy[j])<50:
                near.append({'id1':a['id'],'name1':a['name'],'id2':b['id'],'name2':b['name'],'distance_m':round(float(np.linalg.norm(fxy[i]-fxy[j])),1)})
    mismatches=[{'id':f['id'],'name':f['name'],'addressDistrict':f['sourceDistrict'],'pointDistrict':f['district']} for f in fs if f['district'] and f['sourceDistrict']!=f['district']]
    audit={'as_of':'2026-10-31','season':'10월의 공휴일 아닌 통상 주간, 특정 주차 미지정','source_total':len(raw),'public_total':sum(r['bk_cd_name']=='공공체육시설' for r in raw),'selected_rows':len(selected),'unique':len(fs),'closed_records':sum(f['state']!='운영' for f in fs),'outside_or_missing':[f['id'] for f in fs if f['dong'] is None],'primary':len(primary),'district_count':len(set(f['district'] for f in primary)),'dong_count':len(dong),'grid_count':len(grid),'duplicates':duplicates,'near_same_kind':near,'district_mismatches':mismatches,'correlations':corrs,'policy_median_potential':med,'policy_counts':dict(Counter(evening.policy)),'sensitivity':sensitivity,'listed24h':sum(f['listed24h'] for f in primary),'legacy':sum(f['legacy'] for f in primary),'free_explicit':sum(f['free'] for f in primary)}
    audit['coordinate_flag_excluded']=[f['id'] for f in fs if f['state']=='운영' and f['district'] and f['coordinateFlag']]
    audit['active_missing_outside']=sum(f['state']=='운영' and f['dong'] is None for f in fs)
    dump(OUT/'audit.json',audit)
    # Browser coordinates and calculation results are packed together; file:// works too.
    simple=dg.copy();simple.geometry=simple.geometry.simplify(35,preserve_topology=True)
    geo=json.loads(simple.to_crs(4326)[['adm_cd','adm_nm','sggnm','geometry']].to_json())
    case_rows,case_contributions,case_paragraphs=build_cases(evening,primary,W,dong)
    csvout('case_studies.csv',case_rows);csvout('case_contributions.csv',case_contributions)
    payload={'case_studies':records(case_rows),'case_contributions':records(case_contributions),'case_paragraphs':case_paragraphs,'audit':audit,'facilities':fs,'metrics':records(df),'districts':records(dd),'summary':summary,'policies':records(evening),'geo':geo,'kinds':KINDS,'scenarios':{k:v[0] for k,v in SCENARIOS.items()}}
    dump(DIST/'data/results.json',payload)
    (DIST/'data/results.js').write_text('window.RESEARCH_DATA='+json.dumps(payload,ensure_ascii=False,allow_nan=False,separators=(',',':'))+';',encoding='utf-8')
    make_charts(dong,df,dd,ss,audit)
    make_case_charts(case_rows,primary,DIST/'figures')
    print(json.dumps({k:v for k,v in audit.items() if k not in ['near_same_kind','district_mismatches','duplicates']},ensure_ascii=False,indent=2))
    return payload

def make_charts(dong,df,dd,ss,audit):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    available={f.name for f in font_manager.fontManager.ttflist}
    font=next((f for f in ['Malgun Gothic','Noto Sans CJK KR','NanumGothic'] if f in available),'DejaVu Sans')
    plt.rcParams.update({'font.family':font,'axes.unicode_minus':False,'figure.dpi':150,'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'#ffffff','figure.facecolor':'#ffffff','axes.facecolor':'#ffffff'})
    colors=['#b9470b','#fbd6b8','#dedede'];t=ss[ss.kind=='전체']
    fig,ax=plt.subplots(figsize=(9,4.8));left=np.zeros(len(t))
    for col,label,color in zip(['open','closed','unknown'],['운영시간 내','운영시간 외','확인 불가'],colors):
        ax.barh(t.label,t[col],left=left,label=label,color=color,height=.54)
        for i,(v,l) in enumerate(zip(t[col],left)):
            if v:ax.text(l+v/2,i,str(v),ha='center',va='center',color='white' if col=='open' else '#252525',fontsize=10)
        left+=t[col].to_numpy()
    ax.invert_yaxis();ax.set_xlabel('등록 시설 수(개)');ax.set_title('시간대별 시설 운영 상태',loc='left',weight='bold',pad=20);ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,-.18),frameon=False)
    fig.tight_layout();fig.savefig(DIST/'figures/scenario_counts.png',bbox_inches='tight');fig.savefig(DIST/'figures/scenario_counts.svg',bbox_inches='tight');plt.close(fig)
    ev=df[(df.kind=='전체')&(df.scenario=='wed20')];sun=df[(df.kind=='전체')&(df.scenario=='sun14')]
    fig,axs=plt.subplots(1,3,figsize=(16,6))
    for ax,(vals,title) in zip(axs,[(ev.potential,'시간 미반영 잠재 접근성'),(ev.access,'수요일 20시'),(sun.access,'일요일 14시')]):
        g=dong.copy();g['v']=vals.to_numpy();g.plot(column='v',ax=ax,cmap='Greys',vmin=0,vmax=float(ev.potential.quantile(.98)),linewidth=.12,edgecolor='white',legend=True,legend_kwds={'shrink':.6});ax.axis('off');ax.set_title(title,fontsize=13,weight='bold')
    fig.suptitle('시간대별 공공체육시설 접근성 비교',x=.04,ha='left',weight='bold',fontsize=19)
    fig.text(.04,.04,'단위: 거리 가중 시설 수 | 500m 격자·반감거리500m·직선거리2km | 미확정 시간의 기여 제외',fontsize=10)
    fig.savefig(DIST/'figures/access_maps.png',bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.5,5.5));ax.scatter(ev.density,ev.access,s=20,c='#d75a26',alpha=.65,edgecolors='none');ax.set(xlabel='등록 시설 밀도(개/km²)',ylabel='수요일20시 접근성(거리 가중 시설 수)',title=f"시설 밀도와 야간 접근성의 관계 · ρ={audit['correlations']['wed20']['density_vs_access_spearman']:.3f}");fig.tight_layout();fig.savefig(DIST/'figures/density_access.png',bbox_inches='tight');plt.close(fig)
    p=ss.pivot(index='kind',columns='scenario',values='open').reindex(KINDS);fig,ax=plt.subplots(figsize=(9,4.8));p.rename(columns={k:v[0] for k,v in SCENARIOS.items()}).plot.bar(ax=ax,color=['#e8792a','#b9470b','#f4ac75','#fbd6b8'],width=.8);ax.set(xlabel='',ylabel='운영시간 내 등록 시설 수(개)',title='종목·시간대별 운영시간 내 시설 수');ax.tick_params(axis='x',rotation=0);ax.legend(fontsize=9,frameon=False);fig.tight_layout();fig.savefig(DIST/'figures/by_sport.png',bbox_inches='tight');plt.close(fig)

if __name__=='__main__':main()
