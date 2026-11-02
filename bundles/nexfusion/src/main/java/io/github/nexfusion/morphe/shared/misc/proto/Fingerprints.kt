package io.github.nexfusion.morphe.shared.misc.proto

import io.github.nexfusion.morphe.AccessFlags
import io.github.nexfusion.morphe.Fingerprint
import io.github.nexfusion.morphe.Opcode
import io.github.nexfusion.morphe.StrictQuery
import io.github.nexfusion.morphe.checkCast
import io.github.nexfusion.morphe.methodCall
import io.github.nexfusion.morphe.string

@StrictQuery
internal object NewElementProtoParserFingerprint : Fingerprint(
    classFingerprint = ProtoStuffReflectionFingerprint,
    accessFlags = listOf(AccessFlags.STATIC),
    parameters = listOf("L"),
    returnType = "[B",
    filters = listOf(
        checkCast("[B")
    )
)

private object ProtoStuffReflectionFingerprint : Fingerprint(
    accessFlags = listOf(AccessFlags.PRIVATE, AccessFlags.STATIC),
    parameters = listOf(),
    returnType = "Ljava/lang/reflect/Field;",
    filters = listOf(
        string("buf"),
        methodCall(
            opcode = Opcode.INVOKE_VIRTUAL,
            name = "getDeclaredField"
        ),
        methodCall(
            opcode = Opcode.INVOKE_VIRTUAL,
            name = "setAccessible"
        )
    )
)
