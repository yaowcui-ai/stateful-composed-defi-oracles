export function buildFormalPlan(lock) {
  if (lock.status !== "FROZEN_PRE_EXECUTION" || lock.split_unit !== "episode") throw new Error("condition lock is not frozen at episode grain");
  const episodeIds = new Set(lock.episodes.map(x => x.episode_id));
  const plan = lock.conditions.map(row => {
    if (!episodeIds.has(row.episode_id)) throw new Error(`unknown episode: ${row.episode_id}`);
    return {...row, replacement_allowed:false};
  });
  if (new Set(plan.map(x => x.condition_id)).size !== plan.length) throw new Error("duplicate condition id");
  return plan;
}


export async function executePlanWith(plan, executor) {
  const failures = new Map();
  const output = [];
  for (const row of plan) {
    try {
      const result = await executor(row);
      if (failures.has(row.episode_id)) {
        output.push({...row, ...result, comparable:false, noncomparability_reason:`ancestor episode failure: ${failures.get(row.episode_id)}`});
      } else {
        output.push({...row, ...result});
      }
    } catch (error) {
      const reason = String(error.message || error);
      failures.set(row.episode_id, reason);
      output.push({...row, attempted:true, comparable:false, noncomparability_reason:reason, error:String(error)});
    }
  }
  return output;
}
