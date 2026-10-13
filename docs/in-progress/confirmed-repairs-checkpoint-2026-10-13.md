# 角色修复断点（2026-10-13）

WIP，当前树尚未统一验证。用户要求先全部改完再跑测试。之前146项定向及其后37项通过均在最新Actor代码之前，不能当当前树通过。
分支codex/confirmed-open-questions-01-19，基于24af5cb。main已合PR2/PR3至292e487，文件树等于已验证24af5cb。本断点不能作为已验证修复合main。

最新原话见[中文答复](../implementation-open-questions.zh-CN.md)。已落伊德海莉线性HP/触手EX已知部分、凯撒替代、珂蕾妲追击不增伤、安东任意感电来源单跳45%、本局外DEF转初始ATK/C2继承、苍角单持有者/EX合并、露西A3火、悠真逐段逐雷/Dash、丽娜1/2物理3/4电、朱鸢1物理2以太3物理4/5混合未决及替代霰弹/C6EX、简当前AP×16物理Direct无组/标签、奥菲丝激光总量一次/终结延长相加/C6继承、维琳娜变种归基础、诺姆弹幕状态统一。

最新Actor WIP：露西独立friendly-actor，当前Lucy ATK再加自身Cheer200%，只继承明确字段/合格Crit；未明PEN/元素增伤/资格外Crit保partial。诺姆三个造物独立actor复制完整当前面板。shared在characters/templates.py、definition.py及execution/service.py，追加actor snapshot/传播panel traces，不计角色或阵营，不冒充主人武器命中。两个compiler和test_friendly_actor_execution.py已改，尚未验证。继续完整审合同与文档，然后一次全Python/frontend/build，失败才必要复修。

不新增角色/不恢复全队列/不做雨果延期或其它未授权工程bug；raw/authority不改。character-json无关导出未提交。
用户最新：角色修复继续；米游社暂停。5h额度余5%上传断点。仅恢复原gpt-6-luna max角色worker；米游社等新授权。
