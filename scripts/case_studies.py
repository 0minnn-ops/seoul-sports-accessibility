"""Reproducible district examples; all evidence comes from the frozen inputs."""
import numpy as np
import pandas as pd


def build(evening, primary, W, dong):
    ranked = evening.copy()
    for metric in ['density', 'access']:
        ranked[metric + '_rank'] = ranked[metric].rank(method='min', ascending=False).astype(int)
    # Deliberate contrast cases, not a representative or causal sample.
    codes = ['11220580', '11170620', '11220610', '11120570', '11140690', '11120710']
    labels = ['밀도 최고', '저녁 접근성 최고', '동 내부 0개·주변 공급 높음', '동 내부 0개·주변 공급 낮음', '밀도 높음·저녁 감소', '넓은 면적·낮은 밀도']
    rows, contributions = [], []
    opened = np.array([f['status']['wed20'] == 1 for f in primary])
    for code, label in zip(codes, labels):
        r = ranked.loc[ranked.code == code].iloc[0].to_dict()
        i = dong.index[dong.adm_cd == code][0]
        weighted = W[i] * opened
        inside = np.array([f['dong'] == code for f in primary])
        r.update(case=label, internal_access=float(weighted[inside].sum()), external_access=float(weighted[~inside].sum()))
        r['external_share'] = r['external_access'] / r['access'] if r['access'] else None
        assert np.isclose(r['internal_access'] + r['external_access'], r['access'])
        rows.append(r)
        for j in np.argsort(-weighted)[:5]:
            if weighted[j] <= 0:
                continue
            f = primary[j]
            contributions.append(dict(case_code=code, case_name=r['name'], facility_id=f['id'], facility_name=f['name'], facility_dong=f['dongName'], facility_district=f['district'], contribution=float(weighted[j]), outside=bool(not inside[j]), url=f['url']))
    byname = {r['name']: r for r in rows}
    b, g, m, j = [byname[n] for n in ['방배본동', '구산동', '망원1동', '진관동']]
    top = [x for x in contributions if x['case_name'] == '방배본동'][:3]
    top_text = ', '.join(x['facility_name'] + '(' + x['facility_dong'] + ')' for x in top)
    paragraphs = [
        dict(title='행정경계 외부 시설의 접근성 기여', text=f"방배본동과 구산동은 모두 분석 표본의 동 내부 시설이 0개여서 밀도가 0이다. 그러나 수요일 20시 접근성은 각각 {b['access']:.2f}, {g['access']:.2f}로 다르다. 방배본동의 값은 전부 동 밖 시설에서 오며, 기여가 큰 시설은 {top_text}이다. 행정경계 안의 수만으로 주변 공급을 판단하면 이 차이가 사라진다. 다만 방배본동은 계산 격자점이 {b['grid_n']}개여서 위치 선택에 민감하며, 직선거리 모형이 실제 보행 연결성을 보장하지 않는다."),
        dict(title='공원·복합운동장의 종목시설 집중', text="반포2동의 10개 항목 중 5개는 반포종합운동장, 3개는 반포한강공원, 2개는 서초구민체육센터 이름으로 등록되어 있다. 높은 밀도는 10개의 독립적인 운동 거점보다 몇몇 거점에 여러 종목이 모인 구조를 반영한다. 고척2동도 7개 중 4개가 고척근린공원 이름의 종목시설이며, 이 4개는 원문에 24시간으로 표기되어 있다. 따라서 저녁 접근성 1위라는 결과를 이용 편의나 서비스 품질 1위로 읽을 수는 없다. 공원·체육거점의 복합 이용이라는 해석은 시설명과 위치 자료에 근거하며, 토지이용 면적이나 수용력을 측정한 결과는 아니다."),
        dict(title='한강공원 시설의 계절별 운영시간', text=f"망원1동은 밀도 {m['density']:.2f}개/km²로 427개 동 중 {m['density_rank']}위지만, 저녁 접근성은 {m['access']:.2f}로 {m['access_rank']}위다. 잠재 접근성 {m['potential']:.2f} 대비 저녁 접근성 범위는 {m['access']:.2f}~{m['access_upper']:.2f}, 유지율은 {100*m['retention']:.1f}~{100*m['retention_upper']:.1f}%이다. 동 내부 5개 중 망원한강공원 농구장·축구장·테니스장은 10~3월 07~17시로 표기되어 20시에 시간 외이며, 수영장은 과거 개장예정 안내 때문에 미확정이다. 수변 공원에 여러 종목이 모여 있어도 계절별 시간 제약이 겹치면 저녁 공급이 줄어드는 사례이다. 야간 조명이나 소음이 단축 운영의 원인인지는 이 자료로 확인하지 못했다."),
        dict(title='행정구역 면적과 인구 비가중 평균의 영향', text=f"진관동은 분석 시설 {j['n']}개, 경계 면적 {j['area_km2']:.2f}km²로 밀도가 {j['density']:.2f}개/km²이다. 잠재 접근성과 저녁 접근성은 모두 {j['access']:.2f}로, 이 모형에서는 저녁 폐쇄보다 기본적인 시설 배치·행정구역 범위의 영향이 먼저 드러난다. {j['grid_n']}개 계산지점을 인구와 무관하게 평균하므로 사람이 적은 공간도 같은 비중으로 반영한다. 따라서 낮은 값을 주민 모두의 시설 부족으로 해석해서는 안 된다. 산지·주거지의 실제 비중과 시설 주변 인구를 확인하려면 토지피복·용도지역·인구 자료를 추가로 결합해야 한다.")
    ]
    visuals = [
        ('case_external.png', '동 내부 시설이 모두 0개여도 주변 공급에 따라 저녁 접근성이 다르다.', '방배본동은 계산지점 1개로 산출되어 위치 선택에 민감하다.'),
        ('case_clusters.png', '반포2동의 10개 종목시설은 세 시설명 그룹에 집중되어 있다.', '시설명 기준의 분류이며 독립 건물 수·수용력을 뜻하지 않는다.'),
        ('case_mangwon.png', f"망원1동은 밀도 {m['density_rank']}위지만 저녁 접근성은 {m['access_rank']}위다. 한강공원 3개 종목시설은 10월 20시에 시간 외다.", '회색 구간은 미확정 시설을 개방으로 가정할 때 추가되는 기여다.'),
        ('case_jingwan.png', '진관동은 저녁에도 잠재 접근성이 유지된다. 낮은 값은 시설 배치와 집계 범위를 함께 검토해야 한다.', f"{j['grid_n']}개 계산지점의 인구 비가중 평균이며 주민 평균 경험을 뜻하지 않는다.")
    ]
    for paragraph, (figure, summary, note) in zip(paragraphs, visuals):
        paragraph.update(figure=figure, summary=summary, note=note)
    return pd.DataFrame(rows), pd.DataFrame(contributions), paragraphs


