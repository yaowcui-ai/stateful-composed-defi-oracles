import test from "node:test";
import assert from "node:assert/strict";
import { sanitizeCeloResponse } from "./celo_rpc_sanitizer.mjs";


test("Celo full block responses retain identity and state but omit incompatible transactions", () => {
  const input = {jsonrpc:"2.0", id:3, result:{hash:"0xabc", stateRoot:"0xdef", number:"0x1", transactions:[{type:"0x7b",feeCurrency:"0x1",hash:"0x2"},{type:"0x7e",sourceHash:"0x3",hash:"0x4"}]}};
  const out = sanitizeCeloResponse("eth_getBlockByNumber", ["0x1", true], input);
  assert.equal(out.result.hash, "0xabc");
  assert.equal(out.result.stateRoot, "0xdef");
  assert.deepEqual(out.result.transactions, []);
  assert.deepEqual(input.result.transactions.map(x => x.type), ["0x7b", "0x7e"]);
});


test("non-full blocks and state responses pass through unchanged", () => {
  const block = {jsonrpc:"2.0",id:1,result:{transactions:["0x1"]}};
  assert.deepEqual(sanitizeCeloResponse("eth_getBlockByNumber", ["latest", false], block), block);
  const code = {jsonrpc:"2.0",id:2,result:"0x6000"};
  assert.deepEqual(sanitizeCeloResponse("eth_getCode", ["0x0","latest"], code), code);
});
