import {
  actionsForEntityInteraction,
  codexRouteForBlockInteraction,
  codexRouteForEntityDeath,
  codexRouteForEntityInteraction,
  routeForBlock,
  routeForCompletedItem,
  routeForItem,
} from "./catalog.js";

export function createInteractionRouter({ discover, codexDiscover = () => false, blockActions, itemActions, entityActions = {} }) {
  function dispatchBlock(context) {
    const route = routeForBlock(context.block.typeId), codexEvents = codexRouteForBlockInteraction(context.block.typeId) ?? [];
    if (!route && !codexEvents.length) return false;
    for (const key of route?.discoveries ?? []) discover(context.player, key);
    for (const eventId of codexEvents) codexDiscover(context.player, eventId);
    for (const actionId of route?.actions ?? []) {
      const action = blockActions[actionId];
      if (action) action(context);
    }
    return true;
  }
  function dispatchItem(context) {
    const route = routeForItem(context.itemStack.typeId);
    const action = route && itemActions[route];
    if (!action) return false;
    action(context); return true;
  }
  function dispatchCompletedItem(context) {
    const route = routeForCompletedItem(context.itemStack.typeId), action = route && itemActions[route];
    if (!action) return false;
    action(context); return true;
  }
  function dispatchEntityInteraction(context) {
    const codexEvents = codexRouteForEntityInteraction(context.target.typeId) ?? [];
    const actions = actionsForEntityInteraction(context.target.typeId) ?? [];
    if (!codexEvents.length && !actions.length) return false;
    for (const eventId of codexEvents) codexDiscover(context.player, eventId);
    for (const actionId of actions) entityActions[actionId]?.(context);
    return true;
  }
  function dispatchEntityDeath(context) {
    const codexEvents = codexRouteForEntityDeath(context.entity.typeId) ?? [];
    if (!codexEvents.length) return false;
    for (const eventId of codexEvents) codexDiscover(context.player, eventId);
    return true;
  }
  function dispatchEntityDeathEvent(event) {
    const player = event.damageSource?.damagingEntity;
    if (player?.typeId !== "minecraft:player") return false;
    return dispatchEntityDeath({ player, entity: event.deadEntity });
  }
  return { dispatchBlock, dispatchItem, dispatchCompletedItem, dispatchEntityInteraction, dispatchEntityDeath, dispatchEntityDeathEvent };
}
