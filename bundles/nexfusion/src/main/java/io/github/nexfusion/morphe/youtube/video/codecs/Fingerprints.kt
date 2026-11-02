package io.github.nexfusion.morphe.youtube.video.codecs

import io.github.nexfusion.morphe.AccessFlags
import io.github.nexfusion.morphe.Fingerprint

internal object Vp9CapabilityFingerprint : Fingerprint(
    accessFlags = listOf(AccessFlags.PUBLIC, AccessFlags.FINAL),
    returnType = "Z",
    strings = listOf(
        "vp9_supported",
        "video/x-vnd.on2.vp9"
    )
)
