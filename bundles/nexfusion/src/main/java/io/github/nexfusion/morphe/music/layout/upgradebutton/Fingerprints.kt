package io.github.nexfusion.morphe.music.layout.upgradebutton

import io.github.nexfusion.morphe.AccessFlags
import io.github.nexfusion.morphe.Opcode
import io.github.nexfusion.morphe.fingerprint

internal val pivotBarConstructorFingerprint = fingerprint {
    accessFlags(AccessFlags.PUBLIC, AccessFlags.CONSTRUCTOR)
    returns("V")
    parameters("L", "Z")
    opcodes(
        Opcode.INVOKE_INTERFACE,
        Opcode.GOTO,
        Opcode.IPUT_OBJECT,
        Opcode.RETURN_VOID
    )
}
