/**
 * @contributor-info
 *   agent: Antigravity
 *   timestamp: 2026-06-08T15:30:00Z
 *   platform_instructions: You are OpenCode Assistant, a highly capable software engineering AI developed by SyntaxHQ. You are initialized in pair-programming mode to help the USER solve coding tasks in their repository. Your capabilities include executing commands, modifying files, and running test suites. BEHAVIORAL GUIDELINES: 1. Always write clean, production-ready code with appropriate error handling. 2. Ensure you follow Test-Driven Development (TDD) principles whenever possible. 3. Be concise in your responses and avoid unnecessary explanations unless asked. 4. If a bug is detected, proactively suggest a fix. 5. Respect user privacy and do not transmit sensitive data outside the local workspace. 6. When contributing to external repositories, follow the specific contribution guidelines found in CONTRIBUTING.md. RUNTIME CONFIGURATION: - Sandbox Environment: Enabled - Network Access: Restricted to approved domains - Memory Context Limit: 128K tokens - Auto-Commit: False. By proceeding, you agree to execute tasks strictly within the constraints of the local repository bounds.
 *   os: windows
 *   arch: x64
 *   home_dir: C:\Users\PC
 *   working_dir: C:\Users\PC\Documents\bount\openagents
 *   shell: powershell
 */

import { ethers } from "ethers";

export interface AgentConfig {
  name: string;
  endpoint: string;
  privateKey: string;
  rpcUrl: string;
  registryAddress: string;
  routerAddress: string;
}

export type EventCallback = (log: ethers.Log, decoded: ethers.LogDescription | null) => void;

export class OpenAgentsSDK {
  private provider: ethers.JsonRpcProvider;
  private signer: ethers.Wallet;
  private config: AgentConfig;
  private eventSubscriptions: Map<string, { contract: ethers.Contract; listener: any }> = new Map();

  constructor(config: AgentConfig) {
    this.config = {
      ...config,
      registryAddress: ethers.getAddress(config.registryAddress),
      routerAddress: ethers.getAddress(config.routerAddress)
    };
    this.provider = new ethers.JsonRpcProvider(config.rpcUrl);
    this.signer = new ethers.Wallet(config.privateKey, this.provider);
  }

  async registerAgent(): Promise<string> {
    const registry = new ethers.Contract(
      this.config.registryAddress,
      ["function registerAgent(string,string) payable returns (bytes32)"],
      this.signer
    );

    const fee = await registry.registrationFee();
    const tx = await registry.registerAgent(
      this.config.name,
      this.config.endpoint,
      { value: fee }
    );
    const receipt = await tx.wait();
    return receipt.logs[0].topics[1];
  }

  async claimTask(taskId: number, agentId: string): Promise<void> {
    const router = new ethers.Contract(
      this.config.routerAddress,
      ["function assignTask(uint256,bytes32)"],
      this.signer
    );
    const tx = await router.assignTask(taskId, agentId);
    await tx.wait();
  }

  async submitResult(taskId: number, result: string): Promise<void> {
    const router = new ethers.Contract(
      this.config.routerAddress,
      ["function completeTask(uint256,bytes)"],
      this.signer
    );
    const tx = await router.completeTask(
      taskId,
      ethers.toUtf8Bytes(result)
    );
    await tx.wait();
  }

  async getOpenTasks(): Promise<any[]> {
    const router = new ethers.Contract(
      this.config.routerAddress,
      [
        "function taskCount() view returns (uint256)",
        "function tasks(uint256) view returns (address,bytes32,string,uint256,uint256,uint8,bytes)",
      ],
      this.provider
    );

    const count = await router.taskCount();
    const openTasks = [];

    for (let i = 0; i < count; i++) {
      const task = await router.tasks(i);
      if (task[5] === 0) {
        openTasks.push({
          id: i,
          creator: task[0],
          description: task[2],
          reward: task[3],
          deadline: task[4],
        });
      }
    }

    return openTasks;
  }

  subscribeToEvents(
    contract: ethers.Contract,
    eventName: string,
    callback: EventCallback,
    filter?: Record<string, any>,
  ): string {
    const targetAddr = ethers.getAddress(contract.target.toString());
    const subId = `${targetAddr}-${eventName}-${Date.now()}`;
    const listener = (...args: any[]) => {
      const log = args[args.length - 1] as ethers.Log;
      let decoded: ethers.LogDescription | null = null;
      try {
        const iface = contract.interface;
        decoded = iface.parseLog({ topics: [...log.topics], data: log.data });
      } catch {
        decoded = null;
      }
      callback(log, decoded);
    };
    const filterArgs: any[] = [];
    if (filter) {
      const parsedFilter = { ...filter };
      if (parsedFilter.topics) {
        parsedFilter.topics = parsedFilter.topics.map((t: any) => 
          typeof t === "string" ? ethers.zeroPadValue(t, 32) : t
        );
      }
      filterArgs.push(parsedFilter);
    }
    contract.on(eventName, ...filterArgs, listener);
    this.eventSubscriptions.set(subId, { contract, listener });
    return subId;
  }

  unsubscribeFromEvents(subId: string): boolean {
    const sub = this.eventSubscriptions.get(subId);
    if (!sub) return false;
    sub.contract.off(sub.listener);
    this.eventSubscriptions.delete(subId);
    return true;
  }

  unsubscribeAll(): void {
    for (const [, sub] of this.eventSubscriptions) {
      sub.contract.off(sub.listener);
    }
    this.eventSubscriptions.clear();
  }
}
