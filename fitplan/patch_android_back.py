from pathlib import Path
p=Path('fitplan/app/assets/app.js')
s=p.read_text(encoding='utf-8')
marker='function setupView(){'
if 'fitplanNavGuardKey' in s:
    print('Back navigation already patched')
else:
    assert marker in s, 'Cannot locate FitPlan screen navigation code'
    patch=r"""// Android WebView native Activity handles Back using WebView.goBack().
// Preserve an in-app same-document history entry to avoid Activity exit.
const fitplanNavGuardKey='fitplan_inapp_back_guard_v1';
function fitplanBack(){
 if(modal){modal=null;render();return;}
 if(view==='setup'&&setupPage>0){setupBack();return;}
 if(view==='player'){
  if(state.player){exitPlayer();return;}
  view='work';render();return;
 }
 if(view==='calibration'){save();view='work';render();return;}
 if(view==='ready'||view==='finish'||view==='setup'){
  view=state.onboard?'home':'setup';render();return;
 }
 if(view==='machines'){view='work';render();return;}
 if(view!=='home'){view='home';render();return;}
 toast('홈 화면입니다');
}
function installFitplanAndroidBack(){
 try{
  const original=history.state;
  history.replaceState({...(original&&typeof original==='object'?original:{}),fitplanRoot:true},'');
  history.pushState({fitplanGuard:fitplanNavGuardKey},'');
  window.addEventListener('popstate',()=>{
   fitplanBack();
   history.pushState({fitplanGuard:fitplanNavGuardKey},'');
  });
  window.addEventListener('keydown',e=>{
   if(e.key==='Escape'||(e.key==='Backspace'&&e.target?.tagName!=='INPUT'&&e.target?.tagName!=='TEXTAREA')){
    e.preventDefault();fitplanBack();
   }
  });
 }catch(err){console.warn('Back navigation guard unavailable',err);}
}
installFitplanAndroidBack();
"""
    s=s.replace(marker,patch+'\n'+marker,1)
    p.write_text(s,encoding='utf-8')
    print('Android system back navigation patched')
