#!/usr/bin/env python3
"""Apply the user-approved reference layout after V7.5 integration.
Preserves training algorithms, local storage, profile, signing, and exercise catalog.
"""
from pathlib import Path
import re
base=Path('fitplan/native/app/src/main/assets')
p=base/'app.js'
s=p.read_text(encoding='utf8')

def swap(old,new):
 global s
 assert old in s, f'UI patch anchor missing: {old[:100]}'
 s=s.replace(old,new,1)

def replace_func(a,b,new):
 global s
 left=s.index('function '+a+'(')
 right=s.index('function '+b+'(',left)
 s=s[:left]+new+'\n'+s[right:]

header='''function head(){return `<header class="fp-head"><div class="fp-mark"><span class="barbell-logo">━●━</span><div><div class="fp-title">Fit<span>Plan</span></div><span class="fp-v76-small">개인 맞춤형 운동 코치</span></div></div><button class="btn secondary small" onclick="Fit.go('settings')" aria-label="설정">⚙</button></header>`;}'''
s,n=re.subn(r'function head\(\)\{return `.*?`;\}',lambda m:header,s,count=1,flags=re.S)
assert n==1
nav='''function nav(){const tabs=[['home','⌂','홈'],['work','▰','운동'],['history','▤','기록'],['state','▥','분석']];return `<nav class="tabbar">${tabs.map(([key,ico,label])=>`<button class="${view===key?'active':''}" onclick="Fit.go('${key}')"><span aria-hidden="true">${ico}</span><small>${label}</small></button>`).join('')}</nav>`;}'''
s,n=re.subn(r'function nav\(\)\{return `.*?`;\}',lambda m:nav,s,count=1,flags=re.S)
assert n==1
home=r'''function homeView(){
 const prof=state.profile,active=state.active,hist=state.history||[],program=splitProgram(),split=program.days[state.sessionIndex%program.days.length];
 const now=Date.now(),recent=hist.filter(h=>{const t=Date.parse(h.date||'');return Number.isFinite(t)&&now-t<7*86400000&&now-t>=-86400000});
 const target=Math.max(1,num(prof.days,3)),rate=Math.min(100,Math.round(recent.length/target*100));
 const sets=recent.reduce((n,h)=>n+mainCount(h),0),last=hist[hist.length-1];
 const trend=hist.slice(-4).map(h=>({d:dateLabel(h),v:mainCount(h)}));
 const strength=last?.items?.flatMap(it=>(it.sets||[]).filter(z=>z.done&&!z.warmup&&num(z.actualWeight)>0).map(z=>num(z.actualWeight)))||[];
 const previous=strength.length?Math.max(...strength):null;
 return `${head()}<div class="fp-v76-logo">Fit<em>Plan</em> <span class="pill">V7.6</span></div>
 <p class="fp-v76-muted mt8">운동할수록 더 정확해지는 적응형 운동 플랜</p>
 <div class="card hero fp-v76-hero"><div class="fp-v76-head">오늘의 운동 <span class="pill grey">개인별 자동 설계</span></div>
 <h1>${esc(active?.splitName||split[0])}</h1><span class="pill grey">◷ 약 ${active?.adjustedPredictedMinutes||prof.duration}분 · ${active?.items?.length||'추천'}종목 · ${esc(program.label)}</span>
 <button class="btn primary full" onclick="Fit.go('${active?'work':'ready'}')">▶ ${active?'운동 이어하기':'운동 시작하기'}</button></div>
 <div class="card"><div class="fp-v76-head">▥ 주간 진행 <span class="fp-v76-small">${recent.length} / ${target}회</span></div><div class="fp-v76-progress"><i style="width:${rate}%"></i></div>
 <div class="fp-v76-ministats"><div>운동 횟수<span class="value">${recent.length}회</span></div><div>완료 본세트<span class="value">${sets}세트</span></div><div>주간 목표<span class="value">${rate}%</span></div></div></div>
 <div class="card"><div class="fp-v76-head">▥ 주간 운동 추세 <button class="btn tiny secondary" onclick="Fit.go('state')">상세 분석 ›</button></div>
 ${svgGraph(trend,'최근 운동별 완료 본세트','세트')}
 <div class="fp-v76-row"><span>◉ 누적 운동 완료</span><strong>${hist.length}회</strong></div><div class="fp-v76-row"><span>▰ 직전 운동 최고 중량</span><strong>${previous===null?'기록 없음':formatWeight(previous)+'kg'}</strong></div></div>
 <div class="card"><div class="fp-v76-head">▦ 다음 운동 계획</div><div class="fp-v76-summary"><div><div class="fp-v76-small">추천 루틴</div><strong>${esc(active?.splitName||split[0])}</strong><div class="fp-v76-muted">${active?.items?.length||'자동 선택'}종목 · 약 ${active?.timeLimit||prof.duration}분</div></div><button class="btn small outline" onclick="Fit.go('${active?'work':'ready'}')">보기 ›</button></div></div>
 <div class="fp-v76-ministats mt16"><div onclick="Fit.go('ready')">▦<span class="value">일정 관리</span></div><div onclick="Fit.go('work')">↻<span class="value">운동 기록</span></div><div onclick="Fit.go('state')">◎<span class="value">성과 분석</span></div></div>
 <button class="btn outline full mt16" onclick="Fit.programPreview()">전체 운동 계획 보기</button>`;
}
'''
replace_func('homeView','readyView',home)

