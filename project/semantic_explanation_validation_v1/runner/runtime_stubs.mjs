import solc from "solc";


const cache = new Map();


export function buildAggregatorRuntime({decimals, answer, timestamp, callOk=true, currentRoundId=101n}) {
  const key = JSON.stringify({decimals,answer:String(answer),timestamp,callOk,currentRoundId:String(currentRoundId)});
  if (cache.has(key)) return cache.get(key);
  const source = `// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.30;
contract HeldOutAggregator {
  function decimals() external pure returns (uint8) { return ${Number(decimals)}; }
  function latestRoundData() external pure returns (uint80,int256,uint256,uint256,uint80) {
    ${callOk ? "" : "revert();"}
    return (${currentRoundId}, ${answer}, ${timestamp}, ${timestamp}, ${currentRoundId});
  }
  function getRoundData(uint80 round) external pure returns (uint80,int256,uint256,uint256,uint80) {
    ${callOk ? "" : "revert();"}
    return (round, ${answer}, ${timestamp}, ${timestamp}, round);
  }
}`;
  const input = {language:"Solidity",sources:{"HeldOutAggregator.sol":{content:source}},settings:{optimizer:{enabled:true,runs:200},outputSelection:{"*":{"*":["evm.deployedBytecode.object"]}}}};
  const output = JSON.parse(solc.compile(JSON.stringify(input)));
  const errors = (output.errors || []).filter(item => item.severity === "error");
  if (errors.length) throw new Error(errors.map(item => item.formattedMessage).join("\n"));
  const runtime = `0x${output.contracts["HeldOutAggregator.sol"].HeldOutAggregator.evm.deployedBytecode.object}`;
  cache.set(key, runtime);
  return runtime;
}
