import assert from "node:assert/strict";
import test from "node:test";
import {
  classifyMiyousheUrl,
  isSuccessfulPayload,
  responseMatchesUid,
} from "../src/importers/miyoushe/capture.js";

test("识别米游社角色列表与详情接口", () => {
  assert.equal(
    classifyMiyousheUrl(
      "https://act-api-takumi.mihoyo.com/event/nap_cultivate_tool/user/avatar_basic_list?uid=16241824",
    ),
    "avatar-basic-list",
  );
  assert.equal(
    classifyMiyousheUrl(
      "https://act-api-takumi.mihoyo.com/event/nap_cultivate_tool/user/batch_avatar_detail_v2?uid=16241824",
    ),
    "avatar-detail",
  );
  assert.equal(classifyMiyousheUrl("https://example.com/image.png"), null);
});

test("只接受目标 UID 和成功响应", () => {
  assert.equal(
    responseMatchesUid("https://example.com/api?uid=16241824", "16241824"),
    true,
  );
  assert.equal(
    responseMatchesUid("https://example.com/api?uid=10000000", "16241824"),
    false,
  );
  assert.equal(isSuccessfulPayload({ retcode: 0, data: { list: [] } }), true);
  assert.equal(isSuccessfulPayload({ retcode: -100, data: null }), false);
});
