package progressive.form;
@interface ModContent { String kind(); String id(); }
@interface Behavior { String id(); String ownerKind(); String owner(); String trigger(); String actions(); String conditions() default ""; }
@interface UiIntent { String id(); String title(); String purpose(); String controls(); }
@ModContent(kind="block", id="progressive:selector_console")
@UiIntent(id="progressive:selector_form", title="Selector Console", purpose="Choose one processing mode", controls="smelt,compress,cancel")
@Behavior(id="progressive:selector_console/open", ownerKind="block", owner="progressive:selector_console", trigger="block_interact", actions="open_interaction_ui")
public final class Fixture {}
