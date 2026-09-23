import test from "node:test";
import assert from "node:assert/strict";
import {adjacentWindows, deterministicSample} from "./natural_history_core.mjs";

test("natural windows are adjacent fixed seven-day intervals before the anchor",()=>{
  const [a,b]=adjacentWindows(1_500_000,7);
  assert.equal(a.endTimestamp+1,b.startTimestamp);
  assert.equal(b.endTimestamp+1,1_500_000);
  assert.equal(a.endTimestamp-a.startTimestamp+1,604800);
});

test("deterministic sampling preserves size and endpoints without randomness",()=>{
  const sample=deterministicSample(Array.from({length:1000},(_,i)=>i),100);
  assert.equal(sample.length,100); assert.equal(sample[0],0); assert.deepEqual(sample,deterministicSample(Array.from({length:1000},(_,i)=>i),100));
});
