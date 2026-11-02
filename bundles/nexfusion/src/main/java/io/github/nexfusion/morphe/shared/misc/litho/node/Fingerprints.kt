package io.github.nexfusion.morphe.shared.misc.litho.node

import io.github.nexfusion.morphe.AccessFlags
import io.github.nexfusion.morphe.Fingerprint
import io.github.nexfusion.morphe.Opcode
import io.github.nexfusion.morphe.methodCall
import io.github.nexfusion.morphe.youtube.layout.hide.general.ParseElementFromBufferFingerprint

internal object TreeNodeResultListFingerprint : Fingerprint(
    classFingerprint = ParseElementFromBufferFingerprint,
    accessFlags = listOf(AccessFlags.PRIVATE, AccessFlags.FINAL),
    returnType = "Ljava/util/List;",
    filters = listOf(
        methodCall(name = "nCopies", opcode = Opcode.INVOKE_STATIC),
    )
)
