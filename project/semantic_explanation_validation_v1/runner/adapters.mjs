export const ADAPTERS = Object.freeze({
  VESTA: Object.freeze({
    role: "KNOWN", chainId: 42161, endpoint: "https://arbitrum-one.public.blastapi.io", blockNumber: 504401544,
    blockHash: "0xe4de5b0aa87785925a320862794cfd89f5569cc94308933a247e8be4f6f6eac7", root: "0xC93408bFBEa0Bf3E53bEdBce7D5C1e64db826702",
    primarySignature: "fetchPrice(address)", returnFields: ["price"], publicFields: ["status", "lastGoodPrice"], historyFields: ["status_pre", "lastGoodPrice_pre", "LastGoodPriceUpdated", "PriceFeedStatusChanged"], nonAbiFields: [],
  }),
  AURIGAMI: Object.freeze({
    role: "KNOWN", chainId: 1313161554, endpoint: "https://mainnet.aurora.dev", blockNumber: 215607038,
    blockHash: "0xf8d3df95f8f6e0bf55decf6437fb24dddd743834f6e0777efc51cb546b3f83a1", root: "0xC6e5185438e1730959c1eF3551059A3feC744E90",
    primarySignature: "getUnderlyingPrice(address)", returnFields: ["price"], publicFields: ["mainFeedRaw", "mainFeed", "isFromMainFeed", "validPeriod", "futureTolerance"], historyFields: ["raw_pre", "aggregate_pre", "MainFeedSync", "MainFeedFail"], nonAbiFields: [],
  }),
  FATHOM: Object.freeze({
    role: "KNOWN_INCOMPLETE", chainId: 50, endpoint: "https://earpc.xinfin.network", blockNumber: 107219710,
    blockHash: "0x19017f946190a457b62cd2d86ba53c111f75f2d23ce55a3f86978a40fde536ed", root: "0x5dE248bbD0ae9E846B8dBa12960fc3524Fb37a88",
    primarySignature: "peekPrice()", returnFields: ["price", "success"], publicFields: ["delayedPrice", "latestPrice", "lastUpdateTS", "isPriceFresh", "isPriceOk", "timeDelay", "priceLife"], historyFields: ["delayed_pre", "latest_pre", "lastUpdateTS_pre"], nonAbiFields: [],
  }),
  MENTO: Object.freeze({
    role: "PROSPECTIVE_NEW", chainId: 42220, endpoint: "https://forno.celo.org", blockNumber: 77467895,
    blockHash: "0x44cfb1c3c2dc5fc64839ffaaba577a013d923325791579e28866a024a832e187", root: "0xefb84935239dacdecf7c5ba76d8de40b077b7b33",
    primarySignature: "report(address,uint256,address,address)", returnFields: ["success_or_revert"], publicFields: ["medianRate", "medianTimestamp", "getRates", "getTimestamps", "numRates", "numTimestamps", "reportExpirySeconds", "getTokenReportExpirySeconds", "isOldestReportExpired"], historyFields: ["rates_pre", "timestamps_pre", "OracleReported"], nonAbiFields: [],
  }),
  FELIX: Object.freeze({
    role: "PROSPECTIVE_BOUNDARY", chainId: 999, endpoint: "https://rpc.hyperliquid.xyz/evm", blockNumber: 45864222,
    blockHash: "0x7dca15d1636dca73ca6c00608afac949ffa0c4fc6f7b31fd6c3015e885abdd82", root: "0x12a1868b89789900e413a6241ca9032dd1873a51",
    primarySignature: "fetchPrice()", returnFields: ["price", "newFailureDetected"], publicFields: ["lastGoodPrice", "whypeUsdOracle", "WHYPE_USD_STALENESS_THRESHOLD", "WHYPE_USD_DECIMALS"], historyFields: ["lastGoodPrice_pre", "PriceFeedDisabled", "oracle_round_pre"], nonAbiFields: ["priceFeedDisabled_slot"],
  }),
});


export function validateAdapters() {
  const ids = Object.keys(ADAPTERS).sort();
  for (const [id, item] of Object.entries(ADAPTERS)) {
    if (!Number.isInteger(item.chainId) || !Number.isInteger(item.blockNumber)) throw new Error(`${id}: invalid chain/block`);
    if (!/^0x[0-9a-f]{40}$/i.test(item.root)) throw new Error(`${id}: invalid root`);
    if (!/^0x[0-9a-f]{64}$/i.test(item.blockHash)) throw new Error(`${id}: invalid block hash`);
    if (!item.returnFields.length || !item.publicFields.length) throw new Error(`${id}: incomplete observation declaration`);
  }
  return {count: ids.length, ids};
}
