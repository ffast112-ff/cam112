#!/usr/bin/env python3
"""V8.3 quality-first V4 generator patch. No saved-state/schema migrations."""
from pathlib import Path
p=Path("fitplan/native/app/src/main/assets/precision-engine-v4.js")
s=p.read_text("utf-8")
def replace(old,new):
 global s
 assert old in s, "V8.3 source anchor changed: "+old[:95]
 s=s.replace(old,new,1)
replace("const focusSet=p=>{const s=new Set(p.focus||[]);if(s.has('팔')){s.add('삼두');s.add('이두');}if(s.has('하체')){s.add('둔근');s.add('뒤허벅지');s.add('종아리');}return s;};",
"""const focusSet=p=>{const s=new Set(p.focus||[]);
 if(s.size>=4)return new Set(); // Four or more regions is balanced full-body, not four priorities.
 if(s.has('팔')){s.add('삼두');s.add('이두');}
 if(s.has('하체')){s.add('둔근');s.add('뒤허벅지');s.add('종아리');}
 return s;};""")
replace("const v=[3,4,5,6][p.level]+(p.level>=2&&focus.has(e.m)&&minutes>=90?1:0);",
"const v=minutes<=60?3:minutes<=90?4:[3,4,5,5][p.level]+(p.level>=2&&focus.has(e.m)&&minutes>=105?1:0);")
replace("  const patterns=template.patterns.filter(pat=>(CREDIT[pat])&&ctx.catalog.some(e=>e.pattern===pat&&V3.allowedExercise(e,ctx.p,ctx.r,ctx.unavailable)));",
"""  let patterns=template.patterns.filter(pat=>(CREDIT[pat])&&ctx.catalog.some(e=>e.pattern===pat&&V3.allowedExercise(e,ctx.p,ctx.r,ctx.unavailable)));
  // Swap pull vertical/horizontal where equipment prevents the template's pull.
  if(split.id==='full'&&ctx.p.days<=3){
    if(!patterns.some(p=>p==='pullvertical'||p==='pullhorizontal')){
      const alt=['pullhorizontal','pullvertical'].find(pat=>ctx.catalog.some(e=>e.pattern===pat&&V3.allowedExercise(e,ctx.p,ctx.r,ctx.unavailable)));
      if(alt)patterns.push(alt);
    }
  }""")
replace("  const items=[],used=new Set();\n  let score=sessionScore(items,ctx).total,est=0;",
"""  const items=[],used=new Set();
  let score=sessionScore(items,ctx).total,est=0;
  // Seed full-body movement coverage before optional sets; don't force impossible
  // exercises, ignore contraindications, or exceed the allocated time.
  if(split.id==='full'&&ctx.p.days<=3){
    const families={lower:['squat','hinge','glutes'],push:['push'],pull:['pullvertical','pullhorizontal']};
    const preferred=ctx.minutes<45?['lower',ctx.sessionIndex%2?'pull':'push']:['lower','push','pull'];
    for(const family of preferred){
      if(items.length>=maxExercises)break;
      const options=candidates.filter(it=>families[family].includes(it.pattern)&&!used.has(it.id));
      options.sort((a,b)=>(b.kind==='compound')-(a.kind==='compound')||
        (ctx.oldExercises.has(b.id)?1:0)-(ctx.oldExercises.has(a.id)?1:0)||a.id.localeCompare(b.id));
      for(const it of options){
        const total=sum([...items,it].map(z=>seconds(z.exercise,z.sets,ctx)));
        if(total>budget)continue;
        items.push(it);used.add(it.id);est=total;score=sessionScore(optimizeOrder(items,ctx),ctx).total;
        break;
      }
    }
  }""")
replace("candidate.combined=R(candidate.score+(rankedMap.get(split.id)?.score||0)*.42,2);",
"""candidate.combined=R(candidate.score+(rankedMap.get(split.id)?.score||0)*.42+
          (c.p.days<=2&&split.id==='full'?12:0),2);""")
p.write_text(s,"utf-8")
print("Quality V8.3 installed: balanced focus, essential patterns, conditional pull substitute, conservative set caps, 2-day full-body preference")
