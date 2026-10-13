# ZZZ Calculator

![ZZZ Calculator](frontend/public/brand/zzz-calculator-logo-wide.png)

绝区零角色与装备伤害计算器，使用 Python 计算内核和 React 网页界面。支持配置队伍、音擎与驱动盘，也可从米游社导入国服账号的角色和实际装备。程序在本机运行，通过浏览器使用。

## 快速启动（Windows）

1. 在 GitHub 项目页点击 **Code → Download ZIP**，下载完整项目并解压；也可使用 Git 克隆仓库。下载 ZIP 时先解压，再运行里面的文件。
2. 打开项目根目录，也就是同时包含 `run.cmd`、`scripts`、`frontend` 和 `pyproject.toml` 的文件夹。
3. **双击 [run.cmd](run.cmd)**，保持打开的运行窗口，等待环境配置和前端构建完成。首次启动需要联网下载依赖，耗时取决于网络情况。
4. 浏览器会自动打开计算器。若没有自动打开，复制运行窗口中“已启动”后面的地址到浏览器，默认是 [http://127.0.0.1:8000](http://127.0.0.1:8000)。

使用期间请保持运行窗口打开；**停止服务时，在该窗口按 `Ctrl+C`**。以后启动仍双击 `run.cmd`；更新项目代码后，先停止旧服务，再重新启动。

启动入口 `run.cmd` 调用 [scripts/run.ps1](scripts/run.ps1)，自动完成：

- 检查 Python 3.11+，创建或复用项目的 `.venv`，安装后端 Web 依赖。
- 检查 Node.js 与 npm，按 `frontend/package-lock.json` 安装前端依赖。
- 构建网页，启动本地服务，等待服务就绪后打开浏览器。

脚本使用 Windows PowerShell 5.1 或更高版本。未找到 Python 时会尝试通过 winget 为当前用户安装 Python 3.12；没有 winget 时，按提示手动安装 Python 3.11+ 后重新运行。未找到兼容的 Node.js 与 npm 时，会从 Node.js 官方下载并校验 LTS 压缩包，解压到项目 `.cache/launcher/runtimes/`。

后续启动在依赖配置未变化时复用已安装依赖，每次仍会重新构建网页。启动脚本按自身位置寻找项目，无需提前切换工作目录。

### Windows 启动参数

在项目根目录打开 PowerShell，可执行：

```powershell
.\run.cmd                  # 正常启动并打开浏览器
.\run.cmd -Port 8080        # 默认8000；被占用时自动寻找后续空闲端口
.\run.cmd -NoBrowser        # 启动但不自动打开浏览器
.\run.cmd -SetupOnly        # 只配置依赖与构建，不启动服务
.\run.cmd -Reinstall        # 重新安装依赖并构建
```

### 常见启动问题

- **首次安装失败**：查看运行窗口的错误信息，确认能访问 Python 包索引、npm 和 Node.js 下载站点，再重新运行。失败窗口会保留提示；需要强制重装依赖时使用 `.\run.cmd -Reinstall`。
- **提示没有 Python 或 winget**：手动安装 [Python 3.11+](https://www.python.org/downloads/windows/)，然后重新打开 `run.cmd`。
- **浏览器无法打开页面**：先确认窗口已经显示“已启动”，再使用窗口中的实际地址。8000 被占用时，脚本会从后续最多19个端口中寻找空闲端口。
- **提示另一个窗口正在配置项目**：等待那个窗口配置结束，再启动，避免同时安装依赖。
- **服务启动失败或异常退出**：查看窗口提示以及项目 `.cache/launcher/` 下的 `server-*.log` 和 `server-*.error.log`。

浏览器米游社缓存按访问地址和端口保存；更换端口时需在新地址重新获取，原地址的缓存仍保留。

## 手动启动（Windows / macOS / Linux）

手动启动需先安装 Python 3.11+ 和 Node.js（可使用 22.x 的 22.12 及以上版本或 24.x，含 npm）。以下命令都从项目根目录开始执行。

### Windows PowerShell

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -e '.[web]'
cd frontend
npm ci
npm run build
cd ..
.venv\Scripts\python.exe -m uvicorn web.api:app --host 127.0.0.1 --port 8000
```

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[web]'
cd frontend
npm ci
npm run build
cd ..
.venv/bin/python -m uvicorn web.api:app --host 127.0.0.1 --port 8000
```

看到服务启动成功后，在浏览器打开 [http://127.0.0.1:8000](http://127.0.0.1:8000)。手动启动不会自动打开浏览器，也不会自动更换端口；端口被占用时修改命令中的 `--port`，并打开对应地址。终端需保持运行，按 `Ctrl+C` 停止服务。修改前端代码后需重新执行 `npm run build`，修改后端代码后需重新启动服务。

前端开发与热更新方式见 [frontend/README.md](frontend/README.md)。

## 米游社角色获取

打开 `http://127.0.0.1:8000`，展开左侧“从米游社加载我的角色”。默认选择“扫码登录”，点击“生成登录二维码”，使用本人**米游社 App** 扫描并在手机上确认登录。页面显示未扫描、已扫描待确认、登录成功、过期或取消状态；确认后自动读取并填写国服绝区零游戏 UID，多账号时可选择。没有自动读到 UID 时可手动填写，再点击“获取并保存角色”。生成二维码本身不会登录账号，确认登录需由使用者在米游社 App 完成。

“手动 Cookie”入口继续保留：切换后输入**国服绝区零游戏 UID** 和本人米游社登录 Cookie，点击“获取并保存角色”。UID 不是米游社账号 ID；完整装备需要已登录账号的战绩权限。Cookie 可在本人浏览器登录米游社、打开绝区零战绩后，从开发者工具 Network 中该战绩请求的 Request Headers 复制 `Cookie` 内容；不要把 Cookie 发到聊天或提交到仓库。

二维码本地有效期最多三分钟（遵循官方返回的更短期限）；扫码确认后，本次登录最多十分钟。扫码 Cookie 只在本次服务器进程内存中暂存，浏览器只持有随机会话标识，Cookie 不下发到浏览器或写入文件。点击“退出登录”、切换到手动 Cookie、刷新/离开页面时清理本次扫码会话；即使关闭页面时取消请求未能送达，后端也会在期限到达后清除凭据。刷新页面或重启服务需要重新扫码。角色资料缓存仍可独立加载。

获取到的角色、影画、技能、潜能、实际音擎和驱动盘按 UID 保存在当前浏览器，最多保留最近五个账号。刷新页面后可从“已保存账号”直接加载，不需要再次请求米游社；“加载到当前槽位”替换当前操作角色，角色已在队伍中时选中并更新该角色。原有从零配置和 JSON 导入、导出仍可使用。手动 Cookie 输入框在请求开始时清空，Cookie 不写入本地缓存、服务器文件或返回资料。清除本地资料后需要重新获取。

点击队伍中的角色槽位即可设为主控，拖动仍可交换位置。角色库按角色 ID 降序排列，可按职业、属性和阵营组合筛选。每名角色的装备配置可独立折叠；折叠后保留等级、影画、音擎名称、精炼及驱动盘有效词条数量。

v2 的有效词条默认读取米游社有效副属性方案；可自行勾选并保存到当前浏览器，角色配置 JSON 同时保存该选择。当前总数按驱动盘副词条的初始出现及强化次数统计，不包含主词条、套装或音擎。攻击、生命、防御的固定数值副词条以小字 `+N` 附在对应百分比词条后；非命破角色的穿透值单独显示为小词条，均不计入总数。米游社获取时的官方汇总数量保留作对照；旧缓存没有有效副属性方案时需重新获取，缺少方案时页面会注明采用可修改的职业预设。

计算时同步对每名队员逐项尝试增加一条 S 级副词条，重新执行现有角色、音擎、驱动盘、队友与派生事件计算，展示不暴击、期望、满暴击三种模式的变化。固定攻击、生命、防御以及非命破角色的穿透值也参与比较；比较不会改变真实装备、不受某个盘已满 9 次的限制。零基准和不完整结算不显示推断的百分比增益，配置变化后需重新计算。

敌人选择使用已保存的 [Nanoka 正式版怪物数据](https://zzz.nanoka.cc/monster/)，默认“卫士Ⅱ型”，可搜索并选择具体怪物变体；切换目标读取其真实抗性和失衡倍率，防御默认按等级成长曲线更新，可手动修改或恢复默认。源数据没有怪物属性的条目不进入可选列表；源未提供流明抗性时，计算流明伤害前需填写或确认手动值。数据版本、缺失项和更新方法见 [v2 接入说明](docs/v2-feature-notes.md)。

缺失立绘使用已打包的官方角色图片，下载来源见 [角色图片来源记录](frontend/public/characters/sources.json)。敌人区域的“计算模式”可切换危局强袭战与式舆防卫战，按正式期数、难度/防线、房间、目标和场地增益计算；触发状态与层数需明确选择。危局生命档位独立于敌人战斗等级。场地使用与普通角色相同的计算管线及词条收益比较，支持场景文件导入/导出。执行方案已通过审阅，见 [Endgame 执行方案](docs/v2-endgame-plan.md)；未决条款见 [v2 接入说明](docs/v2-feature-notes.md)。

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
