import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Interface } from "ethers";
import { ADAPTERS } from "./adapters.mjs";
import { normalize, partitionObservation, normalizeTraceReturn, impersonatedBalanceWei, strictlyFutureTimestamp } from "./collector_core.mjs";
import { buildFormalPlan } from "./formal_plan.mjs";
import { buildAggregatorRuntime } from "./runtime_stubs.mjs";


const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..");
const EXEC = path.join(ROOT, "03_execution");
const RAW = path.join(EXEC, "raw_rpc");
const OBS = path.join(EXEC, "observations");
const TRACES = path.join(EXEC, "traces");
for (const directory of [EXEC, RAW, OBS, TRACES]) fs.mkdirSync(directory, {recursive:true});
const ENDPOINT = process.env.SEV_HARDHAT_URL || "http://127.0.0.1:8546";
const CELO_FORK = process.env.SEV_CELO_FORK_URL || "http://127.0.0.1:18545";
const BEEF = "0x000000000000000000000000000000000000bEEF";
const ZERO = "0x0000000000000000000000000000000000000000";

let rpcId = 1;
let seq = 1;
let active = {implementation:"NONE",episode_id:"NONE",condition_id:"NONE",role:"INFRASTRUCTURE"};
const auditFile = path.join(EXEC, "RPC_AUDIT_LOG.jsonl");
const ledgerFile = path.join(EXEC, "CALL_LEDGER.jsonl");
const exposureFile = path.join(EXEC, "EXPOSURE_LOG.jsonl");
for (const file of [auditFile, ledgerFile, exposureFile]) fs.writeFileSync(file, "");

const now = () => new Date().toISOString();
const hex = value => `0x${BigInt(value).toString(16)}`;
const append = (file, value) => fs.appendFileSync(file, JSON.stringify(normalize(value)) + "\n");

async function rpc(method, params, role=active.role) {
  const id = rpcId++;
  const intent = {seq:seq++,phase:"INTENT",recorded_before_action:true,timestamp:now(),rpc_id:id,...active,role,method};
  append(auditFile, intent);
  let json;
  try {
    const response = await fetch(ENDPOINT, {method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({jsonrpc:"2.0",id,method,params})});
    json = await response.json();
  } catch (error) {
    append(auditFile, {seq:seq++,phase:"RESULT",intent_seq:intent.seq,rpc_id:id,ok:false,error:String(error)});
    throw error;
  }
  const rawName = `${String(id).padStart(6,"0")}_${active.implementation}_${active.episode_id}_${active.condition_id}_${method}.json`.replaceAll(/[^A-Za-z0-9_.-]/g,"_");
  fs.writeFileSync(path.join(RAW, rawName), JSON.stringify(normalize({request:{jsonrpc:"2.0",id,method,params},response:json}), null, 2) + "\n");
  append(auditFile, {seq:seq++,phase:"RESULT",intent_seq:intent.seq,rpc_id:id,ok:!json.error,raw_file:`raw_rpc/${rawName}`,rpc_error:json.error?.message ?? "NA"});
  if (json.error) throw new Error(`${method}: ${json.error.message}`);
  return json.result;
}

function conceptual(kind, detail={}) {
  append(ledgerFile, {timestamp:now(),...active,kind,detail:normalize(detail)});
}

async function reset(id) {
  const adapter = ADAPTERS[id];
  const jsonRpcUrl = id === "MENTO" ? CELO_FORK : adapter.endpoint;
  await rpc("hardhat_reset", [{forking:{jsonRpcUrl,blockNumber:adapter.blockNumber}}], "EPISODE_RESET");
  const block = await rpc("eth_getBlockByNumber", ["latest", false], "BLOCK_IDENTITY");
  if (Number(BigInt(block.number)) !== adapter.blockNumber || block.hash.toLowerCase() !== adapter.blockHash.toLowerCase()) throw new Error(`${id}: pinned block mismatch`);
  conceptual("FORK_RESET", {chain_id:adapter.chainId,block_number:adapter.blockNumber,block_hash:block.hash,transport_override:id === "MENTO"});
  return block;
}

