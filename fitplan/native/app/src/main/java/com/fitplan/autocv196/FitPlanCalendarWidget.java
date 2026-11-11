package com.fitplan.autocv196;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Bundle;
import android.widget.RemoteViews;
import org.json.JSONArray;
import org.json.JSONObject;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

/** Resizable launcher widget. All data remains on the device. */
public final class FitPlanCalendarWidget extends AppWidgetProvider {
    private static final int GREEN=Color.rgb(67,247,111);
    private static final int WHITE=Color.rgb(238,250,244);
    private static final int GRAY=Color.rgb(155,173,180);
    static void refresh(Context c){
        AppWidgetManager am=AppWidgetManager.getInstance(c);
        ComponentName name=new ComponentName(c,FitPlanCalendarWidget.class);
        int[] ids=am.getAppWidgetIds(name);
        for(int id:ids)render(c,am,id);
    }
    @Override public void onUpdate(Context c,AppWidgetManager am,int[] ids){
        for(int id:ids)render(c,am,id);
    }
    @Override public void onAppWidgetOptionsChanged(Context c,AppWidgetManager am,int id,Bundle options){
        super.onAppWidgetOptionsChanged(c,am,id,options);render(c,am,id);
    }
    private static String iso(Calendar c){
        return new SimpleDateFormat("yyyy-MM-dd",Locale.US).format(c.getTime());
    }
    private static void render(Context c,AppWidgetManager am,int id){
        RemoteViews root=new RemoteViews(c.getPackageName(),R.layout.fitplan_widget);
        Calendar now=Calendar.getInstance(),month=(Calendar)now.clone();
        month.set(Calendar.DAY_OF_MONTH,1);
        root.setTextViewText(R.id.widget_title,"FitPlan  ·  "+(month.get(Calendar.MONTH)+1)+"월");
        Intent intent=new Intent(c,MainActivity.class);
        intent.putExtra("open_schedule",true);
        intent.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP|Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pending=PendingIntent.getActivity(c,4000+id,intent,
                PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
        root.setOnClickPendingIntent(R.id.widget_root,pending);
        SharedPreferences prefs=c.getSharedPreferences("fitplan_widget",Context.MODE_PRIVATE);
        JSONObject data;
        try{data=new JSONObject(prefs.getString("schedule","{}"));}catch(Exception e){data=new JSONObject();}
        Set<String> done=new HashSet<>(),weekdays=new HashSet<>();
        JSONObject override=data.optJSONObject("overrides");
        JSONArray dates=data.optJSONArray("done"),chosen=data.optJSONArray("weekdays");
        if(dates!=null)for(int i=0;i<dates.length();i++)done.add(dates.optString(i));
        if(chosen!=null)for(int i=0;i<chosen.length();i++)weekdays.add(String.valueOf(chosen.optInt(i)));
        if(weekdays.isEmpty()){weekdays.add("1");weekdays.add("3");weekdays.add("5");}
        int height=am.getAppWidgetOptions(id).getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_HEIGHT,200);
        boolean compact=height<155;
        root.removeAllViews(R.id.widget_calendar);
        int firstDay=(month.get(Calendar.DAY_OF_WEEK)+6)%7;
        int count=compact?7:42;
        Calendar cursor=(Calendar)(compact?now:month).clone();
        if(compact){int offset=(cursor.get(Calendar.DAY_OF_WEEK)+6)%7;cursor.add(Calendar.DAY_OF_MONTH,-offset);}
        else cursor.add(Calendar.DAY_OF_MONTH,-firstDay);
        int completed=0;
        Calendar day=(Calendar)now.clone();
        Calendar last=(Calendar)now.clone();last.add(Calendar.DAY_OF_MONTH,7);
        String next="일정 없음";
        for(int i=0;i<8;i++){
            String key=iso(day);
            int wk=day.get(Calendar.DAY_OF_WEEK)-1;
            String overrideValue=override==null?"":override.optString(key,"");
            if(!done.contains(key)&&("planned".equals(overrideValue)||(!"rest".equals(overrideValue)&&weekdays.contains(String.valueOf(wk))))){
                next=(day.get(Calendar.MONTH)+1)+"/"+day.get(Calendar.DAY_OF_MONTH)+" 운동 예정";break;
            }
            day.add(Calendar.DAY_OF_MONTH,1);
        }
        root.setTextViewText(R.id.widget_summary,next);
        for(String key:done){
            if(key.startsWith(iso(month).substring(0,7)))completed++;
        }
        root.setTextViewText(R.id.widget_count,"완료 "+completed+"일");
        for(int row=0;row<count/7;row++){
            RemoteViews week=new RemoteViews(c.getPackageName(),R.layout.fitplan_widget_row);
            for(int col=0;col<7;col++){
                String key=iso(cursor);
                int weekday=cursor.get(Calendar.DAY_OF_WEEK)-1;
                String ov=override==null?"":override.optString(key,"");
                boolean completedDay=done.contains(key);
                boolean planned="planned".equals(ov)||(!"rest".equals(ov)&&weekdays.contains(String.valueOf(weekday)));
                RemoteViews cell=new RemoteViews(c.getPackageName(),R.layout.fitplan_widget_cell);
                String mark=completedDay?"●":planned?"○":"";
                cell.setTextViewText(R.id.widget_day,cursor.get(Calendar.DAY_OF_MONTH)+"\n"+mark);
                cell.setTextColor(R.id.widget_day,completedDay?GREEN:planned?WHITE:GRAY);
                if(key.equals(iso(now)))cell.setInt(R.id.widget_day,"setBackgroundResource",R.drawable.fitplan_widget_today);
                else if(!compact&&cursor.get(Calendar.MONTH)!=month.get(Calendar.MONTH))
                    cell.setInt(R.id.widget_day,"setAlpha",115);
                week.addView(R.id.widget_week_cells,cell);
                cursor.add(Calendar.DAY_OF_MONTH,1);
            }
            root.addView(R.id.widget_calendar,week);
        }
        am.updateAppWidget(id,root);
    }
}
