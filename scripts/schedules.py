"""Auditable scenario coding; 1 listed open, 0 listed closed, -1 unresolved.

Ordinary non-holiday October, unspecified week of month. Never infer Saturday
hours from weekday hours or 24-hour operation from 'open all year'.
"""
import re

SCENARIOS = {'wed14':('수요일 14시',0,14),'wed20':('수요일 20시',0,20),
             'sat14':('토요일 14시',1,14),'sun14':('일요일 14시',2,14)}

def clean(value):
    return re.sub(r'\s+',' ',value or '').strip().replace('～','~').replace('–','~').replace('：',':').replace('24:.00','24:00').replace('09::00','09:00')

def ranges(text):
    found=re.findall(r'(\d{1,2})\s*:\s*(\d{2})\s*[~\-]\s*(\d{1,2})\s*:\s*(\d{2})',text)
    return [(60*int(a)+int(b),60*int(c)+int(d)) for a,b,c,d in found
            if int(a)<24 and int(c)<=24 and int(b)<60 and int(d)<60 and (int(c)<24 or int(d)==0)]

def at(intervals,hour):
    if not intervals:return -1
    return int(any(a <= hour*60 < b for a,b in intervals))

# Overrides below refer only to the frozen source fields, never to assumed live
# schedules. Each value is wed14, wed20, sat14, sun14 and an audit explanation.
OVERRIDES={}
def put(ids,values,reason):
    for fid in ids:OVERRIDES[fid]=(values,reason)

put([764],[-1,-1,1,1],'평일 계절별 운영시간 상이: 정확한 계절별 시각 미기재')
put([815,1244,878,1064],[1,1,-1,-1],'주말 시간 없음/문의/예약 조건; 공휴일 열의 시각을 주말로 전용하지 않음')
put([743],[1,1,1,1],'평일 열에 월~토 06:00~21:50; 주말 열에 일요일 06:00~19:30')
put([646],[0,1,0,0],'매일 13:00~15:00 코트 정비시간 차감, 일요일 휴관')
put([845,852,1056],[1,1,1,1],'휴장 13:00~14:00 종료시각은 개방시간에 포함')
put([1243],[1,-1,1,1],'18시 이후 주민 무료 개방은 종료시각 미기재: 20시 확인 불가')
put([676],[1,-1,1,1],'하절기18시/동절기17시 이후 자유개방 종료시각 미기재')
put([1097],[-1,-1,1,1],'평일 열 09~21시와 별도 안내 월~목06~22시가 충돌: 평일 미확정')
put([997],[1,1,-1,0],'평일 열 토09~18시와 주말 휴관 안내 충돌: 토요일 미확정')
put([1014],[1,1,1,0],'평일 열에 토요일10:00~17:50 별도 명시')
put([950],[1,1,1,-1],'토요일09~17시는 공휴일 열에 명시; 일요일 시각 미기재')
put([963],[1,1,-1,1],'주말 열은 일요일·공휴일만 명시: 토요일 미확정')
put([1189],[1,1,-1,1],'주말 열에 일요일만 명시: 토요일 미확정')
put([1373],[1,1,-1,1],'주말 열에 일요일만 명시: 토요일 미확정')
put([1090],[1,1,-1,-1],'평일 청소13~14시 반영; 주말 시각 미기재')
put([757],[1,1,-1,-1],'주말 열은 휴관일만 기재, 주말 시각 없음')
put([1165],[1,1,-1,-1],'주말 일반 일일이용 불가·주말 시각 없음: 회원 이용 여부 미확정')
put([1029],[-1,-1,-1,-1],'4~9월 시간만 명시; 10월 운영 여부 미확정')
put([1512,1671,1020],[-1,-1,-1,-1],'운영 상태와 개장예정/공사중지/특정기간 문구가 충돌하거나 적용기간 미확정')
put([1010],[0,1,1,1],'평일09~16시는 학교 운동장 사용으로 공공이용 제외')
put([1037],[1,0,1,1],'축구경기07~20시 적용, 조깅트랙 시간 제외')
put([1382,1384,896],[1,0,0,0],'방역12~14시 종료 후 14시 개방, 주말 휴관')
put([870],[1,0,0,0],'수영장 별도 운영09~17시, 주말 휴관')
put([1247],[-1,-1,-1,-1],'방역 휴게 타임의 정확한 시각 미기재')
put([1012],[1,0,1,1],'정비13~14시 차감; 환절기 정비기간은 별도 미검증')
put([910],[1,1,-1,-1],'주말 열에 개시시각 한 시간 변경만 있고 기준 시각 없음')
put([1639],[-1,-1,-1,-1],'야간 조명20시 종료는 시설 개방시간과 같다고 볼 수 없음')
put([1503,919,1065,1241,1455],[-1,-1,-1,-1],'일조·계절에 따른 탄력 운영: 정확한 적용시간 미확정')
put([1604],[1,1,1,-1],'일요일 탄력 운영 명시')
put([797],[-1,-1,1,1],'짝수 주 수요일 휴관; 기준 주차를 특정하지 않아 수요일 미확정')
put([759],[0,0,1,1],'매주 수요일 휴관')
put([671],[1,1,1,-1],'10월 둘째·넷째 주 일요일만 개관: 일요일 주차 미확정')
put([704],[1,1,-1,0],'매월 마지막 토요일 휴관, 일요일 휴관: 토요일 주차 미확정')