async function impersonate(address) {
  await rpc("hardhat_impersonateAccount", [address], "SUPPORT_MECHANICS");
  await rpc("hardhat_setBalance", [address, hex(impersonatedBalanceWei())], "SUPPORT_MECHANICS");
}

async function setCode(address, code, detail) {
  await rpc("hardhat_setCode", [address, code], "DEPENDENCY_INTERVENTION");
  conceptual("DEPENDENCY_INTERVENTION", detail);
}

async function setNext(timestamp) {
  await rpc("evm_setNextBlockTimestamp", [timestamp], "TIME_CONTROL");
}

async function mineAt(timestamp) {
  await setNext(timestamp);
  await rpc("evm_mine", [], "TIME_CONTROL");
}

async function latestBlock() {
  return rpc("eth_getBlockByNumber", ["latest", false], "BLOCK_IDENTITY");
}

async function call(iface, to, name, args=[], role="PURE_OBSERVATION") {
  const raw = await rpc("eth_call", [{to,data:iface.encodeFunctionData(name,args)},"latest"], role);
  return normalize([...iface.decodeFunctionResult(name, raw)]);
}

async function send(from, to, data, role, detail={}) {
  const hash = await rpc("eth_sendTransaction", [{from,to,data,gas:"0x1c9c380"}], role);
  const receipt = await rpc("eth_getTransactionReceipt", [hash], "RECEIPT");
  conceptual(role, {...detail,tx_hash:hash,block_number:Number(BigInt(receipt.blockNumber))});
  return {hash,receipt};
}

async function traceTransaction(hash) {
  const trace = await rpc("debug_traceTransaction", [hash,{disableMemory:true,disableStack:false,disableStorage:false}], "PRIMARY_TRACE");
  const file = path.join(TRACES, `${active.condition_id}.json`);
  fs.writeFileSync(file, JSON.stringify(normalize(trace), null, 2) + "\n");
  return {trace,file:`traces/${active.condition_id}.json`,rawReturn:normalizeTraceReturn(trace.returnValue)};
}

async function tracePure(to, data) {
  const trace = await rpc("debug_traceCall", [{to,data},"latest",{disableMemory:true,disableStack:true,disableStorage:true}], "PRIMARY_AND_TRACE");
  const file = path.join(TRACES, `${active.condition_id}.json`);
  fs.writeFileSync(file, JSON.stringify(normalize(trace), null, 2) + "\n");
  return {trace,file:`traces/${active.condition_id}.json`,rawReturn:normalizeTraceReturn(trace.returnValue)};
}

async function primaryTx(iface, to, name, args, observer, from=BEEF) {
  const pre = await observer();
  const tx = await send(from, to, iface.encodeFunctionData(name,args), "PRIMARY", {entrypoint:name,mutates:true});
  const traced = await traceTransaction(tx.hash);
  let decoded = ["SUCCESS"];
  if (traced.rawReturn !== "0x") decoded = normalize([...iface.decodeFunctionResult(name, traced.rawReturn)]);
  const post = await observer();
  const sstores = (traced.trace.structLogs || []).filter(x => x.op === "SSTORE").map(x => ({pc:x.pc,stack_tail:(x.stack || []).slice(-2)}));
  const full = {return:decoded,post_public:post,pre_public:pre,public_history:tx.receipt.logs,trace:{file:traced.file,failed:traced.trace.failed,gas:traced.trace.gas},non_abi_storage:{sstores}};
  conceptual("DESIGNATED_OBSERVATION", {entrypoint:name,one_primary_call:true});
  return {full,layers:partitionObservation(full),tx_hash:tx.hash,block_number:Number(BigInt(tx.receipt.blockNumber))};
}

async function primaryPure(iface, to, name, args, observer) {
  const pre = await observer();
  const data = iface.encodeFunctionData(name,args);
  const traced = await tracePure(to,data);
  if (traced.trace.failed) throw new Error(`${name}: primary pure call reverted`);
  const decoded = normalize([...iface.decodeFunctionResult(name,traced.rawReturn)]);
  const post = await observer();
  const full = {return:decoded,post_public:post,pre_public:pre,public_history:[],trace:{file:traced.file,failed:false,gas:traced.trace.gas},non_abi_storage:{}};
  conceptual("DESIGNATED_OBSERVATION", {entrypoint:name,one_primary_call:true,mutates:false});
  return {full,layers:partitionObservation(full),tx_hash:"NA",block_number:Number(BigInt((await latestBlock()).number))};
}

