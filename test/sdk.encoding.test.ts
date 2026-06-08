import { expect } from "chai";
import { decodeStructuredOutput, AbiField, encodeUint256, encodeAddress } from "../sdk/src/utils/encoding";

describe("Dynamic ABI Encoding/Decoding", () => {
  it("should dynamically load and validate schema correctly", () => {
    // Valid case
    const schema: AbiField[] = [
      { name: "id", type: "uint256" },
      { name: "owner", type: "address" }
    ];
    
    // Create some fake data
    // 0x + 64 chars for uint256 + 64 chars for address
    const idHex = "000000000000000000000000000000000000000000000000000000000000002a"; // 42
    const ownerHex = "0000000000000000000000001111111111111111111111111111111111111111";
    const data = "0x" + idHex + ownerHex;

    const result = decodeStructuredOutput(data, schema);
    expect(result.id.toString()).to.equal("42");
    expect(result.owner).to.equal("0x1111111111111111111111111111111111111111");

    // Invalid schema
    expect(() => decodeStructuredOutput(data, {} as any)).to.throw("Invalid schema: must be an array of fields");
  });

  it("should throw on schema mismatch or decoding errors", () => {
    const schema: AbiField[] = [
      { name: "bad_field", type: "unknown_type" as any }
    ];
    const data = "0x0000";

    expect(() => decodeStructuredOutput(data, schema)).to.throw(/Schema mismatch on field bad_field/);
  });
});
