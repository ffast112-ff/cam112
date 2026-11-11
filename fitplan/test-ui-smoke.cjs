/* Verify actual post-patch FitPlan DOM, not just JS syntax.
 * npm install --no-save jsdom@26 before running.
 */
const fs=require('fs'),path=require('path'),assert=require('assert');
const {JSDOM,VirtualConsole}=require('jsdom');
const assets=path.resolve(__dirname,'native/app/src/main/assets');
const index=fs.readFileSync(path.join(assets,'index.html'),'utf8');
const html=index.replace(/<script[^>]*src="[^"]+"[^>]*><\/script>/g,'');
const errors=[],consoleShim=new VirtualConsole();
consoleShim.on('jsdomError',e=>errors.push(String(e)));
consoleShim.on('error',e=>errors.push(String(e)));
const dom=new JSDOM(html,{url:'https://fitplan-local.test/',runScripts:'dangerously',pretendToBeVisual:true,virtualConsole:consoleShim});
const win=dom.window;
win.fetch=async()=>({ok:false,status:503,json:async()=>({})});
win.FitPlanNative={
  getAppVersion:()=> '1.9.16',saveSnapshot:()=>{},loadSnapshot:()=>'',cancelTimer:()=>{},
  scheduleTimer:()=>{},syncSchedule:()=>{},downloadUpdate:()=>{}
};
win.localStorage.setItem('fitplan_autocoach_01',JSON.stringify({
  schema:19,onboard:true,profile:{sex:'male',goal:'hypertrophy',days:3,duration:60,place:'gym',height:178,weight:96,focus:['등'],restrictions:[]},
  settings:{alert:'off',githubRepo:'ffast112-ff/cam112'},history:[],sessionIndex:0,machines:{},cycleReports:[]
}));
const scripts=Array.from(index.matchAll(/<script[^>]*src="([^"]+)"[^>]*><\/script>/g)).map(m=>m[1]);
for(const src of scripts){try{win.eval(fs.readFileSync(path.join(assets,src),'utf8')+'\n//# sourceURL='+src);}catch(e){throw new Error('Script '+src+' failed: '+e.stack);}}
assert(win.Fit,'FitPlan actions not registered');
for(const view of ['home','work','history','state','schedule']){
  try{win.Fit.go(view);}catch(e){throw new Error(view+': '+e.stack);}
  const text=win.document.querySelector('#app')?.textContent||'';
  assert(!text.includes('화면을 불러오지 못했습니다'),view+' crashed while rendering');
  assert(text.length>30,view+' produced blank UI');
  const nav=win.document.querySelector('.tabbar');
  assert(nav&&nav.querySelectorAll('button').length===5,'Bottom navigation not rendered for '+view);
  assert(win.document.querySelectorAll('svg.fp-art').length===0,'Broken external svg icon still used');
  const icons=[...win.document.querySelectorAll('img.fp-art')];
  assert(icons.length>=5,'Missing navigation images: '+view);
  for(const im of icons){
    assert(im.getAttribute('src').startsWith('data:image/svg+xml;base64,'),'Icon not self-contained');
    const svg=Buffer.from(im.src.split(',')[1],'base64').toString('utf8');
    assert(svg.includes('<svg')&&svg.includes('viewBox'),'Invalid icon SVG');
  }
  if(view==='schedule'){
    assert(win.document.querySelectorAll('.fp-day').length===42,'Calendar cells !=42');
    const before=win.document.querySelector('.fp-calendar-head strong').textContent;
    win.Fit.moveCalendar(1);
    assert(win.document.querySelector('.fp-calendar-head strong').textContent!==before,'Month navigation broken');
    win.Fit.todayCalendar();
    win.Fit.selectCalendar('2026-11-13');
    win.Fit.markCalendar('planned');
    assert(win.FitEngine.state().settings.scheduleOverrides['2026-11-13']==='planned','Manual schedule not saved');
  }
  process.stdout.write('PASS '+view+' '+text.length+' chars '+icons.length+' icons\n');
}
// Regression: projected days are not hard-coded Tue/Thu/Sat; actual exercise details display.
win.Fit.trainingWeekday(-1);
assert.deepStrictEqual(Array.from(win.FitEngine.state().settings.trainingWeekdays||[]),[],'No fixed weekday constraint');
const today=new Date(),local=[today.getFullYear(),String(today.getMonth()+1).padStart(2,'0'),String(today.getDate()).padStart(2,'0')].join('-');
win.FitEngine.state().history.push({
  schema:19,finishedAt:Date.now(),splitName:'테스트 하체',
  items:[{currentId:'test-exercise',sets:[{done:true,warmup:false,role:'work',actualWeight:90,actualReps:12}]}]
});
win.Fit.go('schedule');win.Fit.selectCalendar(local);
assert(win.document.querySelector('#app').textContent.includes('테스트 하체'),'Completed workout split missing on calendar');
assert(win.document.querySelector('#app').textContent.includes('1세트'),'Completed exercise count missing on calendar');
const detailIcons=win.document.querySelectorAll('img.fp-art.tiny-art').length;
assert(detailIcons>0,'Decorative detailed menu images were not rendered');
console.log('PASS history date details and image-based secondary icons',detailIcons);

assert(!errors.some(x=>/FitPlan render error|Uncaught/i.test(x)),errors.join('\n'));
const css=fs.readFileSync(path.join(assets,'style.css'),'utf8');
assert(!css.includes('}\\n.fp-art'),'CSS contains escaped newline');
console.log('FitPlan DOM smoke passed');
dom.window.close();
