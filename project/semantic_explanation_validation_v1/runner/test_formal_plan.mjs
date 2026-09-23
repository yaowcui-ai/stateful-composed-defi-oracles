import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { buildFormalPlan, executePlanWith } from "./formal_plan.mjs";


const HERE = path.dirname(fileURLToPath(import.meta.url));
const conditions = JSON.parse(fs.readFileSync(path.resolve(HERE, "..", "01_protocol", "conditions.json"), "utf8"));


test("formal plan freezes fifty unique conditions in twenty-five episodes", () => {
  const plan = buildFormalPlan(conditions);
  assert.equal(plan.length, 50);
  assert.equal(new Set(plan.map(x => x.condition_id)).size, 50);
  assert.equal(new Set(plan.map(x => x.episode_id)).size, 25);
  assert.ok(plan.every(x => x.replacement_allowed === false));
});


test("executor attempts every row exactly once and poisons episode descendants", async () => {
  const plan = buildFormalPlan(conditions).filter(x => ["FH3A", "FH3B", "VH1A"].includes(x.condition_id));
  const seen = [];
  const rows = await executePlanWith(plan, async row => {
    seen.push(row.condition_id);
    if (row.condition_id === "FH3A") throw new Error("invalid shared history");
    return {comparable:true, observation:{return:["1"]}};
  });
  assert.deepEqual(seen.sort(), ["FH3A", "FH3B", "VH1A"]);
  assert.equal(rows.find(x => x.condition_id === "FH3A").comparable, false);
  assert.equal(rows.find(x => x.condition_id === "FH3B").comparable, false);
  assert.equal(rows.find(x => x.condition_id === "VH1A").comparable, true);
});


test("plan exposes no result-driven substitution hook", () => {
  const plan = buildFormalPlan(conditions);
  assert.ok(plan.every(x => !("replacement" in x) && !("on_failure_select" in x)));
});
