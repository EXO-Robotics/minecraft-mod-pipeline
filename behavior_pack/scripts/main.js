import { world, system } from "@minecraft/server";
import { startRuntime } from "./runtime.js";
import { registerWhisperwoodRegrowth } from "./whisperwood_regrowth.js";

system.beforeEvents.startup.subscribe(event => registerWhisperwoodRegrowth(event, world));
console.warn("[Aionbound Wave 1] runtime-ready-g8");
startRuntime();
