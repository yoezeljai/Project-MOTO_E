package com.motoe.webapp;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;

/** Full-screen wrapper around one page of the local Moto E remote server. */
public class MainActivity extends Activity {
    private WebView web;
    private final Handler handler = new Handler();
    private String url;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        url = getString(R.string.page_url);

        web = new WebView(this);
        web.getSettings().setJavaScriptEnabled(true);
        web.setBackgroundColor(0xFF12161B);
        web.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedError(WebView v, WebResourceRequest req, WebResourceError err) {
                if (req.isForMainFrame()) showOffline();
            }
        });
        setContentView(web);
        web.loadUrl(url);
    }

    /** The Termux server may still be starting after boot: show a note and retry. */
    private void showOffline() {
        web.loadData("<html><body style='background:#12161b;color:#9aa5ae;font-family:sans-serif;"
                + "padding:40px 20px;font-size:18px'>Starting the home server&hellip;<br><br>"
                + "<small>If this stays, open Termux and run:<br>cd ~/remote &amp;&amp; bash start.sh"
                + "</small></body></html>", "text/html", "utf-8");
        handler.postDelayed(new Runnable() {
            public void run() { web.loadUrl(url); }
        }, 4000);
    }

    @Override
    protected void onResume() {
        super.onResume();
        web.getRootView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
        web.reload();
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) web.goBack(); else super.onBackPressed();
    }
}
