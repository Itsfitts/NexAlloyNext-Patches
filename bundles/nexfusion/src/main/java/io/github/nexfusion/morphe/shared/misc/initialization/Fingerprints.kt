package io.github.nexfusion.morphe.shared.misc.initialization

import io.github.nexfusion.morphe.AccessFlags
import io.github.nexfusion.morphe.Fingerprint
import io.github.nexfusion.morphe.Opcode
import io.github.nexfusion.morphe.findMethodDirect
import io.github.nexfusion.morphe.indexOfFirstInstructionReversed
import io.github.nexfusion.morphe.methodCall
import io.github.nexfusion.morphe.string

internal object GlobalConfigGroupFingerprint : Fingerprint(
    accessFlags = listOf(AccessFlags.PUBLIC, AccessFlags.FINAL),
    returnType = "V",
    filters = listOf(
        methodCall(
            opcode = Opcode.INVOKE_VIRTUAL,
            smali = "Ljava/util/concurrent/locks/ReentrantLock;->lock()V"
        ),
        string(string = "com.google.android.libraries.youtube.innertube.cold_stored_timestamp"),
        methodCall(
            opcode = Opcode.INVOKE_INTERFACE,
            name = "putLong"
        )
    )
)

val handleColdFingerprint = findMethodDirect {
    val method = GlobalConfigGroupFingerprint()
    val matches = GlobalConfigGroupFingerprint.matchOrNull(method)?.instructionMatches!!
    val str_index = matches[2].instruction.index

    val index = method.indexOfFirstInstructionReversed (str_index) {
        this.opcode == Opcode.INVOKE_STATIC.opCode
    }

    method.instructions[index].methodRef!!
}