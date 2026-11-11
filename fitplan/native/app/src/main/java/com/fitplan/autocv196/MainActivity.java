package com.fitplan.autocv196;

import android.app.Activity;
import android.Manifest;
import android.content.pm.PackageManager;
import android.webkit.JavascriptInterface;
import java.io.File;
import java.nio.file.Files;
import java.nio.charset.StandardCharsets;
import android.os.Bundle;
import android.os.Build;
import android.util.Log;
import android.graphics.Color;
import android.view.View;
import android.webkit.ConsoleMessage;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebSettings;
import android.widget.TextView;
import android.widget.FrameLayout;
import android.content.res.Configuration;

public final class MainActivity extends Activity {
    private WebView webView;
    private FitPlanUpdater updater;
    private static volatile boolean visible=false;
    public static boolean isVisible(){return visible;}
    private volatile boolean permissionRequested=false;
    private final class NativeBridge {
        @JavascriptInterface public String getAppVersion(){
            try {return getPackageManager().getPackageInfo(getPackageName(),0).versionName;}
            catch(Throwable t){Log.e(TAG,"Cannot read APK version",t);return "";}
        }
        @JavascriptInterface public void scheduleTimer(long deadline,String label,String alert){
            try { TimerAlarmReceiver.schedule(MainActivity.this,deadline,label,alert); } catch(Throwable t){Log.e(TAG,"Timer schedule error",t);}
            if(Build.VERSION.SDK_INT>=33 && !permissionRequested && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED){
                permissionRequested=true;
                runOnUiThread(()->requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},119));
            }
        }
        @JavascriptInterface public void cancelTimer(){TimerAlarmReceiver.cancel(MainActivity.this);}
        @JavascriptInterface public void downloadUpdate(String url){
            if(updater!=null)updater.begin(url);
        }
        @JavascriptInterface public void saveSnapshot(String json){
            if(json==null||json.length()>15000000)return;
            try{
                File target=new File(getFilesDir(),"workout_snapshot.json"), tmp=new File(getFilesDir(),"workout_snapshot.tmp");
                Files.write(tmp.toPath(),json.getBytes(StandardCharsets.UTF_8));
                if(!tmp.renameTo(target))Log.w(TAG,"Snapshot rename failed");
            }catch(Throwable e){Log.w(TAG,"Snapshot backup failed",e);}
        }
        @JavascriptInterface public String loadSnapshot(){
            try{
                File f=new File(getFilesDir(),"workout_snapshot.json");
                if(f.length()>15000000)return "";
                return f.exists()?new String(Files.readAllBytes(f.toPath()),StandardCharsets.UTF_8):"";
            }catch(Throwable e){Log.w(TAG,"Snapshot recovery unavailable",e);return "";}
        }
        @JavascriptInterface public void clearSnapshot(){
            try{new File(getFilesDir(),"workout_snapshot.json").delete();}catch(Throwable e){Log.w(TAG,"Snapshot removal failed",e);}
        }
    }

    private static final String TAG = "FitPlanLaunch";
    private static final String START_URL = "file:///android_asset/index.html";

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.rgb(7,11,10));
        getWindow().setNavigationBarColor(Color.rgb(7,11,10));
        final FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(7,11,10));
        setContentView(root);
        try {
            webView = new WebView(this);
            WebSettings settings = webView.getSettings();
            settings.setJavaScriptEnabled(true);
            settings.setDomStorageEnabled(true);
            settings.setAllowFileAccess(true);
            settings.setDefaultTextEncodingName("UTF-8");
            settings.setMediaPlaybackRequiresUserGesture(false);
            webView.setBackgroundColor(Color.rgb(7,11,10));
            updater=new FitPlanUpdater(this,webView);
            webView.addJavascriptInterface(new NativeBridge(), "FitPlanNative");
            webView.setWebChromeClient(new WebChromeClient() {
                @Override public boolean onConsoleMessage(ConsoleMessage msg) {
                    Log.i(TAG, "JS " + msg.messageLevel() + " " + msg.sourceId() + ":" + msg.lineNumber() + " " + msg.message());
                    return true;
                }
            });
            webView.setWebViewClient(new WebViewClient() {
                @Override public void onPageFinished(WebView v, String url) {
                    Log.i(TAG,"Page finished: " + url);
                }
                @Override public void onReceivedError(WebView v, WebResourceRequest req, WebResourceError error) {
                    if (req.isForMainFrame()) {
                        Log.e(TAG, "Main document error: " + error);
                    }
                }
            });
            root.addView(webView, new FrameLayout.LayoutParams(-1,-1));
            webView.loadUrl(START_URL);
            Log.i(TAG,"Activity and WebView initialized");
        } catch (Throwable t) {
            Log.e(TAG,"Startup failed",t);
            root.removeAllViews();
            TextView label = new TextView(this);
            label.setText("FitPlan 초기화 오류. Android WebView 업데이트를 확인하세요.\n" + t.getClass().getSimpleName() + ": " + t.getMessage());
            label.setTextColor(Color.WHITE);
            label.setTextSize(16);
            label.setPadding(32,48,32,32);
            root.addView(label);
        }
    }
    @Override protected void onResume(){super.onResume();visible=true;if(updater!=null)updater.onResume();}
    @Override protected void onPause(){visible=false;super.onPause();}
    @Override public void onBackPressed() {
        if (webView != null) {
            webView.evaluateJavascript("(function(){if(typeof window.fitplanBack==='function'){window.fitplanBack();return true;}return false;})()", null);
        }
    }
    @Override public void onConfigurationChanged(Configuration cfg) {
        super.onConfigurationChanged(cfg);
    }
    @Override public void onDestroy() {
        if(updater!=null){updater.destroy();updater=null;}
        if(webView!=null){webView.destroy();webView=null;}
        super.onDestroy();
    }
}
