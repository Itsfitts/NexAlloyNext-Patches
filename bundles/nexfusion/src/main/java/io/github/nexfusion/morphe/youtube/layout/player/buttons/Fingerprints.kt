package io.github.nexfusion.morphe.youtube.layout.player.buttons

import io.github.nexfusion.morphe.AccessFlags
import io.github.nexfusion.morphe.Fingerprint
import io.github.nexfusion.morphe.InstructionLocation.MatchAfterImmediately
import io.github.nexfusion.morphe.Opcode
import io.github.nexfusion.morphe.ResourceType
import io.github.nexfusion.morphe.methodCall
import io.github.nexfusion.morphe.opcode
import io.github.nexfusion.morphe.resourceLiteral

internal object ExploderUIFullscreenButtonFingerprint : Fingerprint(
    classFingerprint = ExploderUIFullscreenButtonParentFingerprint,
    filters = listOf(
        resourceLiteral(ResourceType.ID, "fullscreen_button"),
        methodCall(smali = "Landroid/view/View;->findViewById(I)Landroid/view/View;"),
        opcode(Opcode.MOVE_RESULT_OBJECT, MatchAfterImmediately())
    )
)

internal object ExploderUIFullscreenButtonParentFingerprint : Fingerprint(
    accessFlags = listOf(AccessFlags.PUBLIC, AccessFlags.FINAL),
    returnType = "V",
    filters = listOf(
        resourceLiteral(ResourceType.ID, "time_bar_live_label")
    )
)
