#!/usr/bin/env python3
"""FitPlan V8.1 surgical UI: balanced onboarding, single-line days, exercise help, clean settings.
Do not delete machine records or alter learning models.
"""
from pathlib import Path
import re
p=Path('fitplan/native/app/src/main/assets/app.js')
s=p.read_text('utf8')
def change(old,new):
 global s
 assert old in s, 'V8.1 missing anchor: '+old[:100]
 s=s.replace(old,new,1)

# 1 — Cards: layout handled by CSS. Avoid text-wide replacement or broken UI.
# 2 — Seven weekdays are a single evenly divided grid on small screens.
# Remove only the redundant homescreen widget explanation card within scheduleView.
needle="'<div class=\"card\"><div class=\"fp-v76-head\">'+fpIcon('schedule')+' 홈 화면 위젯</div>'"
a=s.find(needle)
assert a>0,'Home widget instructional card missing'
b=s.find("'<button class=\"btn secondary\" onclick=\"Fit.todayCalendar()\">오늘로 이동</button></div>'",a)
assert b>a,'Home widget card terminator missing'
s=s[:a]+s[b+len("'<button class=\"btn secondary\" onclick=\"Fit.todayCalendar()\">오늘로 이동</button></div>'"):]

# 3 — Click exercise items in workout calendar for existing professional guide and video search.
# For known planned exercises use their id. Unknown names get a guarded search link.
anchor="function scheduleView(){"
assert anchor in s
addition=r"""
function fpGuideByName(name){
 const e=CATALOG.find(x=>x.n===name||x.en===name);
 if(e){guide(e.id);return;}
 modal={type:'exerciseLookup',exerciseName:String(name||'운동')};render();
}
"""
s=s.replace(anchor,addition+anchor,1)
old="preview.exercises.map(x=>'<div class=\"fp-v76-row\"><span>'+fpIcon('target','tiny-art')+esc(x)+'</span></div>').join('')"
new="""preview.exercises.map(x=>'<button type="button" class="fp-v81-exercise" onclick="Fit.guideByName(decodeURIComponent(&quot;'+encodeURIComponent(x)+'&quot;))">'+
   fpIcon('target','tiny-art')+'<span>'+esc(x)+'</span>'+fpIcon('next','tiny-art')+'</button>').join('')"""
change(old,new)
# Also give completed exercise names the same guide link.
old="return '<div class=\"fp-v76-row\"><span>'+fpIcon('check','tiny-art')+esc(e?.n||'운동')+"
new="return '<div class=\"fp-v76-row\"><span><button type=\"button\" class=\"fp-v81-exercise fp-v81-inline\" onclick=\"Fit.guideByName(decodeURIComponent(&quot;'+encodeURIComponent(e?.n||'운동')+'&quot;))\">'+fpIcon('check','tiny-art')+esc(e?.n||'운동')+'</button>'+"
change(old,new)
change('window.Fit={coachInsights,','window.Fit={guideByName:fpGuideByName,coachInsights,')
# If model uses a display pattern string rather than a catalog item, offer a safe video search.
anchor="else if(modal.type==='coachInsights'){"
assert anchor in s
s=s.replace(anchor,"""else if(modal.type==='exerciseLookup'){
 content='<h2>'+esc(modal.exerciseName)+'</h2><p class="sub">정확한 기구명으로 자세 안내 영상을 찾아볼 수 있습니다.</p>'+
  '<button class="btn primary full mt12" onclick="Fit.video(decodeURIComponent(&quot;'+encodeURIComponent(modal.exerciseName)+'&quot;))">운동 자세 영상 검색</button>';
}
 """+anchor,1)

# 4 — Hide duplicated weekly selector, TTS and machine registry UI from Settings.
# Keep selected day data, internal machine-specific progression, and user history unchanged.
start=s.index('function settingsView(){')
end=s.index('function ',start+12)
section=s[start:end]
# V7 likely inserted weekday control ahead of voice settings. Remove *only* section-specific
# known clauses, using selectors anchored to settingsView.
# Insert DOM-scoping class; CSS targets only these legacy Settings elements.
section=section.replace('<h1>FitPlan 설정</h1>','<h1>설정</h1>')
s=s[:start]+section+s[end:]