# Keep every existing set editor, workout section, safe alternative and 31-exercise flow.
old='''return `${head()}<div class="eyebrow">TODAY · ${esc(s.program)}</div><h1>${esc(s.splitName)}</h1>
 <div class="card summary-card"><div class="row"><div><span class="muted tiny">운동 목표 시간</span><h2>${s.timeLimit}분</h2></div><div><span class="muted tiny">본운동 종목</span><h2>${s.items.length}개</h2></div><div><span class="muted tiny">전체 진행률</span><h2>${done}/${total}</h2></div></div><div class="progressrail"><div style="width:${p}%"></div></div>
 <button class="btn primary full playbig" onclick="Fit.play('all')">▶ 운동 시작 · 이어하기</button></div>'''
new='''return `${head()}<div class="fp-v76-workhead"><div class="fp-v76-head">운동 진행 <span>${done} / ${total} (${p}%)</span></div><h2>${esc(s.splitName)}</h2><p class="fp-v76-muted">${s.items.length}종목 · 약 ${s.adjustedPredictedMinutes||s.timeLimit}분 · 목표 RIR 2</p><div class="fp-v76-progress"><i style="width:${p}%"></i></div></div>
 <div class="card summary-card"><div class="row"><div><span class="muted tiny">운동 목표 시간</span><h2>${s.timeLimit}분</h2></div><div><span class="muted tiny">본운동 종목</span><h2>${s.items.length}개</h2></div><div><span class="muted tiny">전체 진행률</span><h2>${done}/${total}</h2></div></div>
 <button class="btn primary full playbig" onclick="Fit.play('all')">▶ 운동 시작 · 이어하기</button></div>'''
swap(old,new)

