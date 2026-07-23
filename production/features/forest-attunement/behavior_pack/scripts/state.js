export const PROPERTY_ID = "ccoriginal_cc:forest_attunement_v1";
export const CURRENT_VERSION = 1;

export function decodeState(raw) {
  if (raw === undefined) return { kind: "empty", unlocked: false };
  if (raw === true) return { kind: "legacy", unlocked: true };
  if (raw === false) return { kind: "corrupt", unlocked: false, diagnostic: "legacy-false" };
  if (typeof raw !== "string") return { kind: "corrupt", unlocked: false, diagnostic: "unsupported-type" };
  let value;
  try {
    value = JSON.parse(raw);
  } catch {
    return { kind: "corrupt", unlocked: false, diagnostic: "invalid-json" };
  }
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return { kind: "corrupt", unlocked: false, diagnostic: "invalid-shape" };
  }
  if (value.version === undefined && value.unlocked === true) return { kind: "legacy", unlocked: true };
  if (!Number.isInteger(value.version)) return { kind: "corrupt", unlocked: false, diagnostic: "invalid-version" };
  if (value.version !== CURRENT_VERSION) {
    return { kind: "unknown", unlocked: false, diagnostic: `unknown-version-${value.version}` };
  }
  if (value.unlocked !== true) return { kind: "corrupt", unlocked: false, diagnostic: "invalid-unlock" };
  return { kind: "current", unlocked: true };
}

export function canonicalState() {
  return JSON.stringify({ version: CURRENT_VERSION, unlocked: true });
}

export function isForestAttuned(player) {
  const decoded = decodeState(player.getDynamicProperty(PROPERTY_ID));
  if (decoded.kind === "legacy") {
    try {
      player.setDynamicProperty(PROPERTY_ID, canonicalState());
      return true;
    } catch {
      return false;
    }
  }
  return decoded.kind === "current";
}

export function resetForestAttunement(player) {
  player.setDynamicProperty(PROPERTY_ID, undefined);
}
