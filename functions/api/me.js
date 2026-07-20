import { json, currentUser, publicUser, requireUser } from "../_shared.js";
export async function onRequestGet({ request, env }) { const user = await currentUser(request, env); return requireUser(user) || json({ user: publicUser(user) }); }
