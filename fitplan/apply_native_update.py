#!/usr/bin/env python3
"""Replace browser-based FitPlan updater with native DownloadManager flow."""
from pathlib import Path
p=Path("fitplan/native/app/src/main/assets/app.js")
s=p.read_text(encoding="utf-8")
anchor="let updateCheckInProgress=false,updateCheckedThisLaunch=false,updateStatus='GitHub 버전 확인 대기 중';"
assert anchor in s
s=s.replace(anchor,anchor+"""
let nativeUpdate={status:'idle',percent:0,message:''};
window.fitplanUpdateProgress=function(status,percent,message){
 nativeUpdate={status:String(status||'idle'),percent:Math.max(0,Math.min(100,Number(percent)||0)),message:String(message||'')};
 updateStatus=nativeUpdate.message;
 if(modal?.type==='update')render();
 else if(status==='error'||status==='permission')toast(nativeUpdate.message);
};
""",1)
start=s.index("function openUpdate(){")
end=s.index("function toast(",start)
s=s[:start]+"""function openUpdate(){
 const u=modal?.url;
 if(!u||!validReleaseUrl(u,repoParts(state.settings.githubRepo||UPDATE_CONFIG.defaultRepo)))return;
 if(!window.FitPlanNative||typeof window.FitPlanNative.downloadUpdate!=='function'){
  toast('이 버전에서는 내부 업데이트가 지원되지 않습니다. 새 APK 버전으로 먼저 업데이트해 주세요.');return;
 }
 if(nativeUpdate.status==='downloading'||nativeUpdate.status==='installing')return;
 nativeUpdate={status:'downloading',percent:0,message:'FitPlan 내부에서 다운로드를 시작합니다.'};
 render();
 try{window.FitPlanNative.downloadUpdate(u);}
 catch(err){nativeUpdate={status:'error',percent:0,message:'업데이트 시작 실패. 다시 시도해 주세요.'};render();}
}
"""+s[end:]
# Replace exactly the update-modal arm, leaving all other dialogs unmodified.
start=s.index("else if(modal.type==='update'){")
end=s.index("else if(modal.type==='history'){",start)
s=s[:start]+"""else if(modal.type==='update'){
 const progress=nativeUpdate.status;
 const busy=progress==='downloading'||progress==='ready'||progress==='installing';
 const label=progress==='downloading'?'다운로드 중…':progress==='permission'?'설치 권한 허용 후 돌아오기':progress==='error'?'다운로드 다시 시도':'앱 내부에서 다운로드 및 설치';
 content=`<div class="eyebrow">FITPLAN 자동 업데이트</div><h2>새 버전 ${esc(modal.version)} 출시</h2>
 <p class="sub mt8">현재 ${APP_VERSION} · 브라우저를 거치지 않고 APK를 다운로드합니다. Android의 설치 승인은 필요합니다.</p>
 ${modal.notes?`<div class="callout">${esc(modal.notes)}</div>`:''}
 ${progress!=='idle'?`<div class="card mt12"><strong>${esc(nativeUpdate.message||'업데이트 준비 중')}</strong><div class="fp-v76-progress mt12" role="progressbar" aria-valuenow="${nativeUpdate.percent}" aria-valuemin="0" aria-valuemax="100"><i style="width:${nativeUpdate.percent}%"></i></div><p class="sub mt8">${progress==='downloading'?nativeUpdate.percent+'%':'Android 보안 정책에 따라 사용자 승인이 필요합니다.'}</p></div>`:''}
 <button class="btn primary full mt12" onclick="Fit.openUpdate()" ${busy?'disabled':''}>${label}</button>
 <button class="btn secondary full mt8" onclick="Fit.closeModal()">닫기</button>
 <p class="sub mt8">다운로드한 APK의 패키지명·버전·서명을 확인한 뒤 설치 화면을 엽니다.</p>`;
 }
 """+s[end:]
assert '브라우저에서 APK를 받은 뒤' not in s
p.write_text(s,encoding="utf-8")
print("Native update button and live progress UI integrated")
