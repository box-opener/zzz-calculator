import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { EnkaUidClient, EnkaUidError } from "../src/importers/enka/client.js";
import { mapEnkaShowcase } from "../src/importers/enka/map-enka-build.js";

const uid = process.argv[2];
if (!uid) {
  console.error("用法：npm run import:uid -- <UID>");
  process.exitCode = 1;
} else {
  try {
    const client = new EnkaUidClient();
    const response = await client.fetch(uid);
    const showcase = mapEnkaShowcase(response.data);
    if (response.warning) showcase.warnings.push(response.warning);

    const outputDir = ".cache/uid/normalized";
    const outputPath = path.join(outputDir, `${uid}.json`);
    await mkdir(outputDir, { recursive: true });
    await writeFile(outputPath, JSON.stringify(showcase, null, 2));

    console.log(`已导入 ${showcase.builds.length} 名公开展示角色。`);
    console.log(`标准配置：${outputPath}`);
    if (showcase.warnings.length > 0) {
      console.warn(showcase.warnings.join("\n"));
    }
  } catch (error) {
    if (error instanceof EnkaUidError) {
      console.error(
        `UID 导入失败${error.status ? `（HTTP ${error.status}）` : ""}：${error.message}`,
      );
    } else {
      console.error(`UID 导入失败：${String(error)}`);
    }
    process.exitCode = 1;
  }
}

