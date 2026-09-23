import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {ADAPTERS} from "./adapters.mjs";
import {adjacentWindows} from "./natural_history_core.mjs";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
let rpcId=1;
async function rpc(url,method,params){
  let last;
  for(let attempt=1;attempt<=4;attempt++){
    try{
      const response=await fetch(url,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({jsonrpc:"2.0",id:rpcId++,method,params})});
      const body=await response.text(); const json=JSON.parse(body);
      if(json.error) throw new Error(json.error.message);
      return json.result;
    }catch(error){last=error;console.error(`transport retry ${attempt}/4 ${url} ${method}: ${String(error)}`);if(attempt<4)await new Promise(resolve=>setTimeout(resolve,1000));}
  }
  throw new Error(`${url} ${method}: ${String(last)}`);
}
async function blockAtOrAfter(url,target,high){
  let lo=0,hi=high;
  while(lo<hi){const mid=Math.floor((lo+hi)/2);const b=await rpc(url,"eth_getBlockByNumber",[`0x${mid.toString(16)}`,false]);const ts=Number(BigInt(b.timestamp));if(ts<target)lo=mid+1;else hi=mid;}
  return lo;
}
const deployments={};
for(const [id,a] of Object.entries(ADAPTERS)){
  const endpoint=id === "FATHOM" ? "https://xdc.public-rpc.com" : a.endpoint;
  const anchor=await rpc(endpoint,"eth_getBlockByNumber",[`0x${a.blockNumber.toString(16)}`,false]);
  if(anchor.hash.toLowerCase()!==a.blockHash.toLowerCase())throw new Error(`${id}: anchor hash mismatch`);
  const anchorTimestamp=Number(BigInt(anchor.timestamp)); const windows=[];
  for(const w of adjacentWindows(anchorTimestamp,7)){
    windows.push({...w,fromBlock:await blockAtOrAfter(endpoint,w.startTimestamp,a.blockNumber),toBlock:(await blockAtOrAfter(endpoint,w.endTimestamp+1,a.blockNumber))-1});
  }
  deployments[id]={endpoint,root:a.root,anchorBlock:a.blockNumber,anchorHash:a.blockHash,anchorTimestamp,windows};
  console.log(`${id} ${windows.map(w=>`${w.id}:${w.fromBlock}-${w.toBlock}`).join(" ")}`);
}
const lock={schema:"natural-history-window-lock-v1",status:"FROZEN_BEFORE_SEMANTIC_HISTORY_RETRIEVAL",created_at:new Date().toISOString(),rule:"two adjacent seven-day windows immediately preceding each pinned block; address-only root log inclusion; no window movement; deterministic even sampling capped at 200 records per window only after full count",deployments};
fs.writeFileSync(path.join(root,"01_protocol","natural_history_windows.json"),JSON.stringify(lock,null,2)+"\n");
