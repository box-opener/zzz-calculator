# ZZZ Calculator

This branch implements the frozen `spec-v1` documents as a new deterministic
Python core. The legacy calculator is intentionally not part of the working
tree; it remains recoverable from the Git history and the `spec-v1` tag.

Current scope is deliberately limited to:

- domain enums and discriminated unions;
- `Character`, `Enemy`, `BattleState`, `DamageEvent`, `AnomalyRecord`, `State`,
  and `Effect` models;
- calculation-node names and aggregation metadata;
- unit tests for structural invariants.

The current Stage18-2 slices additionally include reviewed max-level data for
the Ye Shunguang signature W-Engine `14143`, Astra signature W-Engine `14131`,
and the Stage18-2.5 attack/support validation set. Their static panel
contributions and reviewed damage-relevant combat Effects enter the existing
Build Assembly / Matcher / Execution pipeline; non-damage resource effects are
retained in raw source text but are outside the current damage scope.
Non-max-level W-Engine values are intentionally not part of this slice and
produce an explicit diagnostic.

Natural-language parsing and full event dispatch remain outside this stage;
the existing direct-damage calculator, matcher, and reviewed character/build
compilers are reused by the W-Engine validation slice.

## 米游社角色获取

Windows 可直接双击仓库根目录的 **`run.cmd`**：自动创建/复用 `.venv`、安装 Web 依赖、按锁文件安装前端依赖、构建页面，最后启动本地服务并打开浏览器。路径不依赖当前工作目录。首次配置需要联网；之后依赖配置未变化时复用缓存，但每次都会重新构建前端，确保页面跟随工作区代码。

