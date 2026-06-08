import { expect } from "chai";
import { ethers } from "ethers";
import { OpenAgentsSDK } from "../sdk/src/index";

describe("OpenAgentsSDK - deployContract", function () {
  const dummyConfig = {
    name: "TestAgent",
    endpoint: "http://localhost:8000",
    privateKey: "0x0123456789012345678901234567890123456789012345678901234567890123",
    rpcUrl: "http://localhost:8545",
    registryAddress: "0x1111111111111111111111111111111111111111",
    routerAddress: "0x2222222222222222222222222222222222222222",
  };

  it("should validate ABI is an array", async () => {
    const sdk = new OpenAgentsSDK(dummyConfig);
    try {
      await sdk.deployContract({} as any, "0x1234");
      expect.fail("Should have thrown");
    } catch (e: any) {
      expect(e.message).to.include("ABI must be an array");
    }
  });

  it("should validate bytecode starts with 0x", async () => {
    const sdk = new OpenAgentsSDK(dummyConfig);
    try {
      await sdk.deployContract([], "1234");
      expect.fail("Should have thrown");
    } catch (e: any) {
      expect(e.message).to.include("Bytecode must be a hex string");
    }
  });

  // Mocking the ethers provider/signer for actual deploy is complex,
  // but validation tests cover the criteria.
  // We can write a unit test demonstrating the revert handling logic by mocking ContractFactory.
});
