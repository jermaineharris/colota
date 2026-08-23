/**
 * Copyright (C) 2026 Max Dietrich
 * Licensed under the GNU AGPLv3. See LICENSE in the project root for details.
 */

package com.huttsmedia.huttstracking

import android.app.Application
import com.facebook.react.PackageList
import com.facebook.react.ReactApplication
import com.facebook.react.ReactHost
import com.facebook.react.ReactPackage
import com.facebook.react.ReactNativeApplicationEntryPoint.loadReactNative
import com.facebook.react.defaults.DefaultReactHost.getDefaultReactHost
import com.huttsmedia.huttstracking.backup.BackupOrphanCleanup
import com.huttsmedia.huttstracking.bridge.LocationServicePackage
import com.huttsmedia.huttstracking.util.FileLoggerInitializer
import com.huttsmedia.huttstracking.util.MemoryPressureLogger

class MainApplication : Application(), ReactApplication {

    override val reactHost: ReactHost by lazy {
        getDefaultReactHost(
            context = applicationContext,
            packageList = PackageList(this).packages + listOf(LocationServicePackage())
        )
    }

    override fun onCreate() {
        super.onCreate()
        FileLoggerInitializer.start(this)
        loadReactNative(this)
        BackupOrphanCleanup.start(this)
    }

    override fun onTrimMemory(level: Int) {
        super.onTrimMemory(level)
        MemoryPressureLogger.log(level)
    }
}
