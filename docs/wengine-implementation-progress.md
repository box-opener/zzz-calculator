# W-Engine implementation progress (non-authoritative)

This is a resumable queue, not a game-semantics source. Ordering is the insertion order of the live Nanoka 3.2 W-Engine catalog object fetched from
`https://static.nanoka.cc/zzz/3.2/weapon.json` on 2026-10-02. The engine detail records use the already verified live-3.2 route
`https://static.nanoka.cc/zzz/3.2/zh/weapon/{id}.json`.

The index contains 100 entries. The current loader and reviewed mapping both cover 25 matching IDs. The remaining ordered queue contains 75 index-visible engines. There are currently no packaged raw-only IDs and no reviewed-mapping-only IDs. The existing 15 fixtures remain unchanged and retain their legacy source metadata. New engines keep their complete live detail payload and separate source-index URL. The adapter closes the reviewed W-Engine slice at level 60 and includes Refinement 1–5 values. Non-60 build levels remain an explicit missing-data diagnostic, not a range silently approximated from level-60 values.

The rows marked “已实现” have a raw fixture, reviewed mapping, and compiler branch. Refinement values are selected from their own raw refinement text. Rows marked “部分实现” preserve the known Build/Rule behavior and show a non-blocking diagnostic for result types outside the current damage-request contract.

