// SPDX-License-Identifier: MIT


pragma solidity 0.8.24;

import {AggregatorV3Interface} from "../Dependencies/AggregatorV3Interface.sol";
import {RedStonePriceFeedBase} from "./RedStonePriceFeedBase.sol";

contract WHYPERedStonePriceFeed is RedStonePriceFeedBase {

    error WHYPERedStonePriceFeed__InvalidBorrowOperationsAddress();
    error WHYPERedStonePriceFeed__InvalidWHYPEOracleAddress();
    error WHYPERedStonePriceFeed__InvalidWHYPEOracleDecimals();
    error WHYPERedStonePriceFeed__WHYPEOracleDown();

    uint256 public constant WHYPE_USD_STALENESS_THRESHOLD = 86400; // 1 day
    uint8 public constant WHYPE_USD_DECIMALS = 8;
    
    Oracle public whypeUsdOracle;

    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor(){
        _disableInitializers();
    }

    function initialize(address _borrowOperationsAddress, address _whypeUsdOracleAddress) external initializer {

        if(_borrowOperationsAddress == address(0)) revert WHYPERedStonePriceFeed__InvalidBorrowOperationsAddress();
        if(_whypeUsdOracleAddress == address(0)) revert WHYPERedStonePriceFeed__InvalidWHYPEOracleAddress();

        __RedStonePriceFeedBase_init(_borrowOperationsAddress);

        whypeUsdOracle.aggregator = AggregatorV3Interface(_whypeUsdOracleAddress);
        whypeUsdOracle.stalenessThreshold = WHYPE_USD_STALENESS_THRESHOLD;
        whypeUsdOracle.decimals = whypeUsdOracle.aggregator.decimals();

        if(whypeUsdOracle.decimals != WHYPE_USD_DECIMALS) revert WHYPERedStonePriceFeed__InvalidWHYPEOracleDecimals();

        _fetchPrice();

        if(priceFeedDisabled) revert WHYPERedStonePriceFeed__WHYPEOracleDown();
    }

    function _fetchPrice() internal override returns (uint256, bool) {
        (uint256 whypeUsdPrice, bool whypeUsdOracleDown) = _getOracleAnswer(whypeUsdOracle);

        if(whypeUsdOracleDown) return (_disableFeedAndShutDown(address(whypeUsdOracle.aggregator)), true);

        lastGoodPrice = whypeUsdPrice;

        return (whypeUsdPrice, false);
    }
    
}
