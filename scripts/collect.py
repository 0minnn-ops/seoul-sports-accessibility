"""Download public Seoul sports data and published point coordinates. No credentials."""
from pathlib import Path
import concurrent.futures, hashlib, json, re, time
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
KINDS = ['수영장','배드민턴장','테니스장','축구장','풋살장','농구장']
DOWNLOAD = 'https://datafile.seoul.go.kr/bigfile/iot/sheet/json/download.do'
FORM = dict(srvType='S', infId='OA-21779', serviceKind='1', pageNo='1', ssUserId='SAMPLE_VIEW', strWhere='', strOrderby='', filterCol='', txtFilter='')

def main():
    raw = ROOT/'data/raw'; raw.mkdir(parents=True,exist_ok=True)
    path = raw/'seoul_sports_20261031.json'
    if not path.exists():
        r=requests.post(DOWNLOAD,data=FORM,timeout=60);r.raise_for_status()
        assert 'DATA' in r.json();path.write_bytes(r.content)
    rows=json.loads(path.read_text(encoding='utf-8'))['DATA']
    chosen=[r for r in rows if r['bk_cd_name']=='공공체육시설' and r['ft_kind_name'] in KINDS]
    cache=raw/'details';cache.mkdir(exist_ok=True)
    def one(row):
        fid=row['ft_idx']; p=cache/f'{fid}.html'
        url=f'https://sports.seoul.go.kr/main/facilities/facilities_view.do?ft_idx={fid}'
        if not p.exists():
            for trial in range(3):
                try:
                    res=requests.get(url,timeout=35);res.raise_for_status();p.write_bytes(res.content);break
                except requests.RequestException:
                    if trial==2:return {'id':fid,'url':url,'error':'request_failed'}
                    time.sleep(1+trial)
            time.sleep(.25)
        html=p.read_text(encoding='utf-8')
        lat=re.search(r'var\s+lat\s*=\s*[\"\x27]([^\"\x27]*)',html)
        lon=re.search(r'var\s+lng\s*=\s*[\"\x27]([^\"\x27]*)',html)
        soup=BeautifulSoup(html,'html.parser')
        title=soup.find('meta',property='og:title')
        try: coord=[float(lon.group(1)),float(lat.group(1))]
        except (ValueError,AttributeError):coord=None
        return {'id':fid,'url':url,'coordinates':coord,'page_title':title.get('content') if title else None,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    output=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        for i,item in enumerate(ex.map(one,chosen),1):
            output.append(item)
            if i%50==0:print(f'Coordinates collected: {i}/{len(chosen)}',flush=True)
    (raw/'coordinates.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    meta={'downloaded_kst':datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),'catalog':'https://data.seoul.go.kr/dataList/OA-21779/S/1/datasetView.do','download_url':DOWNLOAD,'download_method':'POST','form':FORM,'raw_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'raw_records':len(rows),'public_records':sum(r['bk_cd_name']=='공공체육시설' for r in rows),'selected_kinds':KINDS,'selected_records':len(chosen),'coordinate_records':sum(bool(o.get('coordinates')) for o in output),'license':'공공누리 제1유형: 서울특별시 출처표시, 가공 가능','note':'포털 갱신일은 개별 시설 현장검증일이 아니다. 좌표는 같은 시설 ID의 공식 상세페이지 지도 변수에서 추출.'}
    (raw/'source_manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(meta,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