| Nanoka order | ID | Chinese catalog name | Rank | Specialty | Current state |
|---:|---:|---|:---:|---|---|
| 001 | `12001` | 「月相」-望 | B | 强攻 | 已实现（live raw + reviewed + level-60 Build/Rule + R1–R5 + payload） |
| 002 | `12002` | 「月相」-晦 | B | 强攻 | 已实现（raw + reviewed + conditional wearer damage bonus + R1–R5 + payload） |
| 003 | `12003` | 「月相」-朔 | B | 强攻 | 部分实现（raw + Build + R1–R5；一次性能量回复有资源结果缺口诊断） |
| 004 | `12004` | 「残响」-Ⅰ型 | B | 支援 | 已实现（raw + reviewed + TEAM冲击力panel + R1–R5 + non-stack处理） |
| 005 | `12005` | 「残响」-Ⅱ型 | B | 支援 | 已实现（raw + reviewed + TEAM掌控/精通panel + R1–R5 + non-stack处理） |
| 006 | `12006` | 「残响」-Ⅲ型 | B | 支援 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 007 | `12007` | 「湍流」-铳型 | B | 击破 | 部分实现（raw + Build/EX失衡modifier + R1–R5；Daze结果有非阻断诊断） |
| 008 | `12008` | 「湍流」-矢型 | B | 击破 | 部分实现（raw + Build/主要目标失衡modifier + R1–R5；Daze结果有非阻断诊断） |
| 009 | `12009` | 「湍流」-斧型 | B | 击破 | 已实现（raw + SELF冲击panel active状态 + R1–R5） |
| 010 | `12010` | 「电磁暴」-壹式 | B | 异常 | 已实现（raw + SELF异常掌控panel active状态 + R1–R5） |
| 011 | `12011` | 「电磁暴」-贰式 | B | 异常 | 已实现（raw + Build精通白值 + SELF异常精通panel active状态 + R1–R5） |
| 012 | `12012` | 「电磁暴」-叁式 | B | 异常 | 待实现（仅索引） |
| 013 | `12013` | 「恒等式」-本格 | B | 防护 | 待实现（仅索引） |
| 014 | `12014` | 「恒等式」-变格 | B | 防护 | 待实现（仅索引） |
| 015 | `12015` | 「灰烬」-钴蓝 | B | 命破 | 待实现（仅索引） |
| 016 | `12016` | 「月相」-弦 | B | 锋御 | 待实现（仅索引） |
| 017 | `13001` | 街头巨星 | A | 强攻 | 待实现（仅索引） |
| 018 | `13002` | 时光切片 | A | 支援 | 待实现（仅索引） |
| 019 | `13003` | 雨林饕客 | A | 异常 | 待实现（仅索引） |
| 020 | `13004` | 星徽引擎 | A | 强攻 | 待实现（仅索引） |
| 021 | `13005` | 人为刀俎 | A | 击破 | 待实现（仅索引） |
| 022 | `13006` | 贵重骨核 | A | 击破 | 待实现（仅索引） |
| 023 | `13007` | 正版变身器 | A | 防护 | 待实现（仅索引） |
| 024 | `13008` | 双生泣星 | A | 异常 | 待实现（仅索引） |
| 025 | `13009` | 触电唇彩 | A | 异常 | 待实现（仅索引） |
| 026 | `13010` | 兔能环 | A | 防护 | 待实现（仅索引） |
| 027 | `13011` | 春日融融 | A | 防护 | 待实现（仅索引） |
| 028 | `13012` | 幻变魔方 | A | 命破 | 待实现（仅索引） |
| 029 | `13013` | 鎏金花信 | A | 强攻 | 待实现（仅索引） |
| 030 | `13014` | 电波漫步 | A | 命破 | 待实现（仅索引） |
| 031 | `13015` | 强音热望 | A | 强攻 | 待实现（仅索引） |
| 032 | `13016` | 光影刻刀 | A | 防护 | 待实现（仅索引） |
| 033 | `13017` | 喵运当头 | A | 锋御 | 待实现（仅索引） |
| 034 | `13018` | 咚哒回声 | A | 异常 | 待实现（仅索引） |
| 035 | `13019` | 青漪灵鼎 | A | 命破 | 待实现（仅索引） |
| 036 | `13020` | 炎炙沸釜 | A | 击破 | 待实现（仅索引） |
| 037 | `13021` | 血髓秘匣 | A | 锋御 | 待实现（仅索引） |
| 038 | `13101` | 德玛拉电池Ⅱ型 | A | 击破 | 待实现（仅索引） |
| 039 | `13103` | 聚宝箱 | A | 支援 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 040 | `13106` | 家政员 | A | 强攻 | 待实现（仅索引） |
| 041 | `13108` | 仿制星徽引擎 | A | 强攻 | 待实现（仅索引） |
| 042 | `13111` | 旋钻机-赤轴 | A | 强攻 | 待实现（仅索引） |
| 043 | `13112` | 比格气缸 | A | 防护 | 待实现（仅索引） |
| 044 | `13113` | 含羞恶面 | A | 支援 | 待实现（仅索引） |
| 045 | `13115` | 好斗的阿炮 | A | 支援 | 待实现（仅索引） |
| 046 | `13127` | 维序者-特化型 | A | 防护 | 待实现（仅索引） |
| 047 | `13128` | 轰鸣座驾 | A | 异常 | 待实现（仅索引） |
| 048 | `13135` | 裁纸刀 | A | 击破 | 待实现（仅索引） |
| 049 | `13142` | 震元奇枢 | A | 防护 | 待实现（仅索引） |
| 050 | `13144` | 燔火胧夜 | A | 命破 | 待实现（仅索引） |
| 051 | `14001` | 加农转子 | A | 强攻 | 待实现（仅索引） |
| 052 | `14002` | 逍遥游球 | A | 支援 | 待实现（仅索引） |
| 053 | `14003` | 左轮转子 | A | 击破 | 待实现（仅索引） |
| 054 | `14102` | 钢铁肉垫 | S | 强攻 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 055 | `14104` | 硫磺石 | S | 强攻 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 056 | `14105` | 海妖摇篮 | S | 命破 | 待实现（仅索引） |
| 057 | `14107` | 奔袭獠牙 | S | 防护 | 待实现（仅索引） |
| 058 | `14109` | 霰落星殿 | S | 异常 | 待实现（仅索引） |
| 059 | `14110` | 燃狱齿轮 | S | 击破 | 待实现（仅索引） |
| 060 | `14114` | 拘缚者 | S | 击破 | 待实现（仅索引） |
| 061 | `14116` | 焰心桂冠 | S | 击破 | 待实现（仅索引） |
| 062 | `14117` | 灼心摇壶 | S | 异常 | 待实现（仅索引） |
| 063 | `14118` | 嵌合编译器 | S | 异常 | 待实现（仅索引） |
| 064 | `14119` | 深海访客 | S | 强攻 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 065 | `14120` | 残心青囊 | S | 强攻 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 066 | `14121` | 啜泣摇篮 | S | 支援 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 067 | `14122` | 时流贤者 | S | 异常 | 待实现（仅索引） |
| 068 | `14124` | 防暴者Ⅵ型 | S | 强攻 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 069 | `14125` | 玉壶青冰 | S | 击破 | 待实现（仅索引） |
| 070 | `14126` | 淬锋钳刺 | S | 异常 | 待实现（仅索引） |
| 071 | `14129` | 千面日陨 | S | 强攻 | 待实现（仅索引） |
| 072 | `14130` | 嚣枪喧焰 | S | 强攻 | 待实现（仅索引） |
| 073 | `14131` | 玲珑妆匣 | S | 支援 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 074 | `14132` | 心弦夜响 | S | 强攻 | 待实现（仅索引） |
| 075 | `14133` | 飞鸟星梦 | S | 异常 | 待实现（仅索引） |
| 076 | `14134` | 半糖雪兔 | S | 防护 | 待实现（仅索引） |
| 077 | `14136` | 索魂影眸 | S | 击破 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 078 | `14137` | 青溟笼舍 | S | 命破 | 待实现（仅索引） |
| 079 | `14138` | 牺牲洁纯 | S | 强攻 | 待实现（仅索引） |
| 080 | `14139` | 福虓炉炉 | S | 击破 | 待实现（仅索引） |
| 081 | `14140` | 十方锻星 | S | 异常 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 082 | `14141` | 狸法七变化 | S | 支援 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 083 | `14143` | 云霓孤光 | S | 强攻 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 084 | `14145` | 铸梦炉歌 | S | 支援 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 085 | `14146` | 机巧心种 | S | 强攻 | 待实现（仅索引） |
| 086 | `14147` | 怒目金刚 | S | 命破 | 待实现（仅索引） |
| 087 | `14148` | 昨夜来电 | S | 击破 | 待实现（仅索引） |
| 088 | `14149` | 思络成歌 | S | 支援 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 089 | `14150` | 壳中之灵 | S | 异常 | 待实现（仅索引） |
| 090 | `14151` | 霓虹妄想 | S | 击破 | 待实现（仅索引） |
| 091 | `14152` | 鳞齿寻踪 | S | 强攻 | 待实现（仅索引） |
| 092 | `14153` | 辉骑面铠 | S | 命破 | 待实现（仅索引） |
| 093 | `14154` | 朔月裁霜 | S | 异常 | 待实现（仅索引） |
| 094 | `14155` | 日冕遗蜕 | S | 强攻 | 待实现（仅索引） |
| 095 | `14156` | 琳琅鎏心 | S | 异常 | 待实现（仅索引） |
| 096 | `14157` | 首席跟班 | S | 击破 | 待实现（仅索引） |
| 097 | `14158` | 空羽复归之诗 | S | 异常 | 待实现（仅索引） |
| 098 | `14159` | 骁骑礼赞 | S | 强攻 | 待实现（仅索引） |
| 099 | `14161` | 猩红渴望 | S | 锋御 | 待实现（仅索引） |
| 100 | `14162` | 绯月银棺 | S | 击破 | 待实现（仅索引） |

The first ten missing entries in catalog order are implemented in this batch: `12001`–`12005`, then `12007`–`12011` (existing `12006` was already supported). After review/push, the next unimplemented catalog row is `12012` (「电磁暴」-叁式); continue in index order.
