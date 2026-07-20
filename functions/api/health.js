import { json } from "../_shared.js";
export function onRequestGet({ env }) { return json({ ok: true, aiMode: env.AI_MODE || "mock", database: "d1" }); }
