package com.fitplan.autocv196;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.AlarmManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.media.AudioAttributes;
import android.net.Uri;
import android.os.Build;
import android.Manifest;
import android.util.Log;

/** Android-resident end-of-timer signal and optional softer five-second reminder. */
public final class TimerAlarmReceiver extends BroadcastReceiver {
    private static final String ACTION = "com.fitplan.autocv196.TIMER_COMPLETE";
    private static final int END_REQUEST=3019,PRE_REQUEST=3020;
    private static PendingIntent pending(Context c,int request,int flags){
        Intent i=new Intent(c,TimerAlarmReceiver.class).setAction(ACTION);
        i.putExtra("pre",request==PRE_REQUEST);
        return PendingIntent.getBroadcast(c,request,i,flags|PendingIntent.FLAG_IMMUTABLE);
    }
    public static void cancel(Context c){
        AlarmManager a=(AlarmManager)c.getSystemService(Context.ALARM_SERVICE);
        if(a==null)return;
        for(int code:new int[]{END_REQUEST,PRE_REQUEST}){
            PendingIntent p=pending(c,code,PendingIntent.FLAG_NO_CREATE);
            if(p!=null){a.cancel(p);p.cancel();}
        }
    }
    private static void alarm(AlarmManager a,long when,PendingIntent p){
        if(Build.VERSION.SDK_INT>=31){
            if(a.canScheduleExactAlarms())a.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP,when,p);
            else a.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP,when,p);
        }else if(Build.VERSION.SDK_INT>=23)a.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP,when,p);
        else a.setExact(AlarmManager.RTC_WAKEUP,when,p);
    }
    public static void schedule(Context c,long when,String label,String alert,boolean preAlert){
        cancel(c);
        long now=System.currentTimeMillis();
        if(when<=now||"off".equals(alert))return;
        AlarmManager am=(AlarmManager)c.getSystemService(Context.ALARM_SERVICE);
        if(am==null)return;
        String title=label==null?"운동 타이머 종료":label;
        Intent end=new Intent(c,TimerAlarmReceiver.class).setAction(ACTION)
          .putExtra("label",title).putExtra("alert",alert).putExtra("pre",false);
        alarm(am,when,PendingIntent.getBroadcast(c,END_REQUEST,end,
             PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE));
        if(preAlert&&when-now>5500){
            Intent pre=new Intent(c,TimerAlarmReceiver.class).setAction(ACTION)
              .putExtra("label",title).putExtra("alert",alert).putExtra("pre",true);
            alarm(am,when-5000,PendingIntent.getBroadcast(c,PRE_REQUEST,pre,
                  PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE));
        }
    }
    @Override public void onReceive(Context c,Intent intent){
        try{
            if(MainActivity.isVisible())return; // Foreground WebAudio owns the signals.
            if(Build.VERSION.SDK_INT>=33&&c.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)return;
            String alert=intent.getStringExtra("alert");
            if(alert==null||"off".equals(alert))return;
            boolean pre=intent.getBooleanExtra("pre",false),vibrate="both".equals(alert)||"vibrate".equals(alert);
            NotificationManager nm=(NotificationManager)c.getSystemService(Context.NOTIFICATION_SERVICE);
            if(nm==null)return;
            String channel="fitplan_signal_"+(pre?"pre":"end")+"_"+alert+"_v2";
            if(Build.VERSION.SDK_INT>=26){
                NotificationChannel nc=new NotificationChannel(channel,pre?"FitPlan 5초 전 알림":"FitPlan 종료 시보",pre?NotificationManager.IMPORTANCE_DEFAULT:NotificationManager.IMPORTANCE_HIGH);
                nc.setDescription(pre?"종료 5초 전 짧은 시보":"타이머 종료 시 뚜렷한 시보");
                nc.enableVibration(vibrate);
                if("vibrate".equals(alert))nc.setSound(null,null);
                else {
                    int sound=pre?R.raw.fitplan_pretone:R.raw.fitplan_endtone;
                    Uri soundUri=Uri.parse("android.resource://"+c.getPackageName()+"/"+sound);
                    AudioAttributes attrs=new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_NOTIFICATION_EVENT)
                      .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build();
                    nc.setSound(soundUri,attrs);
                }
                nm.createNotificationChannel(nc);
            }
            Intent launch=c.getPackageManager().getLaunchIntentForPackage(c.getPackageName());
            PendingIntent tap=launch==null?null:PendingIntent.getActivity(c,0,launch,
                    PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
            Notification.Builder b=Build.VERSION.SDK_INT>=26?new Notification.Builder(c,channel):new Notification.Builder(c);
            b.setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
             .setContentTitle(pre?"FitPlan · 종료 5초 전":"FitPlan · 타이머 종료")
             .setContentText(intent.getStringExtra("label"))
             .setAutoCancel(true).setVisibility(Notification.VISIBILITY_PUBLIC);
            if(tap!=null)b.setContentIntent(tap);
            nm.notify(pre?3020:3019,b.build());
        }catch(Throwable t){Log.e("FitPlanAlarm","Native time signal unavailable",t);}
    }
}
