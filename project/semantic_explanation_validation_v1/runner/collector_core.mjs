import crypto from "node:crypto";


export function normalize(value) {
  if (value === undefined || value === null) return "NA";
  if (typeof value === "bigint") return value.toString(10);
  if (Array.isArray(value)) return value.map(normalize);
  if (typeof value === "object") return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, normalize(item)]));
  return value;
}

export function normalizeTraceReturn(value) {
  const text = value ?? "";
  return text.startsWith("0x") ? text : `0x${text}`;
}

export function impersonatedBalanceWei() {
  return 10_000n * 10n ** 18n;
}

export function strictlyFutureTimestamp(requested, current) {
  return Math.max(Number(requested), Number(current) + 1);
}


export function heldOutSchedule(seed, atoms, forbidden, length) {
  const blocked = new Set(forbidden.map(String));
  const allowed = atoms.filter(value => !blocked.has(String(value)));
  if (!allowed.length) throw new Error("no held-out atoms remain");
  const digest = crypto.createHash("sha256").update(seed).digest();
  return Array.from({length}, (_, index) => allowed[digest[index % digest.length] % allowed.length]);
}


export class AuditLedger {
  constructor() {
    this.entries = [];
    this.nextId = 1;
  }

  intent(category, detail = {}) {
    const id = this.nextId++;
    this.entries.push({id, phase: "INTENT", category, recorded_before_action: true, detail: normalize(detail)});
    return id;
  }

  result(intentId, detail = {}) {
    if (!this.entries.some(entry => entry.id === intentId && entry.phase === "INTENT")) throw new Error("result lacks prior intent");
    this.entries.push({intent_id: intentId, phase: "RESULT", detail: normalize(detail)});
  }

  counts() {
    const counts = {};
    for (const entry of this.entries.filter(item => item.phase === "INTENT")) counts[entry.category] = (counts[entry.category] || 0) + 1;
    return counts;
  }
}


export class EpisodeState {
  constructor(id) {
    this.id = id;
    this.rows = [];
    this.failure = null;
  }

  fail(reason) {
    this.failure = reason;
  }

  record(conditionId, row) {
    const output = {condition_id: conditionId, ...normalize(row)};
    if (this.failure) {
      output.comparable = false;
      output.noncomparability_reason = `ancestor episode failure: ${this.failure}`;
    }
    this.rows.push(output);
    return output;
  }
}


export function partitionObservation(full) {
  const keys = {
    R: ["return"],
    P: ["return", "post_public"],
    H: ["return", "post_public", "pre_public", "public_history"],
    X: ["return", "post_public", "pre_public", "public_history", "trace", "non_abi_storage"],
  };
  return Object.fromEntries(Object.entries(keys).map(([layer, fields]) => [
    layer,
    Object.fromEntries(fields.filter(field => field in full).map(field => [field, normalize(full[field])])),
  ]));
}
