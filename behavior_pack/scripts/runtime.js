import { world, system, ItemStack, EquipmentSlot, EntityComponentTypes } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";
import { COMBINED_BUDGETS, RuntimeArbiter } from "./budgets.js";
import { createStateService } from "./state.js";
import { createInteractionRouter } from "./router.js";
import { codexEventsForStructureActivation } from "./catalog.js";
import { createCodexService } from "./codex.js";
import { createCombatService } from "./combat.js";
import { createDeviceService } from "./devices.js";
import { createEncounterService } from "./encounters.js";
import { createChaosService } from "./chaos.js";
import { createStructureService } from "./structures.js";
import { createThornCourtService } from "./thorn_court.js";
import { createWhisperwoodRewardHooks } from "./whisperwood_rewards.js";

export function createRuntime(platform = { world, system, ItemStack, EquipmentSlot, EntityComponentTypes, ActionFormData }) {
  const arbiter = new RuntimeArbiter();
  const state = createStateService({ world: platform.world, system: platform.system, notify: (player, text) => player.sendMessage(`§7[Aionbound] ${text}`) });

  function consumeOne(player, typeId) {
    const container = player.getComponent("minecraft:inventory")?.container, slot = player.selectedSlotIndex, item = container?.getItem(slot);
    if (!item || item.typeId !== typeId) return false;
    if (item.amount > 1) { item.amount--; container.setItem(slot, item); } else container.setItem(slot, undefined);
    return true;
  }
  function boundedEntities(typeId) {
    const output = []; arbiter.beginTick(platform.system.currentTick);
    for (const dimensionId of ["overworld", "nether", "the_end"]) {
      for (const entity of platform.world.getDimension(dimensionId).getEntities(typeId ? { type: typeId } : {})) {
        if (!arbiter.spend("entityQuery")) return output;
        output.push(entity);
      }
    }
    return output;
  }

  const codex = createCodexService({ state, ActionFormData: platform.ActionFormData });
  const structures = createStructureService({ ...platform, state, arbiter, consumeOne });
  const thornCourtRewardHooks = platform.thornCourtRewardHooks ?? createWhisperwoodRewardHooks({ ItemStack: platform.ItemStack, random: platform.random ?? Math.random });
  const thornCourt = createThornCourtService({
    ...platform,
    state,
    boundedEntities,
    rewardHooks: thornCourtRewardHooks,
    codexHooks: {
      onPull: player => codex.discover(player, "codex:ww:boss:thorn_court:encountered"),
      onTerminalCredit: player => {
        codex.discover(player, "codex:ww:boss:thorn_court:defeated");
        codex.discover(player, "codex:ww:equipment:thorn_stalker_skull:earned");
        codex.discover(player, "codex:ww:progression:whisperwood_chapter:seal_credit");
      },
    },
  });
  const combat = createCombatService({ ...platform, state, arbiter, boundedEntities, consumeOne });
  const encounters = createEncounterService({ ...platform, state, boundedEntities, consumeOne });
  const devices = createDeviceService({ ...platform, state, arbiter, consumeOne });
  const chaos = createChaosService({ ...platform, state, arbiter });

  const bossAction = action => context => encounters.routeBoss(action, context);
  const blockActions = {
    guidance: ({ player }) => codex.guidance(player),
    codex: ({ player }) => codex.use(player, "aionbound:trophy_codex"),
    pocket: context => structures.useCell(context.player, context.block, context.itemType),
    chaos: context => chaos.use(context),
    safe_storage_notice: ({ player }) => state.warn(player, "Use the crafted vanilla chest for authoritative safe storage."),
    site_reward: context => structures.claimSite(context),
    ww_progression_site: context => {
      const activation = structures.activateProgressionSite(context);
      if (!activation) return false;
      for (const eventId of codexEventsForStructureActivation(activation.site)) codex.discover(context.player, eventId);
      if (activation.site === "broken_wagon") codex.discover(context.player, "codex:ww:progression:ashen_rumor:broken_wagon_activated");
      if (activation.action === "boss:thorn_court") thornCourt.begin(context.player, context.block.location);
      return true;
    },
    "device:salvage": context => devices.useSalvage(context),
    "device:press": context => devices.usePress(context),
    "device:survey": context => devices.useSurvey(context),
    "boss:foundry": bossAction("boss:foundry"),
    "boss:royal_moth": bossAction("boss:royal_moth"),
    "boss:basalt": bossAction("boss:basalt"),
    "boss:rift": bossAction("boss:rift"),
    "boss:twinbond": bossAction("boss:twinbond"),
    "boss:thorn_court": ({ player, block }) => thornCourt.begin(player, block.location),
  };
  const itemActions = {
    familiar: ({ player }) => combat.useBarkling(player), stripvein: ({ player }) => structures.useStrip(player),
    ray: ({ player }) => combat.useRay(player), mount: ({ player }) => combat.useWhistle(player),
    codex: ({ player, itemStack }) => codex.use(player, itemStack.typeId), edge_stamp: ({ player }) => state.stamp(player, "edge:assembled"),
    ranged: ({ player, itemStack }) => combat.useRanged(player, itemStack.typeId),
    consumable: ({ player, itemStack }) => combat.useConsumable(player, itemStack.typeId),
    whisperwood_utility: ({ player, itemStack }) => combat.useWhisperwoodUtility(player, itemStack.typeId),
    accessory_pulse: ({ player, itemStack }) => combat.accessoryPulse(player, itemStack.typeId),
  };
  const entityActions = {
    waykeeper_notice: ({ player }) => state.warn(player, "Use ordinary interact to mount; movement input directly controls your courser."),
  };
  const router = createInteractionRouter({ discover: state.stamp, codexDiscover: codex.discover, blockActions, itemActions, entityActions });

  function callback(run) {
    arbiter.beginTick(platform.system.currentTick);
    if (!arbiter.spend("callbacksTick")) return false;
    run(); return true;
  }
  function reconcile() {
    encounters.reconcile(); thornCourt.reconcile(); structures.reconcile(); chaos.reconcile();
    for (const player of platform.world.getAllPlayers()) state.playerState(player);
  }
  function tick() { callback(() => {
    if (platform.system.currentTick % 100 === 0) {
      combat.reconcileNaturalEntities();
      for (const player of platform.world.getAllPlayers()) codex.reconcileOwnedItems(player);
    }
    if (platform.system.currentTick % 20 === 0) combat.tickPlayers();
    thornCourt.tick(); structures.tick(); devices.tick(); chaos.tick();
  }); }

  function start() {
    arbiter.defer(platform.system, reconcile);
    platform.world.afterEvents.itemUse.subscribe(event => callback(() => router.dispatchItem({ player: event.source, itemStack: event.itemStack })));
    platform.world.afterEvents.itemCompleteUse.subscribe(event => callback(() => router.dispatchCompletedItem({ player: event.source, itemStack: event.itemStack })));
    platform.world.afterEvents.playerBreakBlock.subscribe(event => callback(() => router.dispatchBlockDiscovery({
      player: event.player,
      typeId: event.brokenBlockPermutation?.type?.id,
    })));
    platform.world.beforeEvents.playerInteractWithBlock.subscribe(event => {
      // This lock must execute synchronously even when ordinary callback budget
      // is exhausted, or vanilla interaction could bypass the pre-clear cache.
      if (thornCourtRewardHooks.guardArenaCacheInteraction?.(event) === true) return;
      callback(() => {
        if (event.block.typeId === "aionbound:chaos_crate_t0") event.cancel = true;
        const context = { player: event.player, block: event.block, itemType: event.itemStack?.typeId };
        if (!arbiter.defer(platform.system, () => router.dispatchBlock(context))) state.warn(event.player, "Interaction scheduler capacity is full.");
      });
    });
    platform.world.afterEvents.playerInteractWithEntity.subscribe(event => callback(() => router.dispatchEntityInteraction({ player: event.player, target: event.target, itemStack: event.itemStack })));
    platform.world.afterEvents.entityHitEntity.subscribe(event => callback(() => combat.mountStep(event)));
    platform.world.afterEvents.entityHurt.subscribe(event => callback(() => { combat.routeMeleeHurt(event); combat.handlePlayerHurt(event); }));
    platform.world.afterEvents.entityDie.subscribe(event => callback(() => {
      router.dispatchEntityDeathEvent(event);
      thornCourt.bossDeath(event);
      encounters.bossDeath(event);
      combat.glasswingDeath(event);
    }));
    platform.system.runInterval(tick, 1);
  }
  return { start, reconcile, tick, state, arbiter, router, codex, combat, devices, encounters, thornCourt, chaos, structures, budgets: COMBINED_BUDGETS };
}

export function startRuntime() { return createRuntime().start(); }
