# AGENTS.md — 小波深夜电台 3D 资产建模

你是被分配到本项目的建模 Agent。本文件和它引用的文档包含完成任务所需的全部上下文，**不依赖任何之前的对话**。按下面顺序读，再开始动手。

## 1. 项目是什么

一档全 3D 制作的 AI / 科技讲解视频节目《小波深夜电台》：横屏 16:9，每期 3–5 分钟。原创的收音机头机器人"小波"在 70 年代复古科技客厅（夜晚）里当深夜电台主播；滚球宠物"滚滚"负责捣乱；桌面机械臂负责摆放道具；还有翻页挂图和复古电视。

所有资产都由 **Python 脚本在 Blender 无界面模式下生成**，后续由一条自动化管线按脚本时间轴批量出片。所以资产必须：可重跑、命名严格、接口固定。

## 2. 阅读顺序

1. 本文件（规则、环境、任务图）
2. `docs/01_show_bible.md` — 视觉与角色设定（风格、配色、角色性格）
3. `docs/02_conventions.md` — 单位、坐标、命名、材质、文件、Blender 5.2 API 注意事项
4. `docs/03_room_layout.md` — 房间尺寸、各区域坐标、机位
5. `docs/04_rig_interface.md` — 各资产必须暴露的骨骼、属性、动作（管线靠这些驱动）
6. `docs/05_render_benchmark.md` — 本机实测渲染速度与引擎选择
7. 你被分配的任务卡 `tasks/Txx_*.md`

## 3. 环境（已实测）

| 项目 | 值 |
| --- | --- |
| 机器 | macOS，Apple M5 Pro（16 核 GPU） |
| Blender | 5.2.2 LTS，路径 `/Applications/Blender.app/Contents/MacOS/Blender` |
| 渲染引擎 | Eevee（标识符 `BLENDER_EEVEE`），1080p 64 采样 + 体积雾约 1.4 秒/帧 |
| 项目根目录 | `~/Documents/personal/video-model`（下文路径都相对它） |

运行方式（**只用命令行无界面模式**，不要依赖图形界面操作）：

```bash
bash tools/blender.sh tools/selftest.py --tag T02        # 环境自测（任务 T00，tag 用你的任务号）
bash tools/blender.sh assets/build/build_xiaobo.py       # 运行一个生成脚本
bash tools/validate.sh assets/xiaobo.blend contracts/xiaobo.json   # 验收
```

`tools/blender.sh` 会自动加 `-b --factory-startup -y --python-exit-code 1`（`-y` 允许驱动器表达式运行 Python），脚本抛异常时退出码为 1。Blender 路径不同时用环境变量 `BLENDER=/path/to/Blender` 覆盖。

可选：Blender 官方 MCP（Blender Lab 出品，要求 Blender 5.1+，本机满足）可以在建模过程中交互式查看场景和截图。它不是必需的；所有交付物必须能只靠上面的命令行重新生成。官方说明它会无防护地执行模型生成的代码，使用时注意。

## 4. 硬性规则

1. **脚本是源代码，.blend 是产物。** 每个资产由 `assets/build/build_<asset>.py` 从空场景生成（先调用 `_common.reset_scene()`），重复运行结果一致。不要在图形界面里手工修改 .blend。
2. **使用公共库** `assets/build/_common.py`（材质、圆角体、属性、驱动、预览渲染、保存）。缺功能就在你自己的脚本里写辅助函数，不要改 `_common.py`；确实需要改时写进任务报告里提议。
3. **颜色只来自** `config/style.json`（色板键名或 `MAT_*` 命名材质）。资产专属材质用资产前缀命名（如 `XB_FaceGlass`）。
4. **接口不能改。** `contracts/<asset>.json` 和 `docs/04_rig_interface.md` 里列出的对象名、骨骼名、属性名、动作名必须一字不差。可以额外加东西，不能少、不能改名。
5. **确定性。** 随机数一律用固定种子（`random.Random(42)`）。
6. **原创。** 小波、滚滚、机械臂和所有道具都是本项目原创设计；不得做得像任何已知的电影、动画、游戏角色或商业产品，不得使用真实品牌 logo、文字商标。logo 位置用 `PROP_logo_tile` 的可替换贴图槽。
7. **外部资源。** 默认不下载任何东西。确需字体或模型时，只能用 CC0 或 SIL OFL 等可商用授权，文件放进 `library/`，并在 `library/LICENSES.md` 记录来源、授权、下载日期。
8. **文件归属。** 只写你的任务卡"拥有的文件"一节列出的路径（多 Agent 并行时靠这条避免冲突）。`config/`、`contracts/`、`docs/`、`tools/`、`_common.py` 对你是只读的。例外：`tasks/STATUS.md` 里只改你自己那一行；T00 自测只写带你任务号的输出（`--tag Txx`）。
9. **完成前必须看图。** 验收脚本会渲染预览图；你必须实际打开这些 PNG 检查外观（能看图的 Agent 直接看；不能看图的在报告里写明"未目检"并标为待人工确认）。

## 5. 任务图

| 任务 | 内容 | 依赖 | 可并行 | 复杂度 | 粗估 Agent 时间 |
| --- | --- | --- | --- | --- | --- |
| T00 | 环境自测 | — | 每个 Agent 开工前各自跑一次 | 低 | 5 分钟 |
| T01 | 房间、家具、灯光、机位、标记点 | T00 | 是 | 高 | 2–4 小时 |
| T02 | 小波（模型、骨骼、屏幕脸、11 个动作） | T00 | 是 | 最高 | 3–5 小时 |
| T03 | 滚滚（模型、骨骼、6 个动作） | T00 | 是 | 中 | 1.5–3 小时 |
| T04 | 桌面机械臂（模型、IK、夹爪、抓放函数） | T00 | 是 | 中高 | 2–3 小时 |
| T05 | 翻页挂图（画架、10 页、翻页、书写函数） | T00 | 是 | 中高 | 2–3 小时 |
| T06 | 复古电视（模型、屏幕材质、媒体函数） | T00 | 是 | 中 | 1–2 小时 |
| T07 | 道具库（11 个道具） | T00 | 是 | 低中 | 1–2 小时 |
| T08 | 组装舞台、七个机位定帧、整体调光 | T01–T07 全部完成 | 否 | 中 | 1–2 小时 |

时间是粗估，取决于 Agent 能力和返工次数。T01–T07 互不依赖，可以分给不同 Agent 同时做；T08 最后做。

## 6. 每个任务的工作流程

1. 在 `tasks/STATUS.md` 里把你的任务改成 `进行中`，写上 Agent 名称和开始时间。
2. 跑 T00 自测，确认环境正常。
3. 读任务卡，写 `assets/build/build_<asset>.py`（以及任务卡要求的其他脚本）。
4. 运行生成脚本 → 运行验收脚本 → 打开 `tasks/reports/validation/<asset>/` 里的预览图检查 → 修改 → 重复，直到验收 PASS 且外观符合设定。
5. 写任务报告 `tasks/reports/Txx.md`：做了什么、最终参数、三角面数、预览图路径、已知问题、对公共文件的修改建议。
6. 在 `tasks/STATUS.md` 里改成 `待审` 并写完成时间。人工审核通过后由人改成 `完成`。

## 7. 完成标准（所有任务通用）

- [ ] 生成脚本从空场景一次跑通，退出码 0
- [ ] `tools/validate.sh` 返回 PASS
- [ ] 预览图已目检，造型、比例、配色符合 `docs/01_show_bible.md`
- [ ] 任务卡里的专项验收项全部满足
- [ ] 报告已写，STATUS 已更新
