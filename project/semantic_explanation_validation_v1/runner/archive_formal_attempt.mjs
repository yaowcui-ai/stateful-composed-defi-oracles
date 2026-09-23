import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const execution = path.resolve(here, "..", "03_execution");
const attempts = path.join(execution, "attempts");
const destination = path.join(attempts, process.argv[2] || "FORMAL_ATTEMPT_001");

if (fs.existsSync(destination)) throw new Error(`archive already exists: ${destination}`);
fs.mkdirSync(destination, {recursive: true});
for (const entry of fs.readdirSync(execution, {withFileTypes: true})) {
  if (entry.name === "attempts") continue;
  fs.renameSync(path.join(execution, entry.name), path.join(destination, entry.name));
}
console.log(destination);
