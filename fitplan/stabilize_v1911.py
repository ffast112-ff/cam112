from pathlib import Path
import json, os, re

p=Path('fitplan/native/app/src/main/assets/app.js')
s=p.read_text(encoding='utf-8')
v=os.environ.get('FITPLAN_BUILD_VERSION') or json.loads(Path('fitplan/version.json').read_text())['version']
s,n=re.subn(r"const APP_VERSION='[^']+';", "const APP_VERSION='"+v+"';",s,count=1)
assert n==1,'App version marker missing'
marker="function save(){try{localStorage.setItem(KEY,JSON.stringify(state));}catch(e){console.warn('Cannot save',e)}}"
assert marker in s,'save() changed'
replacement="""let lastSafeSnapshot=0;
let lastNativeSchedule='';
function nativeSync(){
 try{
  const bridge=window.FitPlanNative;
  if(!bridge)return;
  const p=state.player,c=state.calibrationActive;
  let deadline=0,label='';
  if(p&&!p.paused&&['doing','rest'].includes(p.stage)&&p.deadline>Date.now()+800){
   deadline=p.deadline;
   label=p.stage==='rest'?'휴식 종료':'운동 타이머 종료';
  }else if(c&&c.phase==='rest'&&c.restUntil>Date.now()+800){
   deadline=c.restUntil;label='중량 테스트 휴식 종료';
  }
  const key=deadline+':'+label+':'+state.settings.alert;
  if(key!==lastNativeSchedule){
   lastNativeSchedule=key;
   if(deadline&&state.settings.alert!=='off')bridge.scheduleTimer(deadline,label,state.settings.alert);
   else bridge.cancelTimer();
  }
 }catch(e){console.warn('native alarm sync',e)}
}
function save(){
 try{
  const content=JSON.stringify(state);
  localStorage.setItem(KEY,content);
  const now=Date.now();
  if(now-lastSafeSnapshot>=60000&&window.FitPlanNative&&typeof window.FitPlanNative.saveSnapshot==='function'){
   window.FitPlanNative.saveSnapshot(content);
   lastSafeSnapshot=now;
  }
 }catch(e){console.warn('Cannot save',e)}
 nativeSync();
}"""
s=s.replace(marker,replacement,1)
# Restore last verified private snapshot only when localStorage has no record.
needle="const a=JSON.parse(localStorage.getItem(KEY)||'null');"
assert needle in s,'load storage marker missing'
s=s.replace(needle,"let raw=localStorage.getItem(KEY);if(!raw&&window.FitPlanNative){try{const b=window.FitPlanNative.loadSnapshot();if(b){const snapshot=JSON.parse(b);if(snapshot&&snapshot.profile&&Array.isArray(snapshot.history)){raw=b;localStorage.setItem(KEY,b);}}}catch(e){console.warn('snapshot recovery',e)}}const a=JSON.parse(raw||'null');",1)

s=s.replace("let state=load();", "let lastSafeSnapshot=0,lastNativeSchedule='';\nlet state=load();",1)
s=s.replace("let lastSafeSnapshot=0;\nlet lastNativeSchedule='';\nfunction nativeSync()", "function nativeSync()",1)
# Native backup is a separate, app-private fallback; manual export remains required before uninstall.
# On reset never silently preserve the user's explicitly deleted records.
s=s.replace("function resetConfirm(){localStorage.removeItem(KEY);","function resetConfirm(){try{window.FitPlanNative?.clearSnapshot();}catch(e){}localStorage.removeItem(KEY);",1)
# Ensure a restoring user receives a verified schema-compatible object before local storage is changed.
s=s.replace("if(!obj.profile||!Array.isArray(obj.history))throw Error();",
"""if(!obj||typeof obj!=='object'||Array.isArray(obj)||!obj.profile||typeof obj.profile!=='object'||Array.isArray(obj.profile)||!Array.isArray(obj.history)||obj.history.length>100000||!Number.isFinite(Number(obj.schema||1))||JSON.stringify(obj).length>15000000)throw Error();""",1)
# If localStorage fails, do not claim that the restore succeeded.
s=s.replace("localStorage.setItem(KEY,JSON.stringify(obj));state=load();",
"""localStorage.setItem(KEY,JSON.stringify(obj));if(localStorage.getItem(KEY)!==JSON.stringify(obj))throw Error('Storage verification failed');state=load();""",1)
# On resume align native timer with persisted deadline; no JS timers while fully backgrounded assumed.
s=s.replace("document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden'){save();}else{syncAwake();tick();}});",
"""document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden'){save();}else{nativeSync();syncAwake();tick();}});""",1)
p.write_text(s,encoding='utf-8')
print('FitPlan '+v+' JavaScript stabilization applied')
