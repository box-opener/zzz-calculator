import type { ImportedShowcase } from "../domain/model/character-build.js";

export interface PlayerDataProvider {
  readonly id: string;
  import(uid: string): Promise<ImportedShowcase>;
}

export function assertZzzUid(uid: string): void {
  if (!/^\d{8,10}$/.test(uid)) {
    throw new Error("绝区零 UID 应为 8 到 10 位数字。");
  }
}
