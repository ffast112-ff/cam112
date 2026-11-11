#!/usr/bin/env python3
"""V8.3 final quality gate: reject broken coverage and extreme set bias before display."""
from pathlib import Path
p=Path('fitplan/native/app/src/main/assets/precision-engine-v75.js')
s=p.read_text('utf8')
old="""  if(sets.length>6)errors.push('excessive-sets:'+it.id);"""
new="""  const minutes=N(input.minutes,input.profile?.duration||60);
  const max=minutes<=60?4:minutes<=90?5:6;
  if(sets.length>max)errors.push('excessive-sets:'+it.id);"""
assert old in s
s=s.replace(old,new,1)
anchor=""" if(p.safety?.stop&&(p.items||[]).length)errors.push('unsafe-plan');"""
assert anchor in s
s=s.replace(anchor,""" // Only require all three movement families where a full-body session is
 // feasible: 2 training days, >=45min, no pain/restriction. Home substitutions
 // are already handled by the quality-first V4 candidate generator.
 if(p.split==='full'&&N(input.profile?.days,3)<=2&&
    N(input.minutes,input.profile?.duration||60)>=45&&
    !input.readiness?.pain&&!input.profile?.restrictions?.length){
   const patterns=new Set((p.items||[]).map(it=>it.pattern));
   if(![...patterns].some(x=>['squat','hinge','glutes'].includes(x)))errors.push('missing-lower');
   if(!patterns.has('push'))errors.push('missing-push');
   if(!patterns.has('pullvertical')&&!patterns.has('pullhorizontal'))errors.push('missing-pull');
 }
"""+anchor,1)
# Retest fallback; an already broken V4 routine must not be described as quality-verified.
old="""  return {...fallback,version:'7.5.0',v75:{fallback:true,checks,alerts:[]}};"""
new="""  const fallbackChecks=evaluate(input,fallback);
  return {...fallback,version:'7.5.0',
   v75:{fallback:true,checks,fallbackChecks,qualityVerified:fallbackChecks.ok,
     alerts:fallbackChecks.ok?[]:[{message:'현재 장비·시간·통증 제약에서 모든 품질 조건을 충족하지 못했습니다. 루틴을 확인하세요.'}]}};"""
assert old in s
s=s.replace(old,new,1)
old="""return {...out,version:'7.5.0',v75:{fallback:false,checks,alerts,"""
new="""return {...out,version:'7.5.0',v75:{fallback:false,checks,qualityVerified:true,alerts,"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s,'utf8')
print('V8.3 quality gate: working-set caps, conditional full-body coverage, verified fallback')
