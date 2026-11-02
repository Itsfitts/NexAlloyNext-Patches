package io.github.nexfusion.morphe.youtube.misc.engagement

import io.github.nexfusion.morphe.AccessFlags
import io.github.nexfusion.morphe.Fingerprint
import io.github.nexfusion.morphe.Opcode
import io.github.nexfusion.morphe.fieldAccess
import io.github.nexfusion.morphe.findClassDirect
import io.github.nexfusion.morphe.findFieldDirect
import io.github.nexfusion.morphe.findMethodDirect
import io.github.nexfusion.morphe.youtube.shared.EngagementPanelControllerFingerprint

internal object EngagementPanelUpdateFingerprint : Fingerprint(
    classFingerprint = EngagementPanelControllerFingerprint,
    accessFlags = listOf(AccessFlags.PRIVATE, AccessFlags.FINAL),
    returnType = "V",
    parameters = listOf("L", "Z"),
    filters = listOf(
        fieldAccess(
            opcode = Opcode.IGET_OBJECT,
            type = "Landroid/app/Activity;"
        )
    )
)

val panelInitFingerprint = findMethodDirect {
    panelClass().findMethod {
        matcher {
            name = "<init>"
        }
    }.single()
}

val panelIdField = findFieldDirect {
    panelClass().fields.single { it.typeName == "java.lang.String" }
}

val panelClass = findClassDirect {
    EngagementPanelControllerFingerprint.instructionMatches[3].instruction.classRef!!
}