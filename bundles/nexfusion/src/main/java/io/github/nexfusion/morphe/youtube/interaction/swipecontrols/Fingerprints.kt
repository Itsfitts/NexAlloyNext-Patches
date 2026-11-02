package io.github.nexfusion.morphe.youtube.interaction.swipecontrols

import io.github.nexfusion.morphe.AccessFlags
import io.github.nexfusion.morphe.Fingerprint
import io.github.nexfusion.morphe.Opcode
import io.github.nexfusion.morphe.StrictQuery
import io.github.nexfusion.morphe.fieldAccess
import io.github.nexfusion.morphe.findFieldDirect
import io.github.nexfusion.morphe.literal
import io.github.nexfusion.morphe.methodCall
import io.github.nexfusion.morphe.opcode

@StrictQuery
internal object PlayerOverlayContainerFingerprint : Fingerprint(
    accessFlags = listOf(AccessFlags.PUBLIC, AccessFlags.FINAL),
    returnType = $$"Landroid/view/ViewGroup$LayoutParams;",
    parameters = listOf(),
    filters = listOf(
        opcode(Opcode.NEW_INSTANCE),
        literal(-1),
        fieldAccess(
            opcode = Opcode.IGET_BOOLEAN,
            definingClass = "this"
        ),
        methodCall(
            opcode = Opcode.INVOKE_DIRECT,
            name = "<init>",
            parameters = listOf("I", "I", "Z")
        )
    ),
    custom = {
        addUsingField { type = "boolean" }
    }
)

val PlayerOverlayNameField = findFieldDirect {
    PlayerOverlayContainerFingerprint().declaredClass!!.fields.first { it.typeName == "java.lang.String" }
}