OCT_WINTER=[1433,706,708,705,709,1122,1437,1126,1127,1438,898,1518,1508,912,1510,
            1686,1479,993,992,1256,1258,1448,951,787,1021,1022]
put(OCT_WINTER,[1,0,1,1],'명시된 10~3월 운영시간을 10월 시나리오에 적용')
put([965,879,698,1608],[1,0,1,1],'명시된 3/4~10월 운영시간을 적용, 20시는 종료시각 이후')
put([1212],[1,1,1,1],'명시된 10~3월09~22시 적용')
put([1171],[1,1,1,1],'하절기·동절기 모두 해당 시각 개방; 수요일은 월요일 휴관과 무관')
put([831,1495,1611,1612],[1,0,1,1],'계절 구분 월은 없으나 모든 제시 계절 시간표가 네 시각에서 동일한 상태')
put([1073],[1,1,1,1],'10월06~22시 연장 적용')
put([677],[1,1,1,1],'동절기1시간 단축을 적용해도14/20시는 동일하게 개방')
# 861 and 891 retain ordinary 06~22 in October; 1670 ordinary 07~18.
put([861,891],[1,1,1,1],'단축시간 적용월은12~3월 또는12~2월로 10월에 해당 없음')
put([1670],[1,0,1,1],'10월07~18시;11~2월 단축 미적용')
put([778],[1,1,1,-1],'일요일을 휴일로 볼 수 있으나 둘째·넷째 주 휴관으로 일요일 미확정')

def scenario_states(row):
    fid=row['ft_idx']
    if row['ft_operation_name']!='운영':return [0,0,0,0],'원자료 시설운영상태 휴관; 본 분석 제외'
    if fid in OVERRIDES:return OVERRIDES[fid]
    wd,we,info=[clean(row[k]) for k in ['ft_wd_time','ft_we_time','ft_info_time']]
    result=[];reasons=[]
    for key,(label,day,hour) in SCENARIOS.items():
        text=wd if day==0 else we
        if day:
            target='토' if day==1 else '일'
            # Annotated named day clauses, with public holidays kept separate.
            tok=re.sub(r'법정공휴일|공휴일|법정공유일|공유일|법정휴일','HOLIDAY',text)
            tok=re.sub(r'(토요일|일요일)\s*[,]?\s*(?:및\s*)?HOLIDAY',r'\1',tok)
            matches=list(re.finditer(r'(토요일|일요일|토(?=\s|:)|일(?=\s|:)|HOLIDAY)',tok))
            matches=[m for m in matches if not (m.group()=='HOLIDAY' and tok[max(0,m.start()-4):m.start()].strip().endswith('및'))]
            named=[m for m in matches if m.group().startswith(target)]
            if named:
                m=named[0];end=next((n.start() for n in matches if n.start()>m.start()),len(tok))
                clause=tok[m.start():end]
                if re.search(r'휴관|휴무|미운영|정기휴무',clause):value=0
                else:value=at(ranges(clause),hour)
            elif '주말' in tok and re.search(r'주말[^/]*?(휴관|휴무)',tok):value=0
            elif day==2 and re.search(r'일요일.*?(휴관|휴무)',info):value=0
            else:
                first=tok[:matches[0].start()] if matches else tok
                value=at(ranges(first),hour)
            # A month-week schedule cannot be reduced to all Sundays/Saturdays.
            alltext=we+' '+info
            if target+'요일' in alltext and re.search(r'첫|둘|셋|넷|다섯|홀수|짝수|마지막|\d\s*[,/]\s*\d|\d\s*째?\s*주',alltext):
                if target=='일' or (target=='토' and re.search(r'마지막\s*주\s*토',alltext)):value=-1
        else:
            rs=ranges(text)
            value=at(rs,hour) if len(rs)<=1 else -1
        result.append(value)
    return result,'표준 시각 범위·요일·휴관 문구 해석; 미기재/주차 조건은 확인 불가'
