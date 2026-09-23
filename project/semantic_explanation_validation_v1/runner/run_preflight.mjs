import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";
import { ADAPTERS } from "./adapters.mjs";


const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(HERE, "..", "02_preflight");


export function archiveExistingReport(directory) {
  const report = path.join(directory, "PREFLIGHT_REPORT.json");
  if (!fs.existsSync(report)) return "";
  const attempts = path.join(directory, "attempts");
  fs.mkdirSync(attempts, {recursive:true});
  let index = 1;
  let destination;
  do {
    destination = path.join(attempts, `PREFLIGHT_ATTEMPT_${String(index++).padStart(3, "0")}.json`);
  } while (fs.existsSync(destination));
  fs.renameSync(report, destination);
  return destination.replaceAll("\\", "/");
}


export function buildPreflightPlan(adapters) {
  return Object.entries(adapters).map(([id, item]) => ({
    kind: "IDENTITY_READ",
    implementation: id,
    endpoint: item.endpoint,
    chain_id: item.chainId,
    block_number: item.blockNumber,
    expected_hash: item.blockHash,
    root: item.root,
    methods: ["eth_chainId", "eth_getBlockByNumber", "eth_getCode"],
  }));
}


export function buildLocalCapabilityPlan(adapters, endpointOverrides = {}) {
  return Object.entries(adapters).map(([implementation, item]) => ({
    implementation,
    endpoint:endpointOverrides[implementation] || item.endpoint,
    original_endpoint:item.endpoint,
    block_number:item.blockNumber,
    root:item.root,
    features:["fork_reset","snapshot_revert","time_control","trace_call"],
  }));
}


export function validatePreflightPlan(plan, adapters) {
  const primarySignatures = new Set(Object.values(adapters).map(x => x.primarySignature));
  for (const row of plan) {
    if (row.kind === "SEMANTIC_LABEL" || "label" in row) throw new Error("preflight semantic output is prohibited");
    if (row.kind === "PRIMARY_CALL" || primarySignatures.has(row.signature)) throw new Error("preflight primary call is prohibited");
  }
  return true;
}


async function rpc(endpoint, method, params) {
  const started = new Date().toISOString();
  const response = await fetch(endpoint, {method:"POST", headers:{"content-type":"application/json"}, body:JSON.stringify({jsonrpc:"2.0",id:1,method,params})});
  const json = await response.json();
  if (json.error) throw new Error(`${method}: ${json.error.message}`);
  return {started, result: json.result};
}


const hex = value => `0x${BigInt(value).toString(16)}`;
const shaCode = code => crypto.createHash("sha256").update(Buffer.from(code.slice(2), "hex")).digest("hex");


async function execute() {
  fs.mkdirSync(OUT, {recursive:true});
  const priorAttempt = archiveExistingReport(OUT);
  const plan = buildPreflightPlan(ADAPTERS);
  validatePreflightPlan(plan, ADAPTERS);
  const rows = [];
  for (const row of plan) {
    const item = {...row, attempted:true, primary_calls:0, semantic_outputs:0};
    try {
      const chain = await rpc(row.endpoint, "eth_chainId", []);
      const block = await rpc(row.endpoint, "eth_getBlockByNumber", [hex(row.block_number), false]);
      const code = await rpc(row.endpoint, "eth_getCode", [row.root, hex(row.block_number)]);
      item.observed_chain_id = Number(BigInt(chain.result));
      item.observed_hash = block.result?.hash ?? "NA";
      item.runtime_bytes = code.result === "0x" ? 0 : (code.result.length - 2) / 2;
      item.runtime_sha256 = shaCode(code.result);
      item.identity_pass = item.observed_chain_id === row.chain_id && item.observed_hash.toLowerCase() === row.expected_hash.toLowerCase() && item.runtime_bytes > 0;
      item.status = item.identity_pass ? "PASS" : "FAIL_IDENTITY";
    } catch (error) {
      item.status = "FAIL_TRANSPORT_OR_ARCHIVE";
      item.error = String(error);
    }
    rows.push(item);
  }
  const local = process.env.SEV_HARDHAT_URL;
  const capability = {attempted: Boolean(local), status: local ? "PENDING" : "NOT_RUN", rows:[]};
  if (local) {
    const endpointOverrides = process.env.SEV_CELO_FORK_URL ? {MENTO:process.env.SEV_CELO_FORK_URL} : {};
    for (const item of buildLocalCapabilityPlan(ADAPTERS, endpointOverrides)) {
      const result = {implementation:item.implementation, status:"PENDING", features:item.features};
      try {
        await rpc(local, "hardhat_reset", [{forking:{jsonRpcUrl:item.endpoint,blockNumber:item.block_number}}]);
        const snap = await rpc(local, "evm_snapshot", []);
        const latest = await rpc(local, "eth_getBlockByNumber", ["latest", false]);
        const next = Number(BigInt(latest.result.timestamp)) + 1;
        await rpc(local, "evm_setNextBlockTimestamp", [next]);
        await rpc(local, "evm_mine", []);
        await rpc(local, "debug_traceCall", [{to:item.root,data:"0x"},"latest",{}]);
        await rpc(local, "evm_revert", [snap.result]);
        result.status = "PASS";
      } catch (error) {
        result.status = "FAIL";
        result.error = String(error);
      }
      capability.rows.push(result);
    }
    capability.status = capability.rows.every(x => x.status === "PASS") ? "PASS" : "FAIL";
  }
  const report = {
    schema:"semantic-g5-preflight-v1",
    status: rows.every(x => x.status === "PASS") && capability.status === "PASS" ? "PASS" : "FAIL",
    generated_at:new Date().toISOString(),
    scientific_output_exposure:false,
    formal_conditions_executed:0,
    target_primary_calls:0,
    rows,
    local_capability:capability,
    prior_attempt_archived:priorAttempt || "NA",
  };
  fs.writeFileSync(path.join(OUT, "PREFLIGHT_REPORT.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify({status:report.status, identities:Object.fromEntries(rows.map(x=>[x.implementation,x.status])), local_capability:capability.status}, null, 2));
  if (report.status !== "PASS") process.exitCode = 1;
}


if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url) && process.argv.includes("--execute")) execute().catch(error => { console.error(error); process.exitCode = 1; });
