import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import {fileURLToPath} from "node:url";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const episodes=JSON.parse(fs.readFileSync(path.join(root,"01_protocol","conditions.json"),"utf8")).episodes;
const selected=[];
for(const implementation of [...new Set(episodes.map(x=>x.implementation))]){
  const ranked=episodes.filter(x=>x.implementation===implementation).map(x=>({...x,sha256:crypto.createHash("sha256").update(x.episode_id).digest("hex")})).sort((a,b)=>a.sha256.localeCompare(b.sha256));
  selected.push(ranked[0]);
}
selected.sort((a,b)=>a.implementation.localeCompare(b.implementation));
const out={schema:"independent-reproduction-selection-v1",status:"FROZEN_BY_PREDECLARED_RULE",rule:"lowest sha256(episode_id) within each implementation; one episode per implementation gives 5/25 = 20% coverage repair",selected};
const dir=path.join(root,"06_reproduction");fs.mkdirSync(dir,{recursive:true});fs.writeFileSync(path.join(dir,"SELECTION.json"),JSON.stringify(out,null,2)+"\n");console.log(selected.map(x=>`${x.implementation}:${x.episode_id}`).join(" "));
