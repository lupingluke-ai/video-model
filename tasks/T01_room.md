# T01 房间、家具、灯光、机位

## 拥有的文件

`assets/build/build_room.py`、`assets/room.blend`、`tasks/reports/T01.md`、`tasks/reports/validation/room/`

## 先读

`docs/01_show_bible.md`（风格、配色）、`docs/03_room_layout.md`（**全部坐标以它为准**）、`config/style.json`（`lighting_initial`、`materials`）。

## 目标

一个可以独立调光、独立构图的夜晚复古客厅，包含 7 个机位、7 盏命名灯光、13 个标记点和角色代理体。后续所有镜头都在这个房间里拍。

## 规格

**集合结构**：顶层 `ROOM_SET`，子集合 `ROOM_ARCH`、`ROOM_FURNITURE`、`ROOM_DRESSING`、`LIGHTS`、`CAMS`、`MARKS`、`PROXIES`。

**建筑（ROOM_ARCH）**：地板（顶面 z = 0，深胡桃木，可加很淡的木纹）、后墙（深橄榄绿）、左右墙（胡桃木护墙板或橄榄绿）、天花板、右墙上的窗（窗框 + 玻璃或开口）、窗外城市夜景背板（程序化：深蓝渐变 + 用噪波 / Voronoi 纹理生成的零星暖黄窗点，自发光，放在 x ≈ 4.0，靠景深虚化）。

**家具（ROOM_FURNITURE）**：主讲矮桌、焦橙沙发、电视柜、唱片柜、工作台（含洞洞板）、球形落地灯、熔岩灯、长毛地毯。尺寸和位置见布局文档。全部用 `_common.rounded_box` / `cylinder` / `sphere` 组合，圆润的中古风造型。

**陈设（ROOM_DRESSING）**：木格栅墙（阵列修改器）、青绿霓虹标识（原创电波弧线图形，用曲线加倒角做成发光管，无文字）、黑胶唱机和几张唱片、书架上的书、龟背竹盆栽（叶片可以用简单的平面加圆角轮廓）、洞洞板上的几件工具、窗边一两样小物。数量适中，主讲背景不要太花。

**材质命名**：房间里所有材质要么是 `MAT_*`（来自 style.json），要么以 `ROOM_` 开头（如 `ROOM_ProxyGrey`、`ROOM_LampGlow`、`ROOM_CityNight`），否则验收不过。

**灯光（LIGHTS）**：按 `style.json → lighting_initial` 创建 7 盏灯，名字必须一致：`LGT_Key`、`LGT_Fill`、`LGT_Moon`、`LGT_FloorGlobe`、`LGT_BenchLamp`、`LGT_ShelfStrip`、`LGT_LavaGlow`。可以调参数，最终值写进报告。实用光对应的灯具网格（灯球、灯罩）用发光材质。世界背景接近黑色，略带蓝。

**机位（CAMS）**：按布局文档创建 7 台相机，开景深，对焦到"看向"点（建议用一个空对象作为对焦目标，命名 `FOCUS_<相机名>`）。

**标记点（MARKS）**：按布局文档创建 13 个空对象，位置和 `rotation_euler`（表里是角度，脚本里换成弧度）完全一致。

**代理体（PROXIES）**：在对应标记点放灰色代理体：`PROXY_XB`（0.5 × 0.3 × 0.9，正面贴一块青绿发光矩形当屏幕脸）、`PROXY_GG`（直径 0.3 的球）、`PROXY_ARM`（0.15 × 0.15 × 0.5）、`PROXY_FC`（0.75 × 0.5 × 1.75）、`PROXY_TV`（0.56 × 0.42 × 0.46，正面一块发光屏幕）。代理体只用来调光和构图，T08 会隐藏它们。

**渲染设置**：`_common.setup_render(scene)`；体积雾用一个铺满房间、密度很低（0.01–0.03）的体积立方体，命名 `ROOM_Fog`，可以关掉。

## 步骤建议

1. 先只做建筑、家具代理体和 7 个机位，渲染 7 张预览，确认构图。
2. 加灯光，重点调主讲机位（CAM_Host）：冷暖对比明确，代理屏幕脸是画面最亮处，背景比主体暗一档，无死黑无过曝。
3. 补齐陈设和材质细节，再整体渲染一遍。
4. 用最终设置（1080p、64 采样）分别渲染 CAM_Wide 和 CAM_Host 各一帧，记录每帧耗时写进报告。

## 验收

```bash
bash tools/blender.sh assets/build/build_room.py
bash tools/validate.sh assets/room.blend contracts/room.json
```

验收脚本会给 7 台相机各渲一张预览，放在 `tasks/reports/validation/room/`。专项检查：

- [ ] 7 张机位图构图都对：主体在画面内、没有拍到房间外面；除 CAM_Wide 顶部可见少量天花板外，其他机位看不到天花板
- [ ] CAM_Host 里代理屏幕脸是最亮的区域，暖色实用光和冷色窗光同时可见
- [ ] 窗外夜景是虚化的暖色窗点，不抢主体
- [ ] 整体色调符合 60 / 30 / 10 的配色比例，没有糊成一片棕色
- [ ] 报告里有最终灯光参数表和两张 1080p 单帧的渲染耗时