const V = {root:ADAPTERS.VESTA.root,asset:"0x8d9ba570d6cb60c7e3e0f31343efe75ab8e65fb1",price:"0x761aaeBf021F19F198D325D7979965D0c7C9e53b",index:"0x48C4721354A3B29D80EF03C65E6644A37338a0B1"};
const A = {root:ADAPTERS.AURIGAMI.root,asset:"0x4f0d864b1ABf4B701799a0b30b57A22dFEB5917b",up:["0xf2B7e347Ca4eC2a0F139B1D3073d679911295a2a","0xb3072378821cdaFAc340bF18a0Fbf15c72FEb83B","0xF2f3776B9F69A9302c897AEc26b59027e01D36Cc"],backup:"0xa1E2BcCeD2556249B74a87c673f521D19fe6B644"};
const F = {root:ADAPTERS.FATHOM.root,source:"0xb2dfd3b56a909efbea6e8a49c0d17f653aa1d7ca",token0:"0x951857744785e80e2de051c32ee7b25f9c458c42",token1:"0xd4b5f10d61916bd6e0860144a91ac658de8a1437",factory:"0x9fAb572F75008A42c6aF80b36Ab20C76a38ABc4B"};
const M = {root:ADAPTERS.MENTO.root,feed:"0x44D99a013a0DAdbB4C06F9Cc9397BFd3AC12b017",reporter:"0x1485C0E710ff9EF059834F42b312F10e7af823bd"};
const X = {root:ADAPTERS.FELIX.root,oracle:"0xa8a94Da411425634e3Ed6C331a32ab4fd774aa43"};

const vI = new Interface(["function fetchPrice(address) returns(uint256)","function status() view returns(uint8)","function lastGoodPrice(address) view returns(uint256)","function lastGoodIndex(address) view returns(uint256)"]);
const aI = new Interface(["function updateMainFeedData(address,int256,uint256)","function getUnderlyingPrice(address) view returns(uint256)","function mainFeedRaw(address,address) view returns(uint216,uint32)","function mainFeed(address) view returns(uint216,uint8,uint32)","function validPeriod() view returns(uint256)","function futureTolerance() view returns(uint256)","function _getRawUnderlyingPrice(address) view returns(uint256,uint256,bool)"]);
const fI = new Interface(["function peekPrice() returns(uint256,bool)","function readPrice() view returns(uint256)","function delayedPrice() view returns(uint256,uint256)","function latestPrice() view returns(uint256,uint256)","function lastUpdateTS() view returns(uint256)","function timeDelay() view returns(uint256)","function priceLife() view returns(uint256)","function isPriceOk() view returns(bool)","function isPriceFresh() view returns(bool)"]);
const srcI = new Interface(["function update(address,address)"]);
const factoryI = new Interface(["function getPair(address,address) view returns(address)"]);
const pairI = new Interface(["function token0() view returns(address)","function getReserves() view returns(uint112,uint112,uint32)","function swap(uint256,uint256,address,bytes)"]);
const wxdcI = new Interface(["function deposit() payable","function transfer(address,uint256) returns(bool)"]);
const mI = new Interface(["function report(address,uint256,address,address)","function medianRate(address) view returns(uint256,uint256)","function medianTimestamp(address) view returns(uint256)","function getRates(address) view returns(address[],uint256[],uint8[])","function getTimestamps(address) view returns(address[],uint256[],uint8[])","function numRates(address) view returns(uint256)","function numTimestamps(address) view returns(uint256)","function reportExpirySeconds() view returns(uint256)","function getTokenReportExpirySeconds(address) view returns(uint256)","function isOldestReportExpired(address) view returns(bool,address)"]);
const xI = new Interface(["function fetchPrice() returns(uint256,bool)","function lastGoodPrice() view returns(uint256)","function whypeUsdOracle() view returns(address,uint256,uint8)","function WHYPE_USD_STALENESS_THRESHOLD() view returns(uint256)","function WHYPE_USD_DECIMALS() view returns(uint8)"]);

