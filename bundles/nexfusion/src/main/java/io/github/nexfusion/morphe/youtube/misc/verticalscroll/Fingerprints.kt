package io.github.nexfusion.morphe.youtube.misc.verticalscroll

import io.github.nexfusion.morphe.AccessFlags
import io.github.nexfusion.morphe.Fingerprint
import io.github.nexfusion.morphe.InstructionLocation.MatchAfterImmediately
import io.github.nexfusion.morphe.Opcode
import io.github.nexfusion.morphe.findMethodDirect
import io.github.nexfusion.morphe.methodCall
import io.github.nexfusion.morphe.opcode

internal object CanScrollVerticallyFingerprint : Fingerprint(
    definingClass = "Landroidx/swiperefreshlayout/widget/SwipeRefreshLayout;",
    accessFlags = listOf(AccessFlags.PUBLIC, AccessFlags.FINAL),
    returnType = "Z",
    parameters = listOf(),
    filters = listOf(
        methodCall(smali = "Landroid/view/View;->canScrollVertically(I)Z"),
        opcode(Opcode.MOVE_RESULT, location = MatchAfterImmediately())
    )
)

val canScrollVerticallyMethod = findMethodDirect {
    CanScrollVerticallyFingerprint.instructionMatches.first().instruction.methodRef!!
}
