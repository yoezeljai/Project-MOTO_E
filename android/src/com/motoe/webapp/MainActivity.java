package com.motoe.webapp;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Build;
import android.webkit.GeolocationPermissions;
import android.webkit.WebChromeClient;
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
        web.getSettings().setGeolocationEnabled(true);
        web.getSettings().setDomStorageEnabled(true);  // stand mode remembers clock/frame
        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback cb) {
                cb.invoke(origin, true, false);  // only our own local pages are loaded
            }
        });
        // Only the Clock and Stand apps declare location; for the others this is a silent no-op.
        if (Build.VERSION.SDK_INT >= 23
                && checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[] {Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION}, 1);
        }
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

    /** Clock/Stand only: hide status and navigation bars. A tap shows them; they hide again after 3 s. */
    private boolean immersive() {
        return "1".equals(getString(R.string.immersive));
    }

    private final Runnable hideBars = new Runnable() {
        public void run() {
            getWindow().getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                    | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                    | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION   // "lean back": any tap brings the bars back
                    | View.SYSTEM_UI_FLAG_FULLSCREEN);
        }
    };

    @Override
    protected void onResume() {
        super.onResume();
        if (immersive()) {
            getWindow().getDecorView().setOnSystemUiVisibilityChangeListener(
                    new View.OnSystemUiVisibilityChangeListener() {
                        public void onSystemUiVisibilityChange(int vis) {
                            if ((vis & View.SYSTEM_UI_FLAG_FULLSCREEN) == 0) {
                                handler.removeCallbacks(hideBars);
                                handler.postDelayed(hideBars, 3000);
                            }
                        }
                    });
            hideBars.run();
        }
        web.reload();
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus && immersive()) hideBars.run();
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) web.goBack(); else super.onBackPressed();
    }
}
