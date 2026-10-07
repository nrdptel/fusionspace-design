// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// Posts the reference Live Update (product/mobile/compose/FsLiveUpdate.kt) for Flight 04 under the main.
package co.fusionspace.sample

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.util.Log
import co.fusionspace.design.FsFlightNow
import co.fusionspace.design.FsLiveUpdate

private const val CHANNEL = "flight"
private const val ID = 4

fun postLiveUpdate(context: Context) {
    val nm = context.getSystemService(NotificationManager::class.java)
    nm.createNotificationChannel(NotificationChannel(CHANNEL, "Flight tracking", NotificationManager.IMPORTANCE_DEFAULT))
    val now = FsFlightNow(
        flight = "Flight 04", phase = "under the main",
        altitudeFt = 612, verticalFtS = -18, distanceFt = 1352, bearingTrue = 62,
        liftoffEpochMs = System.currentTimeMillis() - 62_000,
        burnoutS = 2.1f, apogeeS = 16.4f, mainS = 48.0f, expectedLandingS = 82.0f, nowS = 62.0f,
    )
    val notification = FsLiveUpdate.build(context, CHANNEL, R.drawable.fs_rocket, R.drawable.fs_rocket, now)
    Log.i("FsSample", "canPostPromotedNotifications=${nm.canPostPromotedNotifications()} hasPromotable=${notification.hasPromotableCharacteristics()}")
    nm.notify(ID, notification)
}