def make_charts(rows, primary, target):
    """Four compact figures using the same case values and frozen facility list."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    c = rows.set_index('name')
    orange, pale, gray = '#b9470b', '#fbd6b8', '#dedede'

    def finish(fig, ax, filename):
        ax.spines[['top', 'right', 'left']].set_visible(False)
        ax.tick_params(axis='y', length=0, pad=10)
        ax.set_axisbelow(True)
        ax.grid(axis='x', color='#eeeeee', linewidth=.7)
        fig.tight_layout(pad=1.5)
        fig.savefig(target / filename, bbox_inches='tight', facecolor='white')
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 3.5))
    vals = [c.loc[name, 'access'] for name in ['방배본동', '구산동']]
    ax.barh([1, 0], vals, color=orange, height=.42)
    for y, value in zip([1, 0], vals):
        ax.text(value + .08, y, f'{value:.2f}', va='center', fontsize=13, weight='bold')
    ax.set(yticks=[1, 0], yticklabels=['방배본동\n동 내부 0개', '구산동\n동 내부 0개'], xlim=(0, 4.1), ylim=(-.65, 1.65), xlabel='수요일 20시 접근성 · 거리 가중 시설 수')
    finish(fig, ax, 'case_external.png')

    local = [f for f in primary if f['dongName'] == '반포2동']
    names = ['반포종합운동장', '반포한강공원', '서초구민체육센터']
    counts = [sum(f['name'].startswith(name) for f in local) for name in names]
    assert sum(counts) == int(c.loc['반포2동', 'n'])
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.barh([2, 1, 0], counts, color=[orange, '#e8792a', pale], height=.48)
    for y, value in zip([2, 1, 0], counts):
        ax.text(value + .12, y, f'{value}개', va='center', fontsize=13, weight='bold')
    ax.set(yticks=[2, 1, 0], yticklabels=names, xlim=(0, 6), ylim=(-.65, 2.65), xlabel='반포2동 등록 종목시설 수 · 총 10개')
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    finish(fig, ax, 'case_clusters.png')

    m = c.loc['망원1동']
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.barh(1, m.potential, color=pale, height=.42)
    ax.barh(0, m.access, color=orange, height=.42)
    ax.barh(0, m.access_upper - m.access, left=m.access, color=gray, height=.42, label='미확정 기여')
    ax.text(m.potential + .07, 1, f'{m.potential:.2f}', va='center', fontsize=12)
    ax.text(m.access_upper + .07, 0, f'{m.access:.2f}~{m.access_upper:.2f}', va='center', fontsize=12)
    ax.set(yticks=[1, 0], yticklabels=['시간 미반영', '수요일 20시'], xlim=(0, m.potential * 1.22), ylim=(-.65, 1.65), xlabel='망원1동 접근성 · 거리 가중 시설 수')
    ax.legend(loc='upper right', frameon=False, fontsize=10)
    finish(fig, ax, 'case_mangwon.png')

    j = c.loc['진관동']
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.barh([1, 0], [j.potential, j.access], color=[pale, orange], height=.42)
    for y, value in zip([1, 0], [j.potential, j.access]):
        ax.text(value + .015, y, f'{value:.2f}', va='center', fontsize=12)
    ax.set(yticks=[1, 0], yticklabels=['시간 미반영', '수요일 20시'], xlim=(0, .6), ylim=(-.65, 1.65), xlabel='진관동 접근성 · 거리 가중 시설 수')
    ax.set_title(f"{int(j['n'])}개 ÷ {j.area_km2:.2f}km² = {j.density:.2f}개/km²", loc='left', fontsize=13, weight='bold', pad=16)
    finish(fig, ax, 'case_jingwan.png')