async function vObs(){return {status:await call(vI,V.root,"status"),lastGoodPrice:await call(vI,V.root,"lastGoodPrice",[V.asset]),lastGoodIndex:await call(vI,V.root,"lastGoodIndex",[V.asset])};}
async function aObs(){return {raw1:await call(aI,A.root,"mainFeedRaw",[A.up[0],A.asset]),raw2:await call(aI,A.root,"mainFeedRaw",[A.up[1],A.asset]),raw3:await call(aI,A.root,"mainFeedRaw",[A.up[2],A.asset]),main:await call(aI,A.root,"mainFeed",[A.asset]),rawUnderlying:await call(aI,A.root,"_getRawUnderlyingPrice",[A.asset]),validPeriod:await call(aI,A.root,"validPeriod"),futureTolerance:await call(aI,A.root,"futureTolerance")};}
async function fObs(){return {delayedPrice:await call(fI,F.root,"delayedPrice"),latestPrice:await call(fI,F.root,"latestPrice"),lastUpdateTS:await call(fI,F.root,"lastUpdateTS"),timeDelay:await call(fI,F.root,"timeDelay"),priceLife:await call(fI,F.root,"priceLife"),isPriceOk:await call(fI,F.root,"isPriceOk"),isPriceFresh:await call(fI,F.root,"isPriceFresh"),readPrice:await call(fI,F.root,"readPrice")};}
async function mObs(){return {medianRate:await call(mI,M.root,"medianRate",[M.feed]),medianTimestamp:await call(mI,M.root,"medianTimestamp",[M.feed]),rates:await call(mI,M.root,"getRates",[M.feed]),timestamps:await call(mI,M.root,"getTimestamps",[M.feed]),numRates:await call(mI,M.root,"numRates",[M.feed]),numTimestamps:await call(mI,M.root,"numTimestamps",[M.feed]),reportExpirySeconds:await call(mI,M.root,"reportExpirySeconds"),tokenExpiry:await call(mI,M.root,"getTokenReportExpirySeconds",[M.feed]),oldestExpired:await call(mI,M.root,"isOldestReportExpired",[M.feed])};}
async function xObs(){return {lastGoodPrice:await call(xI,X.root,"lastGoodPrice"),whypeUsdOracle:await call(xI,X.root,"whypeUsdOracle"),stalenessThreshold:await call(xI,X.root,"WHYPE_USD_STALENESS_THRESHOLD"),decimals:await call(xI,X.root,"WHYPE_USD_DECIMALS")};}

async function configureV(timestamp, price, age, failed=false) {
  await setCode(V.price,buildAggregatorRuntime({decimals:18,answer:price,timestamp:timestamp-age,callOk:!failed}),{leg:"price",answer:price,age,call_ok:!failed});
  await setCode(V.index,buildAggregatorRuntime({decimals:18,answer:10n**18n,timestamp:timestamp-1,callOk:true}),{leg:"index",answer:10n**18n,age:1,call_ok:true});
}

async function executeVesta(row) {
  const block = await reset("VESTA"); await impersonate(BEEF);
  let t = Number(BigInt(block.timestamp)) + (row.factor.includes("nuisance_time_b") ? 1010 : 10);
  const value = BigInt(row.value);
  const setupValue = row.factor === "retained_H" ? value : 1310000000000000000n;
  await configureV(t,setupValue,1,false); await setNext(t); await send(BEEF,V.root,vI.encodeFunctionData("fetchPrice",[V.asset]),"TARGET_SETUP",{purpose:"legal_cache_prestate"});
  t += row.factor.includes("long_prefix") ? 3 : 1;
  if (row.factor === "age_theta_minus_1") await configureV(t,value,14399,false);
  else if (row.factor.includes("age_rejection") || row.factor === "long_prefix_untrusted") await configureV(t,value,14401,false);
  else if (row.factor.includes("call_failure")) await configureV(t,value,1,true);
  else await configureV(t,value,1,false);
  await setNext(t);
  return primaryTx(vI,V.root,"fetchPrice",[V.asset],vObs);
}

