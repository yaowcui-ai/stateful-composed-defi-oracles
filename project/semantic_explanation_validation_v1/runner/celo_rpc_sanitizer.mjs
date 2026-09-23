import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";


export function sanitizeCeloResponse(method, params, response) {
  const out = structuredClone(response);
  if (method === "eth_getBlockByNumber" && params?.[1] === true && out?.result && Array.isArray(out.result.transactions)) {
    out.result.transactions = [];
  }
  return out;
}


function sanitizeBatch(request, response) {
  if (Array.isArray(request)) {
    const byId = new Map(request.map(item => [item.id, item]));
    return response.map(item => {
      const source = byId.get(item.id);
      return source ? sanitizeCeloResponse(source.method, source.params, item) : item;
    });
  }
  return sanitizeCeloResponse(request.method, request.params, response);
}


export function startSanitizer({port=18545, upstream="https://forno.celo.org"} = {}) {
  const server = http.createServer(async (request, response) => {
    const chunks = [];
    for await (const chunk of request) chunks.push(chunk);
    try {
      const body = JSON.parse(Buffer.concat(chunks).toString("utf8"));
      const upstreamResponse = await fetch(upstream, {method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(body)});
      const json = await upstreamResponse.json();
      const output = sanitizeBatch(body, json);
      response.writeHead(upstreamResponse.status, {"content-type":"application/json"});
      response.end(JSON.stringify(output));
    } catch (error) {
      response.writeHead(502, {"content-type":"application/json"});
      response.end(JSON.stringify({jsonrpc:"2.0",id:null,error:{code:-32098,message:String(error)}}));
    }
  });
  server.listen(port, "127.0.0.1");
  return server;
}


if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.CELO_SANITIZER_PORT || 18545);
  startSanitizer({port});
  console.log(`Celo fork compatibility proxy listening on 127.0.0.1:${port}`);
}
