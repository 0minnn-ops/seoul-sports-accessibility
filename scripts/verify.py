"""Checks for source integrity, time semantics, aggregation and spatial units."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from schedules import scenario_states,at,ranges

ROOT=Path(__file__).resolve().parents[1]
def main():
    manifest=json.loads((ROOT/'data/raw/source_manifest.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((ROOT/'data/raw/seoul_sports_20261031.json').read_bytes()).hexdigest()==manifest['raw_sha256']
    raw={r['ft_idx']:r for r in json.loads((ROOT/'data/raw/seoul_sports_20261031.json').read_text(encoding='utf-8'))['DATA']}
    assert at(ranges('09:00~20:00'),20)==0
    assert at(ranges('09:00~20:00'),14)==1
    assert at(ranges('연중무휴'),20)==-1
    for fid,expected in {828:[1,1,1,0],743:[1,1,1,1],646:[0,1,0,0],797:[-1,-1,1,1],1010:[0,1,1,1],1008:[1,1,1,0],791:[1,1,1,0],1433:[1,0,1,1],948:[1,1,1,1]}.items():
        assert list(scenario_states(raw[fid])[0])==expected,(fid,scenario_states(raw[fid]))
    p=json.loads((ROOT/'dist/data/results.json').read_text(encoding='utf-8'));a=p['audit']
    f=[x for x in p['facilities'] if x['eligible']];df=pd.DataFrame(p['metrics']);s=pd.DataFrame(p['summary'])
    assert len(f)==a['primary'] and len({x['id'] for x in f})==len(f)
    assert a['unique']==a['closed_records']+a['active_missing_outside']+len(a['coordinate_flag_excluded'])+a['primary']
    assert len(df)==427*7*4
    for r in p['summary']:
        t=df[(df.kind==r['kind'])&(df.scenario==r['scenario'])]
        assert len(t)==427 and t.code.is_unique
        assert t.n.sum()==r['total'] and t.open.sum()==r['open'] and t.unknown.sum()==r['unknown']
        assert r['open']+r['unknown']+r['closed']==r['total']
        np.testing.assert_allclose(t.density*t.area_km2,t.n)
        np.testing.assert_allclose(t.open_density*t.area_km2,t.open)
        assert (t.access>=-1e-9).all() and (t.access_upper>=t.access-1e-9).all() and (t.potential>=t.access_upper-1e-9).all()
    for sc in p['scenarios']:
        t=df[df.scenario==sc];all_=t[t.kind=='전체'].set_index('code');parts=t[t.kind!='전체'].groupby('code')[['n','open','unknown','access','potential']].sum()
        np.testing.assert_allclose(all_.loc[parts.index,parts.columns],parts,atol=1e-8)
    # Independently reconstruct one dong's lattice and kernel from geometries.
    dong=gpd.read_file(ROOT/'data/boundaries/seoul_admdong_20261001.geojson').to_crs(5179)
    target=dong[dong.adm_nm.str.endswith('자양3동')].iloc[0]
    minx,miny,maxx,maxy=target.geometry.bounds
    grid=[Point(x,y) for y in np.arange(np.floor(miny/500)*500+250,maxy,500) for x in np.arange(np.floor(minx/500)*500+250,maxx,500) if target.geometry.contains(Point(x,y))]
    fp=gpd.GeoSeries([Point(x['lon'],x['lat']) for x in f],crs=4326).to_crs(5179)
    direct=[]
    for g in grid:
        direct.append(sum(2**(-g.distance(pt)/500) for x,pt in zip(f,fp) if g.distance(pt)<=2000 and x['status']['wed20']==1))
    val=df[(df.code==target.adm_cd)&(df.kind=='전체')&(df.scenario=='wed20')].iloc[0]
    np.testing.assert_allclose(np.mean(direct),val.access,atol=1e-8)
    cand=pd.DataFrame(p['policies']);q=cand[cand.policy=='운영시간 개선 후보']
    assert (q.potential>=a['policy_median_potential']-1e-8).all() and (q.retention_upper<.5).all()
    for item in p['facilities']:
        if item['eligible']:assert not item['coordinateFlag'] and item['state']=='운영'
    print('PASS: source hash, time semantics, all 28 strata, spatial bounds, type additivity, independent distance calculation, policy thresholds')

if __name__=='__main__':main()