async function aUpdate(updater,value,timestamp) {
  await setNext(timestamp);
  return send(updater,A.root,aI.encodeFunctionData("updateMainFeedData",[A.asset,value,timestamp]),"TARGET_SETUP",{updater,value,timestamp});
}

async function executeAurigami(row) {
  const block = await reset("AURIGAMI"); for (const updater of A.up) await impersonate(updater);
  let t = Number(BigInt(block.timestamp)) + (row.factor.includes("nuisance_time_b") ? 1008 : 8);
  const value = BigInt(row.value);
  await setCode(A.backup,buildAggregatorRuntime({decimals:8,answer:value,timestamp:t,callOk:true}),{leg:"backup",answer:value});
  if (row.factor === "updater_2_then_1_first") await aUpdate(A.up[1],value,t);
  else {
    await aUpdate(A.up[1],value,t); t += 1; await aUpdate(A.up[0],value,t);
    if (row.factor === "three_reporter_prefix" || row.factor === "main_expired_after_long_prefix") {t += 1; await aUpdate(A.up[2],value,t);}
    if (row.factor === "raw_only") {t += 1; await aUpdate(A.up[0],value,t);}
    if (row.factor === "aggregate_refresh") {t += 1; await aUpdate(A.up[0],value,t); t += 1; await aUpdate(A.up[1],value,t);}
  }
  const main = await call(aI,A.root,"mainFeed",[A.asset]);
  if (row.factor === "age_theta" || row.factor.includes("backup_nuisance_time")) await mineAt(Number(main[2])+7200);
  if (row.factor === "age_theta_plus_1" || row.factor === "main_expired_after_long_prefix") await mineAt(Number(main[2])+7201);
  return primaryPure(aI,A.root,"getUnderlyingPrice",[A.asset],aObs);
}

function epochSchedule(base){return {updates:Array.from({length:15},(_,i)=>base+1+120*i),endpoint:base+1800};}
async function sourceEpoch(base){const schedule=epochSchedule(base);for(const timestamp of schedule.updates){await setNext(timestamp);await send(BEEF,F.source,srcI.encodeFunctionData("update",[F.token0,F.token1]),"DEPENDENCY_INTERVENTION",{timestamp});}return schedule.endpoint;}
async function setupPeek(timestamp){await setNext(timestamp);return send(BEEF,F.root,fI.encodeFunctionData("peekPrice",[]),"TARGET_SETUP",{timestamp});}
async function normalSwap(timestamp){const pair=(await call(factoryI,F.factory,"getPair",[F.token0,F.token1],"DEPENDENCY_READ"))[0];const token0=(await call(pairI,pair,"token0",[],"DEPENDENCY_READ"))[0];if(token0.toLowerCase()!==F.token0.toLowerCase())throw new Error("Fathom token0 mismatch");const reserves=await call(pairI,pair,"getReserves",[],"DEPENDENCY_READ");const amountIn=BigInt(reserves[0])/107n,ai=amountIn*997n,amountOut=ai*BigInt(reserves[1])/(BigInt(reserves[0])*1000n+ai);await setNext(timestamp);await rpc("eth_sendTransaction",[{from:BEEF,to:F.token0,data:wxdcI.encodeFunctionData("deposit",[]),value:hex(amountIn),gas:"0x1c9c380"}],"SUPPORT_MECHANICS");await send(BEEF,F.token0,wxdcI.encodeFunctionData("transfer",[pair,amountIn]),"SUPPORT_MECHANICS",{amountIn});await send(BEEF,pair,pairI.encodeFunctionData("swap",[0,amountOut,BEEF,"0x"]),"DEPENDENCY_INTERVENTION",{amountIn,amountOut});}

