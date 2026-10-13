# 米游社导入断点（2026-10-13，用户已暂停）

WIP，用户最新明确米游社暂停，不自动恢复。分支codex/miyoushe-import，基础24af5cb，未合main；main现292e487。
草稿：web/miyoushe_import.py内存扫码/角色/详情服务、mapper、API、中文UI；实际盘词条/等级、音擎白值/主词条、可用角色低等级成长及fixtures。当前全树未统一测试/build，旧快照build/AST通过不代表当前验证。
真实官方app/createQRLogin挑战成功生成并展示过临时PNG；尚无扫码确认、真实角色详情或端到端导入证据。QR/凭据/session不入Git，暂停后应停止临时auth服务，恢复时重新生成码。
自动审批拒绝上传详细浏览器指纹，用户未授权；假Android/Xiaomi与伪device_fp已移除。noFP官方扫码可行；如详情要求验证不得绕过，若真需指纹须明确字段/用途/米哈游接收方并获用户授权。
官方H5/维护者协议支持avatar_basic_list/batch_avatar_detail_v2与avatar/equip/weapon结构。还缺脱敏真实已注册角色样例；技能/C3C5口径保现值、缺明确refinement保音擎、Astra/Ye低级缺白值保等级、词条百分比单位及ID待样例校准；不得用最终面板或roll回推造假。
新授权后完整收尾，然后统一tests/build；审主分支App/API/registry/calculation_service/wengine交叉变更，不自行merge。登录用官方扫码，不向用户索Cookie，不永久保存credential。
