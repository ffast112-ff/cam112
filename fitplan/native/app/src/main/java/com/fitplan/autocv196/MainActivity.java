package com.fitplan.autocv196;

import android.app.Activity;
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
    @Override public void onBackPressed() {
        if (webView != null) {
            webView.evaluateJavascript("(function(){if(typeof window.fitplanBack==='function'){window.fitplanBack();return true;}return false;})()", null);
        }
    }
    @Override public void onConfigurationChanged(Configuration cfg) {
        super.onConfigurationChanged(cfg);
    }
    @Override public void onDestroy() {
        if(webView!=null){webView.destroy();webView=null;}
        super.onDestroy();
    }
}
