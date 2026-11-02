package io.github.nexfusion.morphe.youtube.misc.privacy

import io.github.nexfusion.morphe.shared.misc.privacy.SanitizeSharingLinks
import io.github.nexfusion.morphe.youtube.misc.settings.PreferenceScreen
import io.github.nexfusion.patch

val SanitizeSharingLinks = patch(
    name = "Sanitize sharing links",
    description = "Removes the tracking query parameters from shared links."
) {
    SanitizeSharingLinks(
        preferenceScreen = PreferenceScreen.MISC,
        replaceLinksWithShortener = true
    )
}