import { json, readJson, currentUser, publicUser, requireUser, analyzeWithAI, credits, nowText } from "../_shared.js";
export async function onRequestPost({ request, env }) {
  const user = await currentUser(request, env), error = requireUser(user); if (error) return error;
  if (!user.is_admin && user.free_uses <= 0 && user.credits < 100) return json({ error: "积分不足，请先充值" }, 402);
  try {
    const data = await readJson(request), [result, usage] = await analyzeWithAI(data, env), charge = usage.total_tokens ? credits(usage, env) : 0;
    let freeUses = user.free_uses, balance = user.credits; if (!user.is_admin) { if (freeUses > 0) { freeUses -= 1; } else balance = Math.max(0, balance - charge); }
    const title = `${data.position || "目标岗位"} 定制简历`, stamp = nowText();
    await env.DB.batch([
      env.DB.prepare("UPDATE users SET free_uses = ?, credits = ?, total_analyses = total_analyses + 1 WHERE id = ?").bind(freeUses, balance, user.id),
      env.DB.prepare("INSERT INTO resume_history (user_id,title,target_position,match_score,resume_text,created_at) VALUES (?,?,?,?,?,?)").bind(user.id, title, data.position || "目标岗位", result.diagnosis?.score || 0, result.finalResume || "", stamp),
      env.DB.prepare("INSERT INTO usage_logs (user_id,prompt_tokens,completion_tokens,credits_charged,model,created_at) VALUES (?,?,?,?,?,?)").bind(user.id, usage.prompt_tokens || 0, usage.completion_tokens || 0, charge, env.DEEPSEEK_MODEL || "deepseek-chat", stamp),
    ]);
    user.free_uses = freeUses; user.credits = balance; user.total_analyses += 1;
    return json({ result, user: publicUser(user), usage: { creditsCharged: charge } });
  } catch (e) { return json({ error: `AI 分析失败：${e.message}` }, 502); }
}