未找到 Python 3.11+ 时尝试通过 winget 为当前用户安装 Python 3.12；系统没有 winget 时会提示手动安装 Python。未找到兼容的 Node.js 与 npm 时，从 [Node.js 官方发行目录](https://nodejs.org/dist/index.json) 下载并校验 LTS 压缩包，仅解压到项目 `.cache/launcher/runtimes/`。脚本与运行日志都不保存米游社 Cookie。窗口中的 `Ctrl+C` 停止本次启动的服务。

可选参数（命令行执行）：

```powershell
.\run.cmd -Port 8080        # 默认8000；被占用时自动寻找后续空闲端口
.\run.cmd -NoBrowser        # 启动但不自动打开浏览器
.\run.cmd -SetupOnly        # 只配置依赖与构建，不启动服务
.\run.cmd -Reinstall        # 重新安装依赖并构建
```

浏览器米游社缓存按访问地址和端口保存；更换端口时需在新地址重新获取，原地址的缓存仍保留。

安装 Web 依赖并构建前端后，启动同源服务（以下为 Windows PowerShell，命令在仓库根目录执行）：

```powershell
.venv\Scripts\python.exe -m pip install -e '.[web]'
cd frontend
npm ci
npm run build
cd ..
.venv\Scripts\python.exe -m uvicorn web.api:app --host 127.0.0.1 --port 8000
```

打开 `http://127.0.0.1:8000`，展开左侧“从米游社加载我的角色”。默认选择“扫码登录”，点击“生成登录二维码”，使用本人**米游社 App** 扫描并在手机上确认登录。页面显示未扫描、已扫描待确认、登录成功、过期或取消状态；确认后自动读取并填写国服绝区零游戏 UID，多账号时可选择。没有自动读到 UID 时可手动填写，再点击“获取并保存角色”。生成二维码本身不会登录账号，确认登录需由使用者在米游社 App 完成。

“手动 Cookie”入口继续保留：切换后输入**国服绝区零游戏 UID** 和本人米游社登录 Cookie，点击“获取并保存角色”。UID 不是米游社账号 ID；完整装备需要已登录账号的战绩权限。Cookie 可在本人浏览器登录米游社、打开绝区零战绩后，从开发者工具 Network 中该战绩请求的 Request Headers 复制 `Cookie` 内容；不要把 Cookie 发到聊天或提交到仓库。

二维码本地有效期最多三分钟（遵循官方返回的更短期限）；扫码确认后，本次登录最多十分钟。扫码 Cookie 只在本次服务器进程内存中暂存，浏览器只持有随机会话标识，Cookie 不下发到浏览器或写入文件。点击“退出登录”、切换到手动 Cookie、刷新/离开页面时清理本次扫码会话；即使关闭页面时取消请求未能送达，后端也会在期限到达后清除凭据。刷新页面或重启服务需要重新扫码。角色资料缓存仍可独立加载。

获取到的角色、影画、技能、潜能、实际音擎和驱动盘按 UID 保存在当前浏览器，最多保留最近五个账号。刷新页面后可从“已保存账号”直接加载，不需要再次请求米游社；“加载到当前槽位”替换当前操作角色，角色已在队伍中时选中并更新该角色。原有从零配置和 JSON 导入、导出仍可使用。手动 Cookie 输入框在请求开始时清空，Cookie 不写入本地缓存、服务器文件或返回资料。清除本地资料后需要重新获取。

**扫码成功后获取角色仍提示验证码**：这属于角色战绩的安全验证。页面会提供“完成安全验证并继续获取”，点击后由本人完成弹出的极验验证。程序把验证结果交给米游社校验，确认通过后自动继续读取角色，无需重新扫码或重新填写 Cookie。验证沿用扫码设备标识、原账号凭据和 UID；校验通过的挑战信息只在当前扫码会话内存中沿用。取消、过期或米游社不接受验证时不会覆盖已有角色缓存。

待完成的验证会话最多保留五分钟，扫码退出会同步取消关联验证；手动 Cookie 模式触发验证时，凭据也仅在后端内存暂存至完成、取消或到期。验证码组件只在点击验证按钮时从 [极验官方静态地址](https://static.geetest.com/static/js/gt.0.5.2.js) 加载，验证码操作由使用者完成；没有自动解题或离线放行。修改代码后需要停止旧运行窗口，再双击 `run.cmd`，让后端加载修复后的流程。

**完成验证码后仍提示失败**：页面现在区分验证提交失败和验证通过后的角色读取失败；米游社明确拒绝时会显示数字错误码。先确认已重启旧后端，再重试；反馈时提供页面提示或运行日志中的 `stage`、`exception`、`retcode` 行即可，不要提供 Cookie 或验证码结果。诊断日志只记录阶段、异常类型和数字错误码。

当前计算内核只审定了**60级角色、满核心突破（核心7级）、60级音擎与S级15级驱动盘**。其他实际养成等级、未接入角色或装备仍保存源资料并显示原因，加载按钮不可用；不以满级或默认装备代替。未装备音擎、空驱动盘槽位保持为空。米游社显示的最终局外面板只作源资料参考，计算器沿用现有角色/装备模型组装面板；三、五影的技能等级加成在导入时还原为基础等级，避免重复加成。

登录过期、隐私限制、验证码、实名/身份验证、限流和超时会显示对应提示。战绩验证码可在当前页面完成，实名/身份验证需在米游社 App 完成；失败或取消获取不覆盖已有缓存。当前接入仅支持国服 `prod_gf_cn`。扫码登录、由使用者完成验证码后的角色读取已通过真实账号联调；后端1411项、前端180项测试及生产构建通过。

接口为 `POST /api/v1/miyoushe/characters`，请求包含字符串 `uid` 和 `cookie`，返回版本化的 `zzz-miyoushe-profile-v1` 资料；加载配置复用 `zzz-character-config-v2`。登录签名由 [genshin.py](https://github.com/seriaati/genshin.py) 处理，角色列表与装备读取依据 [ZZZeroUID 的接口说明](https://github.com/ZZZure/ZZZeroUID/blob/master/docs/API%E4%B8%8E%E5%AE%98%E6%96%B9%E8%AF%84%E5%88%86%E8%AF%B4%E6%98%8E.md) 和 [SDK 角色模型](https://github.com/seriaati/genshin.py/blob/master/genshin/models/zzz/character.py)；技能有效等级还原及副词条强化次数分别参考 [Seelie 同步脚本](https://greasyfork.org/en/scripts/544867-zzz-seelie-%E6%95%B0%E6%8D%AE%E5%90%8C%E6%AD%A5/code) 和 [Enka→米游社字段转换](https://github.com/ZZZure/ZZZeroUID/blob/master/ZZZeroUID/utils/enka_to_mys.py)。源资料转换不修改项目规则文档或伤害公式。

扫码接口为 `POST /api/v1/miyoushe/qr/start`、`/qr/status` 与 `/qr/cancel`，查询/取消的会话标识放在 JSON 请求体中；响应禁止缓存。扫码后的角色获取请求改为 `{ "uid": "游戏UID", "qr_session": "本次会话标识" }`，与手动 `cookie` 二选一。二维码由本地 [python-qrcode](https://github.com/lincolnloop/python-qrcode) 渲染，不使用外部二维码图片服务。创建/查询协议及确认响应头的六个登录 Cookie 字段参考 [SDK 扫码实现](https://github.com/seriaati/genshin.py/blob/master/genshin/client/components/auth/subclients/app.py)、[扫码 Cookie 模型](https://github.com/seriaati/genshin.py/blob/master/genshin/models/auth/cookie.py) 和 [接口采集文档](https://github.com/UIGF-org/mihoyo-api-collect/blob/main/hoyolab/login/qrcode_hoyolab.md)。本地会话容量为20个，查询限频两秒一次；部署保持默认单进程，同一个会话的请求需要落在创建它的进程。

## Tests

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m pytest
```
