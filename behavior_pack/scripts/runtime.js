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
import { createAshenStructureRewardHooks } from "./ashen_structure_rewards.js";
import { createCrystalRewardHooks } from "./crystal_rewards.js";
import { createPearlDepthsService } from "./pearl_depths.js";
import { createCrystalEquipmentService } from "./crystal_equipment.js";
import { createSkyreachRewardHooks } from "./skyreach_rewards.js";
import { createStormNestService } from "./storm_nest.js";
import { createTwinbondService } from "./twinbond.js";

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
  const ashenStructureRewardHooks = platform.ashenStructureRewardHooks ?? createAshenStructureRewardHooks({ ItemStack: platform.ItemStack, random: platform.random ?? Math.random });
  const crystalRewardHooks = platform.crystalRewardHooks ?? createCrystalRewardHooks({ ItemStack: platform.ItemStack, state, random: platform.random ?? Math.random });
  const skyreachRewardHooks = platform.skyreachRewardHooks ?? createSkyreachRewardHooks({ ItemStack: platform.ItemStack, random: platform.random ?? Math.random });
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
  const pearlDepths = createPearlDepthsService({
    ...platform,
    state,
    boundedEntities,
    rewardHooks: crystalRewardHooks,
    codexHooks: {
      onPull: player => {
        codex.discover(player, "codex:cm:creature:marsh_wight:encountered");
        codex.discover(player, "codex:cm:boss:pearl_depths:encountered");
      },
      onTerminalCredit: player => {
        codex.discover(player, "codex:cm:creature:marsh_wight:defeated");
        codex.discover(player, "codex:cm:boss:pearl_depths:defeated");
        codex.discover(player, "codex:cm:equipment:marsh_wight_mask:obtained");
        codex.discover(player, "codex:cm:progression:crystal_marsh_chapter:seal_credit");
      },
    },
  });
  const stormNest = createStormNestService({
    ...platform,
    state,
    boundedEntities,
    rewardHooks: skyreachRewardHooks,
    codexHooks: {
      onPull: player => codex.discover(player, "codex:sr:boss:storm_nest:encountered"),
      onTerminalCredit: player => {
        codex.discover(player, "codex:sr:boss:storm_nest:defeated");
        codex.discover(player, "codex:sr:equipment:storm_pinion:first_owned");
        codex.discover(player, "codex:sr:progression:skyreach_chapter:seal_credit");
      },
    },
  });
  const combat = createCombatService({ ...platform, state, arbiter, boundedEntities, consumeOne });
  const crystalEquipment = createCrystalEquipmentService({ ...platform, state, arbiter });
  const encounters = createEncounterService({ ...platform, state, boundedEntities, consumeOne });
  const twinbond = createTwinbondService({
    ...platform,
    state,
    boundedEntities,
    codexHooks: {
      onPull: player => state.stamp(player, "codex:finale:twinbond:encountered"),
      onTerminalCredit: player => state.stamp(player, "codex:finale:twinbond:completed"),
      onMastery: player => state.stamp(player, "codex:finale:twinbond:mastery"),
    },
  });
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
    "boss:twinbond": ({ player, block }) => twinbond.blockInteraction(player, block),
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
    crystal_ranged: ({ player, itemStack }) => crystalEquipment.useRanged(player, itemStack.typeId),
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
    encounters.reconcile(); thornCourt.reconcile(); pearlDepths.reconcile(); stormNest.reconcile(); twinbond.reconcile(); structures.reconcile(); chaos.reconcile();
    for (const player of platform.world.getAllPlayers()) state.playerState(player);
  }
  function tick() { callback(() => {
    if (platform.system.currentTick % 100 === 0) {
      combat.reconcileNaturalEntities();
      for (const player of platform.world.getAllPlayers()) codex.reconcileOwnedItems(player);
    }
    if (platform.system.currentTick % 20 === 0) {
      combat.tickPlayers();
      for (const player of platform.world.getAllPlayers()) crystalEquipment.tickPlayer(player);
    }
    thornCourt.tick(); pearlDepths.tick(); stormNest.tick(); twinbond.tick(); structures.tick(); devices.tick(); chaos.tick();
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
      if (ashenStructureRewardHooks.guardArenaCacheInteraction?.(event) === true) return;
      if (crystalRewardHooks.guardArenaCacheInteraction?.(event) === true) return;
      callback(() => {
        if (event.block.typeId === "aionbound:chaos_crate_t0") event.cancel = true;
        const activation = ashenStructureRewardHooks.identifyStructureActivation?.(event.block);
        const crystalActivation = crystalRewardHooks.identifyStructureActivation?.(event.block);
        const context = { player: event.player, block: event.block, itemType: event.itemStack?.typeId };
        if (!arbiter.defer(platform.system, () => {
          if (activation) {
            state.stamp(event.player, activation.stamp);
            for (const eventId of codexEventsForStructureActivation(activation.structure)) codex.discover(event.player, eventId);
            if (activation.structure === "burned_camp") codex.discover(event.player, "codex:ah:progression:crystal_marsh_rumor:burned_camp_visited");
            if (activation.structure === "char_wagon") codex.discover(event.player, "codex:ah:progression:crystal_marsh_rumor:char_wagon_visited");
          }
          if (crystalActivation) {
            state.stamp(event.player, crystalActivation.stamp);
            for (const eventId of codexEventsForStructureActivation(crystalActivation.structure)) codex.discover(event.player, eventId);
            if (crystalActivation.structure === "ancient_boat") codex.discover(event.player, "codex:cm:progression:skyreach_rumor:ancient_boat_visited");
            if (crystalActivation.structure === "ruined_observatory") codex.discover(event.player, "codex:cm:progression:skyreach_rumor:ruined_observatory_visited");
            if (crystalActivation.structure === "sunken_shrine" || crystalActivation.structure === "deep_pool_entrance") pearlDepths.blockInteraction(event.player, event.block);
          }
          if (stormNest.blockInteraction(event.player, event.block)) {
            codex.discover(event.player, "codex:sr:structure:nest_platform:recognized_structure_visit");
          }
          router.dispatchBlock(context);
        })) state.warn(event.player, "Interaction scheduler capacity is full.");
      });
    });
    platform.world.afterEvents.playerInteractWithEntity.subscribe(event => callback(() => router.dispatchEntityInteraction({ player: event.player, target: event.target, itemStack: event.itemStack })));
    platform.world.afterEvents.entityHitEntity.subscribe(event => callback(() => combat.mountStep(event)));
    platform.world.afterEvents.entityHurt.subscribe(event => callback(() => { twinbond.handleHurt(event); combat.routeMeleeHurt(event); combat.handlePlayerHurt(event); }));
    platform.world.afterEvents.entityDie.subscribe(event => callback(() => {
      router.dispatchEntityDeathEvent(event);
      thornCourt.bossDeath(event);
      pearlDepths.bossDeath(event);
      stormNest.bossDeath(event);
      twinbond.bossDeath(event);
      encounters.bossDeath(event);
      combat.glasswingDeath(event);
    }));
    platform.system.runInterval(tick, 1);
  }
  return { start, reconcile, tick, state, arbiter, router, codex, combat, crystalEquipment, devices, encounters, thornCourt, pearlDepths, stormNest, twinbond, crystalRewardHooks, skyreachRewardHooks, ashenStructureRewardHooks, chaos, structures, budgets: COMBINED_BUDGETS };
}

export function startRuntime() { return createRuntime().start(); }
