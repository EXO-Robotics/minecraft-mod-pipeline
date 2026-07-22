package progressive.renderer;
@interface ModContent { String kind(); String id(); }
@interface Unsupported { String feature(); String reason(); }
@ModContent(kind="item", id="progressive:shader_prism")
@Unsupported(feature="custom_renderer", reason="Java OpenGL shader and render-layer injection have no native Add-On equivalent")
public final class Fixture {}
