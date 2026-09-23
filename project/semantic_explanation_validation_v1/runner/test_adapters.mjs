import test from "node:test";
import assert from "node:assert/strict";
import { ADAPTERS, validateAdapters } from "./adapters.mjs";


test("five frozen adapters have exact identities and complete ABI returns", () => {
  const summary = validateAdapters();
  assert.deepEqual(summary.ids, ["AURIGAMI", "FATHOM", "FELIX", "MENTO", "VESTA"]);
  assert.equal(summary.count, 5);
  for (const adapter of Object.values(ADAPTERS)) {
    assert.match(adapter.root, /^0x[0-9a-f]{40}$/i);
    assert.match(adapter.blockHash, /^0x[0-9a-f]{64}$/i);
    assert.ok(adapter.returnFields.length > 0);
    assert.ok(adapter.publicFields.length > 0);
    assert.ok(adapter.primarySignature.includes("("));
  }
});


test("known and prospective roles remain distinct", () => {
  assert.equal(ADAPTERS.VESTA.role, "KNOWN");
  assert.equal(ADAPTERS.AURIGAMI.role, "KNOWN");
  assert.equal(ADAPTERS.FATHOM.role, "KNOWN_INCOMPLETE");
  assert.equal(ADAPTERS.MENTO.role, "PROSPECTIVE_NEW");
  assert.equal(ADAPTERS.FELIX.role, "PROSPECTIVE_BOUNDARY");
});


test("P H and X declarations do not hide public fields in X", () => {
  for (const adapter of Object.values(ADAPTERS)) {
    assert.ok(adapter.historyFields.every(field => !adapter.nonAbiFields.includes(field)));
    assert.ok(adapter.publicFields.every(field => !adapter.nonAbiFields.includes(field)));
  }
  assert.deepEqual(ADAPTERS.FATHOM.nonAbiFields, []);
  assert.deepEqual(ADAPTERS.FELIX.nonAbiFields, ["priceFeedDisabled_slot"]);
});