# Settings implementation spans a single function; remove machine section as a cohesive block.
a=s.index('function settingsView(){')
b=s.index('function ',a+12)
region=s[a:b]
patterns=[
 r'<div class="sectionhead"><h2>헬스장 기구 기록</h2></div><div class="card">.*?</div>\s*(?=<div class="sectionhead">)',
 r'<div class="sectionhead"><h2>음성 코치 · 장기 계획</h2></div><div class="card">.*?<div class="field"><label>자동 장기 계획 기간</label>',
]
# Template strings contain nested expressions; use literal section-based slicing for robust patch.
start_label='<div class="sectionhead"><h2>헬스장 기구 기록</h2></div>'
end_label='<div class="sectionhead"><h2>기록 백업·복원</h2></div>'
if start_label in region:
  i=region.index(start_label);j=region.index(end_label,i)
  region=region[:i]+region[j:]
# Remove voice from mixed voice+weeks card without deleting week-selection functionality.
voice_start='<div class="sectionhead"><h2>음성 코치 · 장기 계획</h2></div>'
voice_end='<div class="field"><label>자동 장기 계획 기간</label>'
if voice_start in region and voice_end in region:
  i=region.index(voice_start);j=region.index(voice_end,i)
  region=region[:i]+'<div class="sectionhead"><h2>운동 프로그램</h2></div><div class="card">'+region[j:]
# Defensive: strip any duplicate weekday selector inside settings only. It is in calendar now.
day_titles=['운동 가능한 요일','운동 요일','훈련 가능 요일','V7 적응형 훈련 일정']
for title in day_titles:
  heading='<div class="sectionhead"><h2>'+title+'</h2></div>'
  if heading in region:
    i=region.index(heading); j=region.find('<div class="sectionhead">',i+len(heading))
    if j>i:region=region[:i]+region[j:]
# Exact weekday card may be a paragraph + chips without a section heading.
i=region.find('<div class="field"><label>운동 가능한 요일</label>')
if i>=0:
  j=region.find('</div>',i)
  if j>=0:region=region[:i]+region[j+6:]
# Remove V7 weekday card even when embedded as a card with headline.
i=region.find('<div class="card"><h2>운동 가능한 요일</h2>')
if i>=0:
  j=region.find('</div>',i+12)
  if j>=0:region=region[:i]+region[j+6:]
s=s[:a]+region+s[b:]

# If the optimized weekday UI was injected as an independent string, remove from settings.
# Store no migrated state: schedule keeps the single source of truth.
p.write_text(s,'utf8')
css=Path('fitplan/native/app/src/main/assets/style.css')
css.write_text(css.read_text('utf8')+"""
/* V8.1 onboarding: true centered option labels, no vertical drift. */
.choices{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.choices .choice{display:flex;align-items:center;justify-content:center;text-align:center;
 flex-direction:column;min-width:0;min-height:88px;padding:13px 8px;border-radius:20px;
 line-height:1.35;gap:4px}
.choices .choice strong{display:block;width:100%;text-align:center;line-height:1.35}
.choices .choice .sub{text-align:center;line-height:1.4}
#app .field:has(button[onclick*="Fit.focus("]) .chips{
 display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px
}
#app .field:has(button[onclick*="Fit.focus("]) .chip{
 display:flex;align-items:center;justify-content:center;white-space:nowrap;min-width:0;
 padding:11px 2px;font-size:13px
}
#app .field:has(button[onclick*="Fit.focus("]) .chip.selected{font-weight:800}
#app .card:has(.fp-v76-head) .chips:has(button[onclick*="Fit.trainingWeekday("]){
 display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:5px;margin-top:12px
}
#app .chips button[onclick*="Fit.trainingWeekday("]{
 min-width:0;width:100%;padding:11px 0;border-radius:50%;font-size:13px;text-align:center
}
.fp-v81-exercise{width:100%;display:flex;align-items:center;gap:10px;
 border:0;border-bottom:1px solid #30434a;padding:14px 3px;
 text-align:left;background:transparent;color:#f3fff6;font-size:15px;cursor:pointer}
.fp-v81-exercise:last-child{border-bottom:0}
.fp-v81-exercise span{flex:1;min-width:0}
.fp-v81-exercise .fp-art{flex-shrink:0}
.fp-v81-exercise.fp-v81-inline{border-bottom:0;padding:2px 0;font-size:inherit;display:inline-flex;width:auto}
@media(max-width:375px){
 .choices .choice{min-height:80px}
 #app .chips button[onclick*="Fit.trainingWeekday("]{font-size:12px;padding:10px 0}
}
""",'utf8')
print('FitPlan V8.1 applied: onboarding layout, 7 weekdays, schedule workout guides, streamlined settings')
