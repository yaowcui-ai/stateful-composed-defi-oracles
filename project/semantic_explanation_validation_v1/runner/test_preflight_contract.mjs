import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { buildPreflightPlan, buildLocalCapabilityPlan, validatePreflightPlan, archiveExistingReport } from "./run_preflight.mjs";
import { ADAPTERS } from "./adapters.mjs";


test("preflight plan contains every chain and no designated selector", () => {
  const plan = buildPreflightPlan(ADAPTERS);
  assert.equal(plan.length, 5);
  assert.doesNotThrow(() => validatePreflightPlan(plan, ADAPTERS));
  const text = JSON.stringify(plan);
  for (const adapter of Object.values(ADAPTERS)) assert.ok(!text.includes(adapter.primarySignature));
});


test("preflight plan cannot contain semantic labels or primary calls", () => {
  const plan = buildPreflightPlan(ADAPTERS);
  assert.throws(() => validatePreflightPlan([...plan, {kind:"SEMANTIC_LABEL", label:"ACCEPTED"}], ADAPTERS), /semantic output/);
  assert.throws(() => validatePreflightPlan([...plan, {kind:"PRIMARY_CALL", signature:"fetchPrice()"}], ADAPTERS), /primary call/);
});

test("a prior failed preflight is archived before a retry", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "sev-preflight-"));
  const report = path.join(dir, "PREFLIGHT_REPORT.json");
  fs.writeFileSync(report, JSON.stringify({status:"FAIL"}));
  const archived = archiveExistingReport(dir);
  assert.ok(archived.endsWith("attempts/PREFLIGHT_ATTEMPT_001.json"));
  assert.equal(JSON.parse(fs.readFileSync(archived, "utf8")).status, "FAIL");
  assert.equal(fs.existsSync(report), false);
});

test("local fork capability is planned once for every frozen chain", () => {
  const plan = buildLocalCapabilityPlan(ADAPTERS);
  assert.equal(plan.length, 5);
  assert.deepEqual(plan.map(x => x.implementation).sort(), Object.keys(ADAPTERS).sort());
  assert.ok(plan.every(x => x.features.includes("fork_reset") && x.features.includes("trace_call")));
});

test("a transport-only fork endpoint override does not change deployment identity", () => {
  const plan = buildLocalCapabilityPlan(ADAPTERS, {MENTO:"http://127.0.0.1:18545"});
  const mento = plan.find(x => x.implementation === "MENTO");
  assert.equal(mento.endpoint, "http://127.0.0.1:18545");
  assert.equal(mento.original_endpoint, ADAPTERS.MENTO.endpoint);
  assert.equal(mento.block_number, ADAPTERS.MENTO.blockNumber);
  assert.equal(mento.root, ADAPTERS.MENTO.root);
});
