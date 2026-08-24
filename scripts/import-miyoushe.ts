import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import {
  chromium,
  type BrowserContext,
  type Page,
  type Request,
} from "playwright-core";
import { assertZzzUid } from "../src/importers/provider.js";
import {
  captureMiyousheResponse,
  type CapturedMiyousheResponse,
} from "../src/importers/miyoushe/capture.js";
import { mapMiyousheResponse } from "../src/importers/miyoushe/map-miyoushe-build.js";
import type {
  MiyousheAvatarDetail,
  MiyousheDetailResponse,
} from "../src/importers/miyoushe/types.js";

const CULTIVATE_URL =
  "https://act.mihoyo.com/zzz/event/character-builder/index.html" +
  "?game_biz=nap_cn&mhy_auth_required=1&mhy_presentation_style=fullscreen";
const CHROME_PATH =
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

const uid = process.argv[2];
const characterId = process.argv[3];
if (!uid) {
  console.error("用法：npm run import:miyoushe -- <UID>");
  process.exitCode = 1;
} else {
  try {
    assertZzzUid(uid);
    await runCapture(uid, characterId);
  } catch (error) {
    console.error(`米游社导入失败：${String(error)}`);
    process.exitCode = 1;
  }
}

async function runCapture(uid: string, characterId?: string): Promise<void> {
  const profileDir = path.resolve(".cache/miyoushe-browser");
  const outputDir = path.resolve(".cache/uid/miyoushe", uid);
  await mkdir(profileDir, { recursive: true });
  await mkdir(outputDir, { recursive: true });

  let context: BrowserContext | undefined;
  try {
    context = await chromium.launchPersistentContext(profileDir, {
      executablePath: CHROME_PATH,
      headless: false,
      viewport: { width: 430, height: 900 },
      locale: "zh-CN",
    });
    const page = context.pages()[0] ?? (await context.newPage());
    let basicCapture: CapturedMiyousheResponse | undefined;
    let expectedCharacterIds: string[] = [];
    const detailsById = new Map<string, MiyousheAvatarDetail>();
    let detailRequestStarted = false;
    let requestError: unknown;

    page.on("response", (response) => {
      void captureMiyousheResponse(response, uid)
        .then(async (capture) => {
          if (!capture) return;
          if (capture.endpoint === "avatar-basic-list") {
            basicCapture = capture;
            await writeFile(
              path.join(outputDir, "avatar-basic-list.json"),
              JSON.stringify(capture, null, 2),
            );
            if (!detailRequestStarted) {
              expectedCharacterIds = getUnlockedCharacterIds(
                capture.payload,
                characterId,
              );
              if (expectedCharacterIds.length === 0) {
                throw new Error(
                  characterId
                    ? `米游社角色列表中没有已解锁的角色 ${characterId}。`
                    : "米游社角色列表中没有已解锁角色。",
                );
              }
              console.log(`已读取角色列表：${expectedCharacterIds.length} 名已拥有角色。`);
              detailRequestStarted = true;
              await requestCharacterDetails(
                page,
                response.request(),
                uid,
                expectedCharacterIds,
              );
            }
            return;
          }

          for (const detail of getDetails(capture.payload)) {
            const id = String(detail.avatar.id);
            if (expectedCharacterIds.includes(id) && detail.avatar.level > 0) {
              detailsById.set(id, detail);
            }
          }
          if (expectedCharacterIds.length > 0) {
            console.log(
              `已读取角色详情：${detailsById.size}/${expectedCharacterIds.length}`,
            );
          }
        })
        .catch((error: unknown) => {
          requestError = error;
        });
    });

    console.log("已打开米游社官方养成指南。首次使用请在窗口中完成登录。");
    console.log(
      characterId
        ? `登录后将自动读取角色 ID ${characterId} 的详情。`
        : "登录后将自动分批读取账号上的全部已拥有角色。",
    );
    await page.goto(CULTIVATE_URL, { waitUntil: "domcontentloaded" });

    const deadline = Date.now() + 5 * 60_000;
    while (
      Date.now() < deadline &&
      (expectedCharacterIds.length === 0 ||
        detailsById.size < expectedCharacterIds.length)
    ) {
      if (requestError) throw requestError;
      if (page.isClosed()) break;
      await page.waitForTimeout(1_000);
    }

    if (
      expectedCharacterIds.length === 0 ||
      detailsById.size < expectedCharacterIds.length
    ) {
      throw new Error(
        `5 分钟内未完成角色详情读取（${detailsById.size}/${expectedCharacterIds.length}）。`,
      );
    }

    if (!basicCapture) throw new Error("角色列表响应丢失。");
    const details = expectedCharacterIds
      .map((id) => detailsById.get(id))
      .filter((detail): detail is MiyousheAvatarDetail => Boolean(detail));
    const detailResponse: MiyousheDetailResponse = {
      retcode: 0,
      message: "OK",
      data: { list: details },
    };
    await writeFile(
      path.join(outputDir, "avatar-details.json"),
      JSON.stringify(
        {
          endpoint: "avatar-details",
          capturedAt: new Date().toISOString(),
          payload: detailResponse,
        },
        null,
        2,
      ),
    );
    const normalized = mapMiyousheResponse(
      uid,
      detailResponse,
    );
    const normalizedDir = path.resolve(".cache/uid/normalized");
    await mkdir(normalizedDir, { recursive: true });
    const normalizedPath = path.join(normalizedDir, `${uid}.json`);
    await writeFile(normalizedPath, JSON.stringify(normalized, null, 2));

    console.log(`米游社原始数据已保存到：${outputDir}`);
    console.log(`标准角色配置已保存到：${normalizedPath}`);
    console.log("登录凭据仅保存在本机浏览器配置中，项目不会读取或导出 Cookie。");
  } finally {
    await context?.close();
  }
}

