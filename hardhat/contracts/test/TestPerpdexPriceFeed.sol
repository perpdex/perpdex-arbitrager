// SPDX-License-Identifier: GPL-3.0-or-later
pragma solidity 0.7.6;

contract TestPerpdexPriceFeed {
    uint8 _decimals;
    uint256 _price;

    function decimals() external view returns (uint8) {
        return _decimals;
    }

    function getPrice() external view returns (uint256) {
        return _price;
    }

    function setDecimals(uint8 value) external {
        _decimals = value;
    }

    function setPrice(uint256 price) external {
        _price = price;
    }
}
