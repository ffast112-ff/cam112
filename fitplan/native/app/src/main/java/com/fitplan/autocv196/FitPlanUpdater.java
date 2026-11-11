package com.fitplan.autocv196;

import android.app.Activity;
import android.app.DownloadManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.webkit.WebView;
import java.io.File;
import java.util.regex.Pattern;
import org.json.JSONObject;

/** In-app download and OS-confirmed install. No silent installation and no external browser. */
final class FitPlanUpdater {
    private static final Pattern RELEASE_URL=Pattern.compile(
        "^https://github\\.com/ffast112-ff/cam112/releases/download/fitplan-v([0-9]+\\.[0-9]+\\.[0-9]+)/FitPlan-\\1\\.apk$");
    private final Activity activity;
    private final WebView web;
    private final Handler handler=new Handler(Looper.getMainLooper());
    private long downloadId=-1;
    private boolean destroyed=false;
    private boolean permissionPageOpened=false;
    private File staged;
    private final Runnable poll=new Runnable(){@Override public void run(){checkDownload();}};
    FitPlanUpdater(Activity a,WebView w){activity=a;web=w;}

    void begin(String url){
        handler.post(()->{
            if(destroyed)return;
            if(!RELEASE_URL.matcher(url==null?"":url).matches()){
                report("error",0,"허용되지 않은 업데이트 주소입니다.");return;
            }
            if(downloadId!=-1){report("downloading",0,"다운로드가 진행 중입니다.");return;}
            try{
                staged=new File(activity.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS),"fitplan-update.apk");
                if(staged.exists()&&!staged.delete()){
                    report("error",0,"이전 다운로드를 정리하지 못했습니다.");return;
                }
                DownloadManager dm=(DownloadManager)activity.getSystemService(Context.DOWNLOAD_SERVICE);
                DownloadManager.Request req=new DownloadManager.Request(Uri.parse(url));
                req.setTitle("FitPlan 업데이트");
                req.setDescription("공식 GitHub APK 다운로드");
                req.setMimeType("application/vnd.android.package-archive");
                req.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE);
                req.setDestinationUri(Uri.fromFile(staged));
                downloadId=dm.enqueue(req);
                report("downloading",0,"앱 내부에서 APK를 다운로드하고 있습니다.");
                handler.postDelayed(poll,500);
            }catch(Exception e){downloadId=-1;report("error",0,"다운로드 시작 실패: "+e.getClass().getSimpleName());}
        });
    }
    private void checkDownload(){
        if(destroyed||downloadId==-1)return;
        try{
            DownloadManager dm=(DownloadManager)activity.getSystemService(Context.DOWNLOAD_SERVICE);
            DownloadManager.Query q=new DownloadManager.Query().setFilterById(downloadId);
            try(Cursor c=dm.query(q)){
                if(c==null||!c.moveToFirst()){downloadId=-1;report("error",0,"다운로드 작업을 찾지 못했습니다.");return;}
                int status=c.getInt(c.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS));
                long total=c.getLong(c.getColumnIndexOrThrow(DownloadManager.COLUMN_TOTAL_SIZE_BYTES));
                long done=c.getLong(c.getColumnIndexOrThrow(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR));
                int percent=total>0?(int)Math.min(100,done*100/total):0;
                if(status==DownloadManager.STATUS_SUCCESSFUL){
                    downloadId=-1;
                    if(!verifyArchive(staged)){staged.delete();report("error",0,"APK 패키지 또는 서명 검증 실패. 설치를 중단했습니다.");return;}
                    report("ready",100,"다운로드 완료. Android 설치 화면을 엽니다.");
                    installVerified();
                    return;
                }
                if(status==DownloadManager.STATUS_FAILED){
                    int reason=c.getInt(c.getColumnIndexOrThrow(DownloadManager.COLUMN_REASON));
                    downloadId=-1;report("error",percent,"다운로드 실패 (코드 "+reason+"). 다시 시도해 주세요.");return;
                }
                report("downloading",percent, total>0?percent+"% 다운로드 중":"다운로드 연결 중");
            }
            handler.postDelayed(poll,700);
        }catch(Exception e){downloadId=-1;report("error",0,"다운로드 오류: "+e.getClass().getSimpleName());}
    }
    private Signature[] signers(PackageInfo info){
        if(info==null)return null;
        if(Build.VERSION.SDK_INT>=28)
            return info.signingInfo==null?null:info.signingInfo.getApkContentsSigners();
        return info.signatures;
    }
    @SuppressWarnings("deprecation")
    private boolean verifyArchive(File file){
        try{
            if(file==null||!file.isFile()||file.length()<50000)return false;
            PackageManager pm=activity.getPackageManager();
            int flags=Build.VERSION.SDK_INT>=28?PackageManager.GET_SIGNING_CERTIFICATES:PackageManager.GET_SIGNATURES;
            PackageInfo candidate=pm.getPackageArchiveInfo(file.getAbsolutePath(),flags);
            PackageInfo installed=pm.getPackageInfo(activity.getPackageName(),flags);
            if(candidate==null||!activity.getPackageName().equals(candidate.packageName))return false;
            if(candidate.versionCode<=installed.versionCode)return false;
            Signature[] a=signers(candidate),b=signers(installed);
            if(a==null||b==null||a.length!=b.length||a.length==0)return false;
            for(Signature sa:a){
                boolean found=false;
                for(Signature sb:b)if(sa.equals(sb)){found=true;break;}
                if(!found)return false;
            }
            return true;
        }catch(Exception e){return false;}
    }
    void onResume(){
        handler.postDelayed(()->{
            if(destroyed||staged==null||downloadId!=-1||!staged.isFile())return;
            if(Build.VERSION.SDK_INT>=26&&!activity.getPackageManager().canRequestPackageInstalls()){
                report("permission",100,"FitPlan의 '이 출처의 앱 설치 허용'을 켠 후 돌아오세요.");
                return;
            }
            if(permissionPageOpened){permissionPageOpened=false;installVerified();}
        },500);
    }
    private void installVerified(){
        if(!verifyArchive(staged)){report("error",0,"APK 검증에 실패했습니다.");return;}
        try{
            if(Build.VERSION.SDK_INT>=26&&!activity.getPackageManager().canRequestPackageInstalls()){
                report("permission",100,"Android에서 FitPlan의 앱 설치 권한을 허용해 주세요.");
                permissionPageOpened=true;
                Intent settings=new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                        Uri.parse("package:"+activity.getPackageName()));
                activity.startActivity(settings);
                return;
            }
            Uri uri=new Uri.Builder().scheme("content")
                    .authority(activity.getPackageName()+".updatefile").path("fitplan-update.apk").build();
            Intent install=new Intent(Intent.ACTION_VIEW);
            install.setDataAndType(uri,"application/vnd.android.package-archive");
            install.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_ACTIVITY_NEW_TASK);
            report("installing",100,"Android 설치 승인 화면에서 업데이트를 확인해 주세요.");
            activity.startActivity(install);
        }catch(Exception e){report("error",100,"설치 화면 실행 실패: "+e.getClass().getSimpleName());}
    }
    private void report(String status,int percent,String message){
        if(destroyed)return;
        handler.post(()->{
            if(destroyed)return;
            String js="window.fitplanUpdateProgress&&window.fitplanUpdateProgress("+
                JSONObject.quote(status)+","+percent+","+JSONObject.quote(message)+");";
            web.evaluateJavascript(js,null);
        });
    }
    void destroy(){destroyed=true;handler.removeCallbacks(poll);}
}
