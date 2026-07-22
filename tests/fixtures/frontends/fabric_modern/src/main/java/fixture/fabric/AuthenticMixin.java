package fixture.fabric;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.At;

@Mixin(Object.class)
public final class AuthenticMixin {
    @Inject(method = "tick", at = @At("HEAD"))
    private void injectTick() {}
}