async function executeFathom(row) {
  const block = await reset("FATHOM"); await impersonate(BEEF);
  let base = Math.ceil((Number(BigInt(block.timestamp))+120)/120)*120;
  let endpoint = await sourceEpoch(base); await setupPeek(endpoint); base=endpoint; endpoint=await sourceEpoch(base); await setupPeek(endpoint);
  if (row.factor === "delay_899" || row.factor === "delay_900") {const lu=Number((await call(fI,F.root,"lastUpdateTS"))[0]);await setNext(lu+(row.factor.endsWith("899")?899:900));return primaryTx(fI,F.root,"peekPrice",[],fObs);}
  if (row.factor === "retained_age_3600" || row.factor === "retained_age_3601") {const delayed=await call(fI,F.root,"delayedPrice");await mineAt(Number(delayed[1])+(row.factor.endsWith("3600")?3600:3601));return primaryPure(fI,F.root,"readPrice",[],fObs);}
  if (row.factor === "latest_changed_delayed_retained" || row.factor === "delayed_promoted") {await normalSwap(endpoint+1);base=Math.ceil((endpoint+120)/120)*120;endpoint=await sourceEpoch(base);if(row.factor === "delayed_promoted"){await setNext(endpoint);await send(BEEF,F.root,fI.encodeFunctionData("peekPrice",[]),"TARGET_SETUP",{purpose:"first changed promotion"});base=endpoint;endpoint=await sourceEpoch(base);}await setNext(endpoint);return primaryTx(fI,F.root,"peekPrice",[],fObs);}
  if (row.factor === "source_success_shared_prestate") {const current=Number(BigInt((await latestBlock()).timestamp));await setNext(strictlyFutureTimestamp(endpoint,current));return primaryTx(fI,F.root,"peekPrice",[],fObs);}
  if (row.factor === "source_error_shared_prestate") {endpoint += 1801;await setNext(endpoint);return primaryTx(fI,F.root,"peekPrice",[],fObs);}
  if (row.factor.startsWith("equal_value_promotion")) {base=endpoint;endpoint=await sourceEpoch(base);if(row.factor.endsWith("4")){await setNext(endpoint);await send(BEEF,F.root,fI.encodeFunctionData("peekPrice",[]),"TARGET_SETUP",{purpose:"third promotion"});base=endpoint;endpoint=await sourceEpoch(base);}await setNext(endpoint);return primaryTx(fI,F.root,"peekPrice",[],fObs);}
  await setNext(endpoint); return primaryTx(fI,F.root,"peekPrice",[],fObs);
}

async function executeMento(row) {
  const block = await reset("MENTO"); await impersonate(M.reporter);
  let t = Number(BigInt(block.timestamp)) + (row.factor.includes("nuisance_time_b") ? 1007 : 7);
  const value = BigInt(row.value);
  await setNext(t); await send(M.reporter,M.root,mI.encodeFunctionData("report",[M.feed,value,ZERO,ZERO]),"TARGET_SETUP",{purpose:"legal_shared_report_prestate",value});
  let age = 10;
  if (row.factor.includes("361") || row.factor.includes("expired")) age=361;
  if (row.factor.includes("359")) age=359;
  if (row.factor.includes("long_history")) {for(let i=0;i<3;i++){t+=61;await setNext(t);await send(M.reporter,M.root,mI.encodeFunctionData("report",[M.feed,value+BigInt(i+1),ZERO,ZERO]),"TARGET_SETUP",{history_index:i});}}
  t += age; await setNext(t);
  return primaryTx(mI,M.root,"report",[M.feed,value,ZERO,ZERO],mObs,M.reporter);
}

