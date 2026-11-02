package io.github.nexfusion.morphe.youtube.interaction.downloads

import io.github.nexfusion.morphe.AccessFlags
import io.github.nexfusion.morphe.Fingerprint
import io.github.nexfusion.morphe.anyInstruction
import io.github.nexfusion.morphe.string

internal object OfflineVideoEndpointFingerprint : Fingerprint(
    accessFlags = listOf(AccessFlags.PUBLIC, AccessFlags.FINAL),
    returnType = "V",
    parameters = listOf(
        "Ljava/util/Map;",
        "L",
        "Ljava/lang/String", // VideoId
        "L",
    ),
    filters = listOf(
        anyInstruction(
            string("Unsupported Offline Video Action: "), // 21.14 and lower
            string("Unsupported Offline Video Action: %s") // 21.15+
        )
    ),
    custom = {
        addUsingString("Unsupported Offline Video Action: ")
    }
)
