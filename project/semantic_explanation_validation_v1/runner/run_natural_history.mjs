import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {deterministicSample} from "./natural_history_core.mjs";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const lock=JSON.parse(fs.readFileSync(path.join(root,"01_protocol","natural_history_windows.json"),"utf8"));
const output=path.join(root,"05_natural_history"); fs.mkdirSync(output,{recursive:true});
let rpcId=1;
async function rpc(url,method,params){
  let last;
  for(let attempt=1;attempt<=3;attempt++){
    try{
      const response=await fetch(url,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({jsonrpc:"2.0",id:rpcId++,method,params})});
      const text=await response.text(); const json=JSON.parse(text); if(json.error)throw new Error(json.error.message); return json.result;
    }catch(error){last=error;if(attempt<3)await new Promise(resolve=>setTimeout(resolve,750));}
  }
  throw last;
}
function controlledTopics(id){
  const dir=path.join(root,"03_execution","observations"); const topics=new Set();
  for(const file of fs.readdirSync(dir).filter(x=>x.endsWith(".json"))){const row=JSON.parse(fs.readFileSync(path.join(dir,file),"utf8"));if(row.implementation!==id)continue;for(const log of row.full.public_history||[])if(log.topics?.[0])topics.add(log.topics[0].toLowerCase());}
  return [...topics].sort();
}
async function mapLimit(items,limit,fn){
  const results=new Array(items.length);let cursor=0;
  async function worker(){while(true){const index=cursor++;if(index>=items.length)return;results[index]=await fn(items[index]);}}
  await Promise.all(Array.from({length:Math.min(limit,items.length)},worker));return results;
}
const results=[]; const only=process.env.SEV_NATURAL_IMPL;
for(const [id,deployment] of Object.entries(lock.deployments)){
  if(only && id!==only)continue;
  const retrievalEndpoint=id === "VESTA" ? "https://arb1.arbitrum.io/rpc" : (id === "FELIX" ? "https://rpc.hypurrscan.io" : deployment.endpoint);
  const identity=await rpc(retrievalEndpoint,"eth_getBlockByNumber",[`0x${deployment.anchorBlock.toString(16)}`,false]);
  if(identity.hash.toLowerCase()!==deployment.anchorHash.toLowerCase())throw new Error(`${id}: retrieval endpoint anchor mismatch`);
  const known=controlledTopics(id);
  for(const window of deployment.windows){
    const logs=[]; const errors=[]; const chunk=id === "MENTO" ? 5000 : (id === "FATHOM" || id === "FELIX" ? 1000 : 50000);
    const ranges=[];for(let from=window.fromBlock;from<=window.toBlock;from+=chunk)ranges.push({from,to:Math.min(from+chunk-1,window.toBlock)});
    const concurrency=id === "FELIX" ? 2 : 8;
    const batches=await mapLimit(ranges,concurrency,async({from,to})=>{try{return {logs:await rpc(retrievalEndpoint,"eth_getLogs",[{address:deployment.root,fromBlock:`0x${from.toString(16)}`,toBlock:`0x${to.toString(16)}`}])};}catch(error){return {error:{fromBlock:from,toBlock:to,error:String(error)}};}});
    for(const batch of batches){if(batch.error)errors.push(batch.error);else logs.push(...batch.logs);}
    const topicCounts={};for(const log of logs){const topic=(log.topics?.[0]||"NO_TOPIC").toLowerCase();topicCounts[topic]=(topicCounts[topic]||0)+1;}
    const matched=logs.filter(log=>known.includes((log.topics?.[0]||"").toLowerCase()));
    const row={schema:"natural-history-window-result-v1",implementation:id,window_id:window.id,...window,root:deployment.root,retrieval_endpoint:retrievalEndpoint,transport_override:retrievalEndpoint!==deployment.endpoint,log_count:logs.length,controlled_event_topic_count:matched.length,controlled_event_topics:known,topic_counts:topicCounts,retrieval_errors:errors,complete:errors.length===0,semantic_scope:logs.length?"actual root-emitted public history; pure reads and internal calls without root logs remain unobserved":"no root-emitted logs observed; no inference of absent calls or absent failures"};
    fs.writeFileSync(path.join(output,`${id}_${window.id}_SAMPLE.json`),JSON.stringify({metadata:row,deterministic_sample:deterministicSample(logs,200)},null,2)+"\n");results.push(row);
    console.log(`${id} ${window.id} logs=${logs.length} matched=${matched.length} errors=${errors.length}`);
  }
}
const allResults=[];for(const file of fs.readdirSync(output).filter(x=>/^[A-Z]+_W[12]_SAMPLE\.json$/.test(x))){allResults.push(JSON.parse(fs.readFileSync(path.join(output,file),"utf8")).metadata);}allResults.sort((a,b)=>`${a.implementation}${a.window_id}`.localeCompare(`${b.implementation}${b.window_id}`));
const summary={schema:"natural-history-summary-v1",status:allResults.length===10&&allResults.every(x=>x.complete)?"COMPLETE":"COMPLETE_WITH_RETAINED_MISSINGNESS",window_count:allResults.length,complete_windows:allResults.filter(x=>x.complete).length,total_root_logs:allResults.reduce((n,x)=>n+x.log_count,0),controlled_topic_matches:allResults.reduce((n,x)=>n+x.controlled_event_topic_count,0),results:allResults,limitations:["Address-filtered logs do not reveal pure eth_call invocations.","Transactions with internal target calls but no root-emitted log are not enumerated.","Counterfactual reads were not counted as production calls.","Empty windows were not moved or replaced."]};
fs.writeFileSync(path.join(output,"NATURAL_HISTORY_SUMMARY.json"),JSON.stringify(summary,null,2)+"\n");console.log(JSON.stringify({status:summary.status,window_count:summary.window_count,total_root_logs:summary.total_root_logs,controlled_topic_matches:summary.controlled_topic_matches},null,2));
