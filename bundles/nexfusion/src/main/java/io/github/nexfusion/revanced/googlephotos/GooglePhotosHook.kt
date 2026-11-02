package io.github.nexfusion.revanced.googlephotos

import io.github.nexfusion.revanced.googlephotos.misc.backup.EnableDCIMFoldersBackupControl
import io.github.nexfusion.revanced.googlephotos.misc.features.SpoofFeaturesPatch

val GooglePhotosPatches = arrayOf(
    SpoofFeaturesPatch,
    EnableDCIMFoldersBackupControl,
)