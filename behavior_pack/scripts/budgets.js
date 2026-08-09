export const COMBINED_BUDGETS = Object.freeze({
  callbacksTick: 96,
  entityQuery: 128,
  schedulerBacklog: 96,
  worldEditsTick: 48,
  particlesAction: 16,
  projectilesPlayer: 4,
  naturalEntitiesTarget: 40,
  bossesWorld: 3,
  twinbondMax: 2,
  mountsWorld: 12,
  familiarsWorld: 24,
  chaosActiveWorld: 1,
  chaosEntitiesEvent: 6,
  chaosBlocksEvent: 48,
  chaosCleanupTicks: 1200,
  devicesWorld: 24,
  deviceOpsTick: 8,
  deviceIntervalTicks: 20,
  structuresQueued: 4,
  structuresActive: 1,
  structureBlocks: 4096,
  cellJobs: 1,
  cellBlocks: 384,
  cellEditsTick: 16,
  stripJobs: 3,
  stripBlocks: 96,
  stripRadius: 4,
  stripCooldown: 160,
  rayRange: 24,
  rayCooldown: 30,
  rayParticles: 12,
  discoveries: 128,
  journalTerminal: 64,
  playerBytes: 8192,
  worldBytes: 49152,
  chaosMinute: 2,
  chaosCooldown: 1800,
});

export class RuntimeArbiter {
  constructor(limits = COMBINED_BUDGETS) {
    this.limits = limits;
    this.tick = -1;
    this.used = Object.create(null);
    this.active = Object.create(null);
    this.backlog = 0;
  }

  beginTick(tick) {
    if (tick !== this.tick) { this.tick = tick; this.used = Object.create(null); }
  }

  spend(name, amount = 1) {
    const limit = this.limits[name];
    if (!Number.isFinite(limit) || amount < 0) return false;
    const next = (this.used[name] ?? 0) + amount;
    if (next > limit) return false;
    this.used[name] = next;
    return true;
  }

  admit(name, limitName, amount = 1) {
    const limit = this.limits[limitName];
    const next = (this.active[name] ?? 0) + amount;
    if (!Number.isFinite(limit) || amount < 0 || next > limit) return false;
    this.active[name] = next;
    return true;
  }

  release(name, amount = 1) { this.active[name] = Math.max(0, (this.active[name] ?? 0) - amount); }

  defer(system, callback) {
    if (this.backlog >= this.limits.schedulerBacklog) return false;
    this.backlog++;
    system.run(() => { this.backlog = Math.max(0, this.backlog - 1); callback(); });
    return true;
  }
}
