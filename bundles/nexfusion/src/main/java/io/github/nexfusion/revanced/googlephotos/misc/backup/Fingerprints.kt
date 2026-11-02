package io.github.nexfusion.revanced.googlephotos.misc.backup

import io.github.nexfusion.morphe.Fingerprint

internal object isDCIMFolderBackupControlMethod : Fingerprint(
    strings = listOf(
        "/dcim",
        "/mars_files/"
    ),
    parameters = listOf("Ljava/lang/String;"),
    returnType = "Z"
)