async function requestCharacterDetails(
  page: Page,
  sourceRequest: Request,
  uid: string,
  characterIds: string[],
): Promise<void> {
  const sourceUrl = new URL(sourceRequest.url());
  const region = sourceUrl.searchParams.get("region") ?? "prod_gf_cn";
  const deviceId = await sourceRequest.headerValue("x-rpc-device_id");
  const deviceFp = await sourceRequest.headerValue("x-rpc-device_fp");
  const headers: Record<string, string> = { "content-type": "application/json" };
  if (deviceId) headers["x-rpc-device_id"] = deviceId;
  if (deviceFp) headers["x-rpc-device_fp"] = deviceFp;

  for (let index = 0; index < characterIds.length; index += 10) {
    const batch = characterIds.slice(index, index + 10);
    await page.evaluate(
      async ({ requestUrl, requestHeaders, requestBody }) => {
        const response = await fetch(requestUrl, {
          method: "POST",
          credentials: "include",
          headers: requestHeaders,
          body: JSON.stringify(requestBody),
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
      },
      {
        requestUrl:
          "https://act-api-takumi.mihoyo.com/event/nap_cultivate_tool" +
          `/user/batch_avatar_detail_v2?uid=${uid}&region=${region}`,
        requestHeaders: headers,
        requestBody: {
          avatar_list: batch.map((id) => ({
            avatar_id: Number(id),
            is_teaser: false,
            teaser_need_weapon: false,
            teaser_sp_skill: false,
          })),
        },
      },
    );
  }
}

function getUnlockedCharacterIds(
  payload: unknown,
  characterId?: string,
): string[] {
  const response = payload as {
    data?: { list?: Array<{ unlocked?: boolean; avatar?: { id?: number } }> };
  };
  return (response.data?.list ?? [])
    .filter(
      (item) =>
        item.unlocked &&
        item.avatar?.id !== undefined &&
        (!characterId || String(item.avatar.id) === characterId),
    )
    .map((item) => String(item.avatar?.id));
}

function getDetails(payload: unknown): MiyousheAvatarDetail[] {
  return (
    (payload as MiyousheDetailResponse).data?.list?.filter(
      (detail) => detail.avatar?.id !== undefined,
    ) ?? []
  );
}
