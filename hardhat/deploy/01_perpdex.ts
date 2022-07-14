import path from "path"
import { DeployFunction } from 'hardhat-deploy/types';
import { HardhatRuntimeEnvironment } from "hardhat/types";
import { Artifacts } from "hardhat/internal/artifacts";
import { Artifact } from "hardhat/types";

async function _getArtifact(artifactsPath: string, contract: string): Promise<Artifact> {
    const artifacts = new Artifacts(artifactsPath);
    return artifacts.readArtifact(contract);
}

async function _getPerpdexArtifact(contractName: string) {
    return await _getArtifact(path.resolve(__dirname + "/../../deps/perpdex-contract/artifacts"), contractName)
}

async function _deployMarket(deploy, deployer, symbol: string, exchangeAddress: string) {
    const priceFeedBase = await deploy("PerpdexPriceFeedBase"+ symbol, {
        from: deployer,
        contract: 'TestPerpdexPriceFeed',
        args: [],
        log: true,
        autoMine: true,
    })

    const priceFeedQuote = await deploy("PerpdexPriceFeedQuote"+ symbol, {
        from: deployer,
        contract: 'TestPerpdexPriceFeed',
        args: [],
        log: true,
        autoMine: true,
    })
 
    const marketArtifact = await _getPerpdexArtifact("TestPerpdexMarket")
    return await deploy('PerpdexMarket' + symbol, {
        from: deployer,
        contract: {
            abi: marketArtifact.abi,
            bytecode: marketArtifact.bytecode,
        },
        args: [symbol, exchangeAddress, priceFeedBase.address, priceFeedQuote.address],
        log: true,
        autoMine: true,
    })
}

const func: DeployFunction = async function (hre: HardhatRuntimeEnvironment) {
    const {deployments, getNamedAccounts} = hre;
    const {deploy, execute} = deployments;
    const {deployer} = await getNamedAccounts();

    // exchange
    const exchangeArtifact = await _getPerpdexArtifact("TestPerpdexExchange")
    const settlementTokenAddress = hre.ethers.constants.AddressZero;

    const exchange = await deploy('PerpdexExchange', {
        from: deployer,
        contract: {
            abi: exchangeArtifact.abi,
            bytecode: exchangeArtifact.bytecode,
        },
        args: [settlementTokenAddress],
        log: true,
        autoMine: true,
    })
    // market
    const marketBTC = await _deployMarket(deploy, deployer, "BTC", exchange.address)
    await execute(
        "PerpdexExchange",
        {
            from: deployer,
            log: true,
            autoMine: true,
        },
        "setIsMarketAllowed",
        marketBTC.address,
        true,
    )
};

export default func;
