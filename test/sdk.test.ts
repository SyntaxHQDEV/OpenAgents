import { expect } from "chai";
import { ethers } from "ethers";
import { OpenAgentsSDK } from "../sdk/src/index";

describe("OpenAgentsSDK", function () {
  const dummyConfig = {
    name: "TestAgent",
    endpoint: "http://localhost:8000",
    privateKey: "0x0123456789012345678901234567890123456789012345678901234567890123",
    rpcUrl: "http://localhost:8545",
    registryAddress: "0x1111111111111111111111111111111111111111",
    routerAddress: "0x2222222222222222222222222222222222222222",
  };

  it("should validate and checksum contract addresses on initialization", () => {
    // lowercase addresses
    const config = {
      ...dummyConfig,
      registryAddress: "0x1111111111111111111111111111111111111111",
      routerAddress: "0x2222222222222222222222222222222222222222",
    };
    const sdk = new OpenAgentsSDK(config);
    expect((sdk as any).config.registryAddress).to.equal(ethers.getAddress(config.registryAddress));
  });

  it("should throw error on invalid addresses", () => {
    const config = {
      ...dummyConfig,
      registryAddress: "0xinvalid",
    };
    expect(() => new OpenAgentsSDK(config)).to.throw();
  });

  it("should properly pad topics to 32 bytes in subscribeToEvents", () => {
    const sdk = new OpenAgentsSDK(dummyConfig);
    const mockContract = {
      target: "0x3333333333333333333333333333333333333333",
      on: (...args: any[]) => {},
      off: (...args: any[]) => {},
      interface: {
        parseLog: () => null
      }
    } as unknown as ethers.Contract;

    const filter = {
      topics: ["0x1234"]
    };

    let paddedTopics: any[] = [];
    mockContract.on = (eventName: string, passedFilter: any, listener: any) => {
      paddedTopics = passedFilter.topics;
    };

    sdk.subscribeToEvents(mockContract, "TaskCreated", () => {}, filter);

    expect(paddedTopics[0]).to.equal(ethers.zeroPadValue("0x1234", 32));
  });
});
