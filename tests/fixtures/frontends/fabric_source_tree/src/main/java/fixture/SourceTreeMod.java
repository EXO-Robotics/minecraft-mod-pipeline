package fixture;

public final class SourceTreeMod {
    public static final Item KEY = registerItem("key", new KeyItem());
    private static Item registerItem(String id, Item item) {
        return Registry.register(Registries.ITEM, Identifier.of("source_tree", id), item);
    }
}

class KeyItem extends Item {
    @Override
    public ActionResult useOnBlock(ItemUsageContext context) {
        return ActionResult.PASS;
    }
}
