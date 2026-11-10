package com.fitplan.autocv196;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.AlarmManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.media.AudioAttributes;
import android.os.Build;
import android.os.SystemClock;
import android.Manifest;
import android.content.pm.PackageManager;
import android.provider.Settings;
import android.net.Uri;
import android.util.Log;

public final class TimerAlarmReceiver extends BroadcastReceiver {
    public static final String ACTION = "com.fitplan.autocv196.TIMER_COMPLETE";
    private static final int REQUEST_CODE = 3019;
    public static void cancel(Context context) {
        AlarmManager manager=(AlarmManager)context.getSystemService(Context.ALARM_SERVICE);
        PendingIntent pending=pending(context,PendingIntent.FLAG_NO_CREATE);
        if(pending!=null && manager!=null){manager.cancel(pending);pending.cancel();}
    }
    private static PendingIntent pending(Context context,int flags) {
        Intent i=new Intent(context,TimerAlarmReceiver.class).setAction(ACTION);
        return PendingIntent.getBroadcast(context,REQUEST_CODE,i,flags|PendingIntent.FLAG_IMMUTABLE);
    }
    public static void schedule(Context context,long when,String label,String alert) {
        cancel(context);
        if(when<=System.currentTimeMillis()||"off".equals(alert))return;
        AlarmManager manager=(AlarmManager)context.getSystemService(Context.ALARM_SERVICE);
        if(manager==null)return;
        Intent i=new Intent(context,TimerAlarmReceiver.class).setAction(ACTION);
        i.putExtra("label",label==null?"운동 타이머 종료":label);
        i.putExtra("alert",alert==null?"both":alert);
        PendingIntent p=PendingIntent.getBroadcast(context,REQUEST_CODE,i,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
        if(Build.VERSION.SDK_INT>=31){
            if(manager.canScheduleExactAlarms())manager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP,when,p);
            else manager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP,when,p);
        }else if(Build.VERSION.SDK_INT>=23){
            manager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP,when,p);
        }else manager.setExact(AlarmManager.RTC_WAKEUP,when,p);
    }
    @Override public void onReceive(Context context,Intent intent) {
        try{
            if(MainActivity.isVisible())return; // Foreground JS plays the alarm itself.
            if(Build.VERSION.SDK_INT>=33&&context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)return;
            NotificationManager nm=(NotificationManager)context.getSystemService(Context.NOTIFICATION_SERVICE);
            if(nm==null)return;
            String alert=intent.getStringExtra("alert");
            if(alert==null||"off".equals(alert))return;
            String channel="fitplan_timer_"+alert+"_v1";
            if(Build.VERSION.SDK_INT>=26){
                NotificationChannel nc=new NotificationChannel(channel,"FitPlan 타이머",NotificationManager.IMPORTANCE_HIGH);
                nc.setDescription("백그라운드 운동 및 휴식 타이머 알림");
                nc.enableVibration("vibrate".equals(alert)||"both".equals(alert));
                if("vibrate".equals(alert))nc.setSound(null,null);
                nm.createNotificationChannel(nc);
            }
            Intent launch=context.getPackageManager().getLaunchIntentForPackage(context.getPackageName());
            PendingIntent tap=launch==null?null:PendingIntent.getActivity(context,0,launch,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
            Notification.Builder builder=Build.VERSION.SDK_INT>=26?new Notification.Builder(context,channel):new Notification.Builder(context);
            builder.setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
                   .setContentTitle("FitPlan 타이머 종료")
                   .setContentText(intent.getStringExtra("label"))
                   .setAutoCancel(true)
                   .setVisibility(Notification.VISIBILITY_PUBLIC);
            if(tap!=null)builder.setContentIntent(tap);
            nm.notify(3019,builder.build());
        }catch(Throwable t){Log.e("FitPlanAlarm","Notification failure",t);}
    }
}
