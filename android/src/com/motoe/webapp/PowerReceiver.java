package com.motoe.webapp;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Stand app only: open the stand page (clock or photo frame) when the charger is connected. */
public class PowerReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context ctx, Intent intent) {
        Intent open = new Intent(ctx, MainActivity.class);
        open.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        ctx.startActivity(open);
    }
}