async function executeFelix(row) {
  const block = await reset("FELIX"); await impersonate(BEEF);
  let t = Number(BigInt(block.timestamp)) + (row.factor.includes("nuisance_time_b") ? 1005 : 5);
  const value = BigInt(row.value);
  await setCode(X.oracle,buildAggregatorRuntime({decimals:8,answer:value,timestamp:t-1,callOk:true}),{oracle_answer:value,age:1,call_ok:true});
  await setNext(t); await send(BEEF,X.root,xI.encodeFunctionData("fetchPrice",[]),"TARGET_SETUP",{purpose:"healthy_cache_prestate"});
  t += 1;
  const stale = row.factor.includes("stale_disable");
  const failed = row.factor.includes("revert_disable");
  const terminal = row.factor.includes("terminal_cached");
  if (!terminal) await setCode(X.oracle,buildAggregatorRuntime({decimals:8,answer:value,timestamp:stale?t-86400:t-1,callOk:!failed}),{oracle_answer:value,age:stale?86400:1,call_ok:!failed});
  if (row.factor === "cached_noncollision") await setCode(X.oracle,buildAggregatorRuntime({decimals:8,answer:value,timestamp:t-86400,callOk:true}),{oracle_answer:value,age:86400,call_ok:true});
  if (terminal) {await setCode(X.oracle,buildAggregatorRuntime({decimals:8,answer:value,timestamp:t-86400,callOk:true}),{oracle_answer:value,age:86400,call_ok:true});await setNext(t);await send(BEEF,X.root,xI.encodeFunctionData("fetchPrice",[]),"TARGET_SETUP",{purpose:"terminal_disable_prestate"});t+=1;}
  await setNext(t);
  return primaryTx(xI,X.root,"fetchPrice",[],xObs);
}

async function executeRow(row) {
  active = {implementation:row.implementation,episode_id:row.episode_id,condition_id:row.condition_id,role:"FORMAL"};
  const started = now();
  let result;
  if (row.implementation === "VESTA") result = await executeVesta(row);
  else if (row.implementation === "AURIGAMI") result = await executeAurigami(row);
  else if (row.implementation === "FATHOM") result = await executeFathom(row);
  else if (row.implementation === "MENTO") result = await executeMento(row);
  else if (row.implementation === "FELIX") result = await executeFelix(row);
  else throw new Error(`unknown implementation ${row.implementation}`);
  return {schema:"semantic-heldout-observation-v1",...row,attempted:true,valid_execution:true,comparable:true,started_at:started,completed_at:now(),...result};
}

async function main() {
  const lock = JSON.parse(fs.readFileSync(path.join(ROOT,"01_protocol","conditions.json"),"utf8"));
  const plan = buildFormalPlan(lock);
  append(exposureFile,{timestamp:now(),event:"FORMAL_EXECUTION_STARTED",condition_count:plan.length});
  const rows=[]; const failedEpisodes=new Map();
  for (const row of plan) {
    let output;
    try {
      output = await executeRow(row);
      if (failedEpisodes.has(row.episode_id)) {output.comparable=false;output.noncomparability_reason=`paired episode contains retained failure: ${failedEpisodes.get(row.episode_id)}`;}
    } catch (error) {
      failedEpisodes.set(row.episode_id,String(error));
      output={schema:"semantic-heldout-observation-v1",...row,attempted:true,valid_execution:false,comparable:false,error:String(error),completed_at:now()};
    }
    rows.push(output);
    fs.writeFileSync(path.join(OBS,`${row.condition_id}.json`),JSON.stringify(normalize(output),null,2)+"\n");
    append(exposureFile,{timestamp:now(),event:"FORMAL_CONDITION_CAPTURED",condition_id:row.condition_id,valid_execution:output.valid_execution,comparable:output.comparable});
    console.log(`${row.condition_id} ${output.valid_execution?"VALID":"FAILED"} ${output.comparable?"COMPARABLE":"NONCOMPARABLE"}`);
  }
  const summary={schema:"semantic-g6-execution-summary-v1",status:"COMPLETE_WITH_RETAINED_FAILURES",completed_at:now(),conditions_planned:plan.length,conditions_attempted:rows.length,valid_executions:rows.filter(x=>x.valid_execution).length,comparable_executions:rows.filter(x=>x.comparable).length,failed_conditions:rows.filter(x=>!x.valid_execution).map(x=>x.condition_id),failed_episodes:[...failedEpisodes.keys()],automatic_retry:false};
  fs.writeFileSync(path.join(EXEC,"EXECUTION_SUMMARY.json"),JSON.stringify(summary,null,2)+"\n");
  console.log(JSON.stringify(summary,null,2));
}

main().catch(error=>{fs.writeFileSync(path.join(EXEC,"EXECUTION_CRASH.json"),JSON.stringify({timestamp:now(),active,error:String(error),stack:error.stack,automatic_retry:false},null,2)+"\n");console.error(error);process.exitCode=1;});
