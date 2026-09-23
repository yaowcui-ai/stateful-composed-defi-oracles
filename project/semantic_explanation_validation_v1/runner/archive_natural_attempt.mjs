import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const source=path.join(root,"05_natural_history"),attempts=path.join(source,"attempts"),destination=path.join(attempts,process.argv[2]||"RETRIEVAL_ATTEMPT_001");
if(fs.existsSync(destination))throw new Error(`archive exists: ${destination}`);fs.mkdirSync(destination,{recursive:true});
for(const entry of fs.readdirSync(source,{withFileTypes:true})){if(entry.name==="attempts")continue;fs.renameSync(path.join(source,entry.name),path.join(destination,entry.name));}
console.log(destination);
