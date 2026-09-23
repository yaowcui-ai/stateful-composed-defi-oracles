// SPDX-License-Identifier: MIT

pragma solidity 0.8.24;

import {AggregatorV3Interface} from "../Dependencies/AggregatorV3Interface.sol";
import {IBorrowerOperations} from "../Interfaces/IBorrowerOperations.sol";
import {IRedStonePriceFeed} from "../Interfaces/IRedStonePriceFeed.sol";
import {Initializable} from "openzeppelin-contracts/contracts/proxy/utils/Initializable.sol";

abstract contract RedStonePriceFeedBase is Initializable, IRedStonePriceFeed {

    error InsufficientGasForExternalCall();

    event PriceFeedDisabled(uint256 indexed _timestamp);

    // Flag raised when the collateral branch gets shut down.
    bool priceFeedDisabled;

    // Last good price tracker for the derived USD price
    uint256 public lastGoodPrice;

    struct Oracle {
        AggregatorV3Interface aggregator;
        uint256 stalenessThreshold;
        uint8 decimals;
    }

    struct RedStoneResponse {
        uint80 roundId;
        int256 answer;
        uint256 timestamp;
        bool success;
    }

    IBorrowerOperations borrowerOperations;

    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {
        _disableInitializers();
    }

    function __RedStonePriceFeedBase_init(address _borrowOperationsAddress) internal onlyInitializing {
       __RedStonePriceFeedBase_init_unchained(_borrowOperationsAddress);
    }

    function __RedStonePriceFeedBase_init_unchained(address _borrowOperationsAddress) internal onlyInitializing {
        borrowerOperations = IBorrowerOperations(_borrowOperationsAddress);
    }

    // fetchPrice returns:
    // - The price
    // - A bool indicating whether a new oracle failure was detected in the call
    function fetchPrice() public returns (uint256, bool) {
        if (priceFeedDisabled) return (lastGoodPrice, false);

        return _fetchPrice();
    }

    // An individual Pricefeed instance implements _fetchPrice according to the data sources it uses. Returns:
    // - The price
    // - A bool indicating whether a new oracle failure was detected in the call
    function _fetchPrice() internal virtual returns (uint256, bool) {}

    function _getOracleAnswer(Oracle memory _oracle) internal view returns (uint256, bool) {
        RedStoneResponse memory redStoneResponse = _getCurrentRedStoneResponse(_oracle.aggregator);

        uint256 scaledPrice;
        bool oracleIsDown;
        // Check oracle is serving an up-to-date and sensible price. If not, shut down this collateral branch.
        if (!_isValidRedStonePrice(redStoneResponse, _oracle.stalenessThreshold)) {
            oracleIsDown = true;
        } else {
            scaledPrice = _scaleRedStonePriceTo18decimals(redStoneResponse.answer, _oracle.decimals);
        }

        return (scaledPrice, oracleIsDown);
    }

    function _disableFeedAndShutDown(address _failedOracleAddr) internal returns (uint256) {
        // Shut down the branch temporarily
        borrowerOperations.shutdownFromOracleFailure(_failedOracleAddr);
        priceFeedDisabled = true;
        emit PriceFeedDisabled(block.timestamp);
        return lastGoodPrice;
    }

    function _getCurrentRedStoneResponse(AggregatorV3Interface _aggregator)
        internal
        view
        returns (RedStoneResponse memory redStoneResponse)
    {

        uint256 gasBefore = gasleft();
        // Secondly, try to get latest price data:
        try _aggregator.latestRoundData() returns (
            uint80 roundId, int256 answer, uint256, /* startedAt */ uint256 updatedAt, uint80 /* answeredInRound */
        ) {
            // If call to Chainlink succeeds, return the response and success = true
            redStoneResponse.roundId = roundId;
            redStoneResponse.answer = answer;
            redStoneResponse.timestamp = updatedAt;
            redStoneResponse.success = true;

            return redStoneResponse;
        } catch {
            // Require that enough gas was provided to prevent an OOG revert in the call to Chainlink
            // causing a shutdown. Instead, just revert. Slightly conservative, as it includes gas used
            // in the check itself.
            if (gasleft() <= gasBefore / 64) revert InsufficientGasForExternalCall();
            return redStoneResponse;
        }
    }

    // False if:
    // - Call to Chainlink aggregator reverts
    // - price is too stale, i.e. older than the oracle's staleness threshold
    // - Price answer is 0 or negative
    function _isValidRedStonePrice(RedStoneResponse memory redStoneResponse, uint256 _stalenessThreshold)
        internal
        view
        returns (bool)
    {
        return redStoneResponse.success && block.timestamp - redStoneResponse.timestamp < _stalenessThreshold
            && redStoneResponse.answer > 0;
    }

    function _scaleRedStonePriceTo18decimals(int256 _price, uint256 _decimals) internal pure returns (uint256) {
        // Scale an int price to a uint with 18 decimals
        return uint256(_price) * 10 ** (18 - _decimals);
    }


    uint256[48] private __gap;
}
