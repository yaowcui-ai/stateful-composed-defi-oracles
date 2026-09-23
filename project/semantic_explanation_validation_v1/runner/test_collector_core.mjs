import test from "node:test";
import assert from "node:assert/strict";
import {
  normalize,
  heldOutSchedule,
  AuditLedger,
  partitionObservation,
  EpisodeState,
  normalizeTraceReturn,
  impersonatedBalanceWei,
  strictlyFutureTimestamp,
} from "./collector_core.mjs";
import { buildAggregatorRuntime } from "./runtime_stubs.mjs";


test("normalization preserves exact integers and explicit absence", () => {
  assert.deepEqual(normalize({a: 2n, b: undefined, c: [null, 3n]}), {a: "2", b: "NA", c: ["NA", "3"]});
});


test("held-out schedule is deterministic and rejects development atoms", () => {
  const a = heldOutSchedule("VH1", [91n, 107n, 131n], [100n, 120n], 8);
  const b = heldOutSchedule("VH1", [91n, 107n, 131n], [100n, 120n], 8);
  assert.deepEqual(a, b);
  assert.equal(a.length, 8);
  assert.ok(a.every(x => ![100n, 120n].includes(x)));
});


test("audit ledger writes intent before result and counts categories", () => {
  const ledger = new AuditLedger();
  const id = ledger.intent("PRIMARY", {method: "eth_call"});
  ledger.result(id, {ok: true});
  assert.deepEqual(ledger.entries.map(x => x.phase), ["INTENT", "RESULT"]);
  assert.equal(ledger.entries[0].recorded_before_action, true);
  assert.deepEqual(ledger.counts(), {PRIMARY: 1});
});


test("episode failure poisons descendants without deleting attempted rows", () => {
  const episode = new EpisodeState("FH3");
  episode.record("FH3A", {comparable: true});
  episode.fail("source history invalid");
  episode.record("FH3B", {comparable: true});
  assert.equal(episode.rows.length, 2);
  assert.equal(episode.rows[1].comparable, false);
  assert.equal(episode.rows[1].noncomparability_reason, "ancestor episode failure: source history invalid");
});


test("partition creates nested R P H X views from one invocation", () => {
  const full = {
    return: ["91", true],
    post_public: {status: 1},
    pre_public: {status: 0},
    public_history: [{event: "Changed"}],
    trace: {failed: false},
    non_abi_storage: {"0x0": "1"},
  };
  const out = partitionObservation(full);
  assert.deepEqual(Object.keys(out.R), ["return"]);
  assert.deepEqual(Object.keys(out.P), ["return", "post_public"]);
  assert.deepEqual(Object.keys(out.H), ["return", "post_public", "pre_public", "public_history"]);
  assert.deepEqual(Object.keys(out.X), ["return", "post_public", "pre_public", "public_history", "trace", "non_abi_storage"]);
});

test("aggregator stub distinguishes valid stale and reverting dependency behaviours", () => {
  const fresh = buildAggregatorRuntime({decimals:8, answer:91n, timestamp:100, callOk:true});
  const stale = buildAggregatorRuntime({decimals:8, answer:91n, timestamp:1, callOk:true});
  const failed = buildAggregatorRuntime({decimals:8, answer:91n, timestamp:100, callOk:false});
  assert.match(fresh, /^0x[0-9a-f]+$/i);
  assert.notEqual(fresh, stale);
  assert.notEqual(fresh, failed);
});

test("trace return normalization accepts prefixed and unprefixed Hardhat values", () => {
  assert.equal(normalizeTraceReturn("0x1234"), "0x1234");
  assert.equal(normalizeTraceReturn("1234"), "0x1234");
  assert.equal(normalizeTraceReturn(""), "0x");
});

test("impersonated account funding covers high-gas fork transactions", () => {
  assert.ok(impersonatedBalanceWei() >= 10_000n * 10n ** 18n);
});

test("a scheduled block timestamp is strictly later than the current block", () => {
  assert.equal(strictlyFutureTimestamp(100, 100), 101);
  assert.equal(strictlyFutureTimestamp(102, 100), 102);
});
