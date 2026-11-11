package com.fitplan.autocv196;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.net.Uri;
import android.os.Environment;
import android.os.ParcelFileDescriptor;
import java.io.File;
import java.io.FileNotFoundException;

/** Read-only, private installer handoff. Only the exact downloaded APK is served. */
public final class UpdateApkProvider extends ContentProvider {
    @Override public boolean onCreate(){return true;}
    @Override public String getType(Uri uri){return "application/vnd.android.package-archive";}
    @Override public ParcelFileDescriptor openFile(Uri uri,String mode) throws FileNotFoundException{
        if(!"r".equals(mode)||uri==null||!"/fitplan-update.apk".equals(uri.getPath()))
            throw new FileNotFoundException("Invalid update URI");
        File path=new File(getContext().getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS),"fitplan-update.apk");
        if(!path.isFile())throw new FileNotFoundException("No verified update");
        return ParcelFileDescriptor.open(path,ParcelFileDescriptor.MODE_READ_ONLY);
    }
    @Override public Cursor query(Uri u,String[] p,String s,String[] a,String o){return null;}
    @Override public Uri insert(Uri u,ContentValues v){throw new UnsupportedOperationException();}
    @Override public int update(Uri u,ContentValues v,String s,String[] a){throw new UnsupportedOperationException();}
    @Override public int delete(Uri u,String s,String[] a){throw new UnsupportedOperationException();}
}