# Add data-grounded analytics cards and retain expert views in a disclosure.
oldstate=s[s.index('function stateView(){'):s.index('function v7StateInsights(){')]
legacy=oldstate.replace('function stateView(){','function detailedStateView(){',1)
state=r'''function stateView(){const hist=state.history||[],recent=hist.slice(-12),cnt=recent.reduce((n,h)=>n+mainCount(h),0);
 const completed=hist.length,weightSeries=hist.filter(h=>num(h.feedback?.weight||h.bodyweight)>0).slice(-4).map(h=>({d:dateLabel(h),v:num(h.feedback?.weight||h.bodyweight)}));
 const setSeries=recent.slice(-4).map(h=>({d:dateLabel(h),v:mainCount(h)}));
 const diff=recent.filter(h=>num(h.feedback?.difficulty||h.difficulty)>0);
 const avg=diff.length?(diff.reduce((a,h)=>a+num(h.feedback?.difficulty||h.difficulty),0)/diff.length).toFixed(1):null;
 const planned=recent.reduce((n,h)=>n+(h.items||[]).reduce((a,it)=>a+(it.sets||[]).filter(z=>!z.warmup).length,0),0);
 const rate=planned?Math.round(cnt/planned*100):null;
 return `${head()}<h1>분석</h1><div class="seg mt16">${[['weight','체중'],['difficulty','강도'],['duration','운동 시간'],['sets','본세트']].map(([key,label])=>`<button class="${chartKey===key?'active':''}" onclick="Fit.graph('${key}')">${label}</button>`).join('')}</div>
 <div class="card fp-v76-analytics"><div class="fp-v76-head">주요 지표 변화 <span class="pill">최근 ${recent.length}회 기록</span></div>
 <div class="fp-v76-analysis-row"><span>▰ 완료한 총 본세트</span><strong>${cnt}세트</strong></div>
 <div class="fp-v76-analysis-row"><span>✓ 운동 완료율</span><strong>${rate===null?'자료 부족':rate+'%'}</strong></div>
 <div class="fp-v76-analysis-row"><span>▥ 기록된 운동 횟수</span><strong>${completed}회</strong></div>
 <div class="fp-v76-analysis-row"><span>◷ 평균 체감 강도</span><strong>${avg===null?'자료 부족':avg+'/10'}</strong></div></div>
 <div class="fp-v76-grid2 mt16"><div class="card"><div class="fp-v76-small">운동 완료율</div><strong class="bigger">${rate===null?'—':rate+'%'}</strong><div class="fp-v76-progress mt12"><i style="width:${rate||0}%"></i></div></div><div class="card"><div class="fp-v76-small">최근 운동</div><strong class="bigger">${recent.length}회</strong><div class="fp-v76-muted">총 ${cnt}세트</div></div></div>
 <div class="sectionhead"><h2>최근 훈련 변화</h2></div>${svgGraph(chartKey==='weight'?weightSeries:chartKey==='sets'?setSeries:recent.slice(-4).map(h=>({d:dateLabel(h),v:chartKey==='duration'?num(h.durationMin):num(h.feedback?.difficulty||h.difficulty)})),chartKey==='weight'?'체중 변화':chartKey==='duration'?'운동 소요 시간':chartKey==='difficulty'?'체감 난이도':'운동량 추세',chartKey==='weight'?'kg':chartKey==='duration'?'분':chartKey==='difficulty'?'점':'세트')}
 <div class="card"><div class="fp-v76-head">훈련 분석</div><div class="fp-v76-ministats"><div>총 운동<span class="value">${completed}회</span></div><div>최근 본세트<span class="value">${cnt}세트</span></div><div>체감 강도<span class="value">${avg===null?'—':avg+'/10'}</span></div></div></div>
 <div class="card"><div class="fp-v76-head">개인 코치 분석</div><p class="fp-v76-muted">${hist.length<3?'운동 기록을 더 쌓으면 개인별 변화 추세와 중량 조절 근거를 확인할 수 있습니다.':'실제 완료 기록을 바탕으로 다음 운동의 회복·중량·운동량을 조정합니다.'}</p></div>
 <details class="fp-v76-detail"><summary>상세 분석 및 회복·근육별 지표 보기</summary>${detailedStateView().replace(head(),'')}</details>`;
}
'''
s=s.replace(oldstate,legacy+state,1)

# Exact circular gauge with a large central clock and functional existing controls.
old='<div class="mint-ring-core"><div class="mint-clock-label">${rest?\'휴식 남은 시간\':\'운동 경과\'}</div><div class="mint-ring-clock" id="player-clock">${shortDuration(clock)}</div></div>'
new='<div class="mint-ring-core"><div class="fp-v76-timer-icon">◴</div><div class="mint-clock-label">${rest?\'휴식 타이머\':\'운동 타이머\'}</div><div class="mint-ring-clock" id="player-clock">${shortDuration(clock)}</div><div class="fp-v76-total">${rest?\'총 \'+shortDuration(p.restSeconds):\'운동 진행 중\'}</div></div>'
assert s.count(old)>=1,(s.count(old),'ring templates changed')
s=s.replace(old,new)
# Rest gauge same SVG r=108: existing tick updater updates live arc.
swap('''<h1 class="player-title">${esc(cur.title)}</h1>
   ${ring}''','''<div class="fp-v76-workhead" style="width:100%;margin:0 0 4px"><div class="fp-v76-head">${esc(cur.title)} <span class="fp-v76-small">${setLabel}</span></div><p class="fp-v76-muted">${esc(phase)} · 개인 목표에 따른 진행</p></div>
   ${ring}''')
swap('''<div class="mint-target"><strong>${weightLabel}</strong><span>${cur.ref.targetReps}${isTimed(e)?'초':'회'}</span></div>''','''<div class="mint-target"><div><span class="fp-v76-small">다음 중량</span><strong>${weightLabel}</strong></div><div><span class="fp-v76-small">세트 목표</span><strong>${cur.ref.targetReps}${isTimed(e)?'초':'회'}</strong></div></div>''')
swap('''${rest?`<div class="mint-rest-actions"><button onclick="Fit.extendRest(30)">휴식 +30초</button></div>`:''}''','''${rest?`<div class="mint-rest-actions"><button onclick="Fit.extendRest(30)">⊕ +30초</button></div>`:''}''')

p.write_text(s,encoding='utf8')
(base/'style.css').write_text((base/'style.css').read_text(encoding='utf8')+'\n'+Path('fitplan/neon-v76.css').read_text(encoding='utf8'),encoding='utf8')
print('FitPlan V7.6 reference UI applied. Existing coach data and timers preserved.')