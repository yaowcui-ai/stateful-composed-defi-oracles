import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import {fileURLToPath} from "node:url";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const endpoint=process.env.SEV_REPLAY_URL||"http://127.0.0.1:8547";
const selection=JSON.parse(fs.readFileSync(path.join(root,"06_reproduction","SELECTION.json"),"utf8"));
const source=path.join(root,"03_execution","raw_rpc");
const digest=value=>crypto.createHash("sha256").update(JSON.stringify(value)).digest("hex");
function semanticProjection(method,payload){
  if(payload?.error)return {error:{code:payload.error.code,message:payload.error.message}};
  const value=payload?.result;
  if(method==="eth_getTransactionReceipt"&&value)return {status:value.status,transactionHash:value.transactionHash,blockNumber:value.blockNumber,gasUsed:value.gasUsed,contractAddress:value.contractAddress??"NA",logs:(value.logs||[]).map(x=>({address:x.address,topics:x.topics,data:x.data,logIndex:x.logIndex}))};
  if(method==="debug_traceTransaction"&&value)return {failed:value.failed,gas:value.gas,returnValue:value.returnValue,sstores:(value.structLogs||[]).filter(x=>x.op==="SSTORE").map(x=>({pc:x.pc,stack:(x.stack||[]).slice(-2)}))};
  return value;
}
let id=1;
async function rpc(method,params){const response=await fetch(endpoint,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({jsonrpc:"2.0",id:id++,method,params})});const json=await response.json();return json;}
const report=[];
for(const item of selection.selected){
  const files=fs.readdirSync(source).filter(name=>name.includes(`_${item.episode_id}_`)).sort();
  const rows=[];let exact=0,semantic=0;
  for(const name of files){
    const original=JSON.parse(fs.readFileSync(path.join(source,name),"utf8"));
    const replay=await rpc(original.request.method,original.request.params);
    const expected={result:original.response.result??null,error:original.response.error??null};
    const observed={result:replay.result??null,error:replay.error??null};
    const match=JSON.stringify(expected)===JSON.stringify(observed);if(match)exact++;
    const expectedSemantic=semanticProjection(original.request.method,original.response),observedSemantic=semanticProjection(original.request.method,replay);const semanticMatch=JSON.stringify(expectedSemantic)===JSON.stringify(observedSemantic);if(semanticMatch)semantic++;
    rows.push({file:name,method:original.request.method,match,semantic_match:semanticMatch,expected_sha256:digest(expected),observed_sha256:digest(observed),expected_semantic_sha256:digest(expectedSemantic),observed_semantic_sha256:digest(observedSemantic),semantic_difference:semanticMatch?"NA":{expected:expectedSemantic,observed:observedSemantic},observed_error:replay.error?.message??"NA"});
  }
  const episode={implementation:item.implementation,episode_id:item.episode_id,rpc_count:rows.length,exact_response_matches:exact,semantic_projection_matches:semantic,mismatch_count:rows.length-exact,semantic_mismatch_count:rows.length-semantic,rows};report.push(episode);console.log(`${item.episode_id} ${exact}/${rows.length} exact ${semantic}/${rows.length} semantic`);
}
const summary={schema:"independent-transcript-replay-v1",status:report.every(x=>x.semantic_mismatch_count===0)?"SEMANTIC_EXACT_REPLAY":"REPLAY_WITH_SEMANTIC_DIFFERENCES",environment:"fresh Hardhat process on separate port; independent transcript driver does not import main runner, reference, interpreter, or scoring code",coverage:{episodes:report.length,total_registered_episodes:25,fraction:report.length/25,scientific_sample_increment:0},report,limitations:["The replay driver is independently implemented, but this run was not performed by an independent human reviewer.","Exact RPC response equality validates replay and decoding inputs; it does not by itself establish novelty or ecological prevalence.","Receipt block hashes are excluded from the stable semantic projection because the separate local fork process generates different local block identities."]};
fs.writeFileSync(path.join(root,"06_reproduction","REPLAY_REPORT.json"),JSON.stringify(summary,null,2)+"\n");console.log(JSON.stringify({status:summary.status,episodes:report.length,rpc_count:report.reduce((n,x)=>n+x.rpc_count,0),exact_mismatches:report.reduce((n,x)=>n+x.mismatch_count,0),semantic_mismatches:report.reduce((n,x)=>n+x.semantic_mismatch_count,0)},null,2));
