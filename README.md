# 서울 공공체육시설의 시간대별 접근성

스마트시티 융합기술세미나 과제3. 서울시 공공체육시설의 등록 밀도와 운영시간 반영 거리 접근성을 비교한다.

## 실행

Python 3.11 이상에서 `pip install -r requirements.txt`를 실행한 뒤 이 폴더에서 아래 명령을 실행한다.

```sh
python scripts/analyze.py
python scripts/verify.py
python scripts/build_notebook.py
```

`analysis.ipynb`는 실행 결과가 포함되어 있다. ZIP을 풀고 이 폴더를 작업 디렉터리로 사용해야 한다. 분석·검증·노트북 실행은 포함 자료만 사용하며 인증키나 인터넷이 필요하지 않다. 수집을 다시 하려면 `scripts/collect.py`를 사용하되, 기존 날짜의 동결 원자료를 먼저 별도 보관하고 새 연구용 파일명·기준일을 지정한다.

웹보고서는 `dist/index.html`을 열어 볼 수 있다. 서버를 사용하려면 `python -m http.server 8769 --directory dist`를 실행하고 `http://127.0.0.1:8769/`로 접속한다. 지도는 외부 타일·API 키를 사용하지 않는다. 다운로드 자료는 `dist/downloads`에 있다.

## 분석 범위

- 주자료: 서울 열린데이터광장 OA-21779, 2026.10.31 수집. 원본의 ‘공공체육시설’ 분류에서 수영장·배드민턴장·테니스장·축구장·풋살장·농구장 선택.
- 좌표: 동일 시설 ID의 서울시 생활체육포털 공개 상세페이지 지도 변수. 자료 최신성 또는 실제 출입구 위치의 현장 검증을 뜻하지 않는다.
- 경계: 통계청 SGIS 기반 vuski/admdongkor 2026.10.01, CC BY 4.0. 기존 별도 과제에서 수집한 외부 공개 경계를 재사용했으며 수업 배포 데이터를 분석 자료로 사용하지 않았다.
- 500m 격자, 직선거리 반감거리500m, 탐색반경2km, EPSG:5179. 행정동·자치구의 인구 비가중 격자 평균이다.
- 시나리오: 10월의 공휴일 아닌 수요일14시·20시, 토요일14시, 일요일14시. 특정 주차는 정하지 않아 주차별 휴관은 미확정으로 처리한다.
- 집계 단위는 등록된 종목별 시설 항목이며 건물·코트·정원 수가 아니다. 동일 종목·시설명(공백 제거)·주소 중복을 정리하고 휴관·좌표 누락/경계 밖·좌표 의심 항목을 제외한다.

## 해석 주의

운영시간 내 시설 수는 실제 예약 가능 슬롯이나 자유 이용 가능성을 뜻하지 않는다. 미확정 시각을0/1로 두어 접근성 범위를 제시하며, 이 범위는 통계적 신뢰구간이 아니고 위치·등록누락·자료 노후화의 불확실성을 포함하지 않는다. ‘연중무휴’만으로24시간 운영을 추정하지 않는다. 표본의 법적 소유형태, 회원·연령·성별·팀 자격, 가격, 정원, 이용률은 검증·가중하지 않았다.

원본 자료 전체897행 → 공공 분류814행 → 6종399행 → 중복 정리398개 → 휴관26개 제외 → 운영 항목 중 좌표 누락·서울 밖14개 제외 → 위치 의심7개 제외 → 분석351개. 최신 산출값은 `data/processed/audit.json`을 기준으로 한다.

## 파일

- `scripts/schedules.py`: 시각 판정 및 원문 근거를 적은 예외 규칙
- `scripts/analyze.py`: 정제, 공간 결합, 격자, 지표, 민감도, 정적 그림·웹 데이터
- `scripts/verify.py`: 시간 의미, 합계, 지표 경계, 독립 거리 계산 검증
- `scripts/build_notebook.py`: 노트북 실행 및 재현 ZIP 생성
- `data/raw/source_manifest.json`: 출처, 수집시점, 요청방법, SHA-256
- `data/raw/details`: 좌표를 추출한 공식 상세페이지 동결본
- `data/processed/facility_audit.csv`: 전체 후보의 원문, 판정, 제외 사유
- `data/processed/dong_metrics.csv`: 427개 동 × 7종 구분 × 4시각
- `dist/figures`: PNG 및 SVG 그림

## 출처

- 서울시 공공체육시설 정보: https://data.seoul.go.kr/dataList/OA-21779/S/1/datasetView.do (공공누리 제1유형, 서울특별시 출처표시)
- 시설 상세: https://sports.seoul.go.kr/main/facilities/facilities_view.do?ft_idx=시설ID
- 경계: https://github.com/vuski/admdongkor/tree/d5d5a821c8de6cc337d47eeca604d7af76271c9b (SGIS 및 가공자 vuski 표시, CC BY 4.0)
- 보조 검토: https://www.data.go.kr/data/15013117/standard.do 및 https://data.seoul.go.kr/dataList/OA-2266/S/1/datasetView.do
- Leaflet: BSD-2-Clause, `dist/vendor/leaflet/LICENSE`

## 웹 배포

Cloudflare Pages에서 `main` 브랜치를 연결하고 프레임워크는 없음, 빌드 명령은 공란, 출력 디렉터리는 `dist`로 설정한다. 분석을 다시 실행하지 않고 포함된 정적 보고서를 제공한다.
