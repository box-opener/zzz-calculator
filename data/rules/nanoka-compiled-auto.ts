import compiledDatabase from "../compiled/nanoka-buffs-3.2.1+17934514.json" with { type: "json" };
import type { BuffRule } from "../../src/domain/model/buff.js";

interface CompiledNanokaEntry {
  disposition: string;
  rule?: BuffRule | null;
  rules?: readonly BuffRule[];
}

interface CompiledNanokaDatabase {
  version: string;
  entries: readonly CompiledNanokaEntry[];
}

const database = compiledDatabase as CompiledNanokaDatabase;

/**
 * 解析器已经判定为 auto-accepted 的规则直接从版本化静态数据库进入运行时。
 *
 * 这里故意不复制任何角色/音擎/驱动盘规则：下一次 Nanoka 更新后，重新执行
 * parse:nanoka:buffs 即可替换这份输入。存在人工审查修订的规则由 reviewed
 * batch 显式覆盖，避免把旧候选的 partial 版本带回计算。
 */
export const NANOKA_COMPILED_AUTO_ACCEPTED_RULES: readonly BuffRule[] =
  database.entries
    .filter((entry) => entry.disposition === "auto-accepted")
    .flatMap((entry) => entry.rules ?? (entry.rule ? [entry.rule] : []))
    .filter((rule) => rule.status === "verified");

export const NANOKA_COMPILED_AUTO_ACCEPTED_VERSION = database.version;
