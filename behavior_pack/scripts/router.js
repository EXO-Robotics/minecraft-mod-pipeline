import { routeForBlock, routeForCompletedItem, routeForItem } from "./catalog.js";

export function createInteractionRouter({ discover, blockActions, itemActions }) {
  function dispatchBlock(context) {
    const route = routeForBlock(context.block.typeId);
    if (!route) return false;
    for (const key of route.discoveries) discover(context.player, key);
    for (const actionId of route.actions) {
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
  return { dispatchBlock, dispatchItem, dispatchCompletedItem };
}
