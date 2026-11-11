/* FitPlan V7.9 sequential workout schedule queue.
   Exercise order advances on completed sessions, never merely on elapsed calendar days.
   Future date edits always reassign every remaining date without changing completed history. */
(function(root, factory) {
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  else root.FitPlanScheduleQueue=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const validDate=s=>typeof s==='string'&&/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(s)
    && !Number.isNaN(new Date(s+'T12:00:00').getTime())
    && new Date(s+'T12:00:00').toISOString().slice(0,10)===s;
  function assign(input={}){
    const today=validDate(input.today)?input.today:new Date().toISOString().slice(0,10);
    const done=new Set(Array.from(input.completedDates||[]).filter(validDate));
    const overrides=input.overrides&&typeof input.overrides==='object'?input.overrides:{};
    const splitNames=(input.splitNames||[]).filter(s=>typeof s==='string'&&s.trim());
    const start=Math.max(0,Math.trunc(Number(input.sessionIndex)||0));
    const candidates=new Map();
    for(const raw of input.baseSlots||[]){
      if(!validDate(raw?.date)||raw.date<today||done.has(raw.date))continue;
      candidates.set(raw.date,{...raw});
    }
    for(const [date,action] of Object.entries(overrides)){
      if(!validDate(date)||date<today||done.has(date))continue;
      if(action==='rest')candidates.delete(date);
      if(action==='planned'&&!candidates.has(date))candidates.set(date,{date,source:'manual'});
    }
    // Rest takes precedence over an optimizer-generated day; completed sessions remain immutable.
    for(const [date,action] of Object.entries(overrides))
      if(action==='rest')candidates.delete(date);
    const sorted=[...candidates.keys()].sort();
    const result=new Map();
    sorted.forEach((date,i)=>{
      const index=start+i;
      const prior=candidates.get(date);
      result.set(date,{...prior,date,sessionIndex:index,
        dayName:splitNames.length?splitNames[index%splitNames.length]:(prior.dayName||'예정 운동'),
        sequence:index,source:prior.source||'optimized'});
    });
    return result;
  }
  return {assign,validDate};
});
