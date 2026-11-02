package io.github.nexfusion.morphe.youtube.video.audio

import io.github.nexfusion.morphe.Fingerprint
import io.github.nexfusion.morphe.InstructionLocation.MatchAfterImmediately
import io.github.nexfusion.morphe.Opcode
import io.github.nexfusion.morphe.methodCall
import io.github.nexfusion.morphe.opcode
import io.github.nexfusion.morphe.string


/**
 * Media3 DefaultAudioSink, where the audio session id of a newly created AudioTrack is read.
 */
internal object AudioTrackSessionIdFingerprint : Fingerprint(
    classFingerprint = Fingerprint(
        filters = listOf(
            string("ExoPlayer:AudioTrackReleaseThread")
        )
    ),
    filters = listOf(
        methodCall(smali = "Landroid/media/AudioTrack;->getAudioSessionId()I"),
        opcode(Opcode.MOVE_RESULT, location = MatchAfterImmediately())
    )
)
