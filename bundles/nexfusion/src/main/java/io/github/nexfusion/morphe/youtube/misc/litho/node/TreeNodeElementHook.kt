package io.github.nexfusion.morphe.youtube.misc.litho.node

import io.github.nexfusion.morphe.shared.misc.litho.context.conversionContextPatch
import io.github.nexfusion.morphe.shared.misc.litho.node.createTreeNodeElementHookPatch
import io.github.nexfusion.patch

val TreeNodeElementHook = createTreeNodeElementHookPatch(
    patch {},
    conversionContextPatch,
    false,
    useLegacyContextRegister = { false }
)