# T02 小波（主角）

## 拥有的文件

`assets/build/build_xiaobo.py`、`assets/build/xiaobo_sheet.py`、`assets/xiaobo.blend`、`tasks/reports/T02.md`、`tasks/reports/validation/xiaobo/`

## 先读

`docs/01_show_bible.md`（小波一节）、`docs/02_conventions.md`（角色统一模式、5.2 API 注意事项）、`docs/04_rig_interface.md`（小波一节）、`contracts/xiaobo.json`。

## 目标

一个原创的收音机头机器人：造型可爱、辨识度高；屏幕脸能做 8 种表情和 5 种图标；骨架和 11 个动作可以被管线直接调用。**不要做得像任何已知的电影、动画或游戏里的机器人。**

## 造型规格（米，正面朝 -Y，底部在 z = 0）

| 部件 | 对象名 | 尺寸 / 位置 | 材质 |
| --- | --- | --- | --- |
| 轮式底座 | XB_Base | 直径约 0.30、高 0.10 的扁圆台，下面 3 个小轮子 | MAT_Rubber + MAT_Brass 装饰环 |
| 躯干 | XB_Body | 0.32 × 0.26 × 0.42 圆角柱体，z 0.12–0.54 | MAT_Cream，前胸一块焦橙面板（MAT_OrangePaint） |
| 颈部 | （可选）XB_Neck | 短圆柱，z 0.54–0.60 | MAT_Brass |
| 头 | XB_Head | 横向胶囊形 0.50 × 0.28 × 0.28，中心 z ≈ 0.74 | MAT_Cream |
| 扬声器网罩（左右"耳朵"） | XB_Speaker_L / R | 头两侧的圆盘，带圆孔阵列或格栅纹理 | MAT_OrangePaint 或 MAT_Brass |
| 屏幕脸 | XB_FaceScreen | 头正面嵌入的圆角矩形，约 0.36 × 0.18 | 深色玻璃 XB_FaceGlass |
| 天线 | XB_Antenna | 头顶右侧（角色自己的右侧，即 -X 一侧）两节细杆 + 顶端小球，总长 0.15（收起）到 0.35（伸出） | MAT_Brass，顶端小球青绿发光 |
| 手臂 | XB_ArmUpper_L/R、XB_ArmLower_L/R | 两节圆柱，各长约 0.14，肩部在躯干上部两侧 | MAT_Cream + 焦橙关节 |
| 手 | XB_Hand_L / R | 连指手套形，约 0.07 | MAT_Cream |
| 面光 | XB_FaceLight | 贴在脸前 3 厘米、朝前的小面光，约 0.3 × 0.15 | 颜色由驱动器读 face_color |

总高约 0.88（不含天线）。头和身体约 1:1.5。手臂垂下时手在 z ≈ 0.25–0.30。

## 屏幕脸（推荐做法：几何体脸）

在深色玻璃面板 `XB_FaceScreen` 后面 2–3 毫米处放发光的小网格，全部绑在 `head` 骨骼上：

- **眼睛** `XB_Eye_L` / `XB_Eye_R`：圆角矩形薄片（约 0.05 × 0.07）。`eye_open` 驱动 Z 缩放（0 时压成一条线）；`look_x` / `look_y` 驱动位置偏移（最大约 ±0.03）。
- **表情**：给眼睛做形态键（笑眼弧线、一大一小、半闭一字、瞪大），由驱动器根据 `face_expr` 选择对应形态键的值。表达式写成简单表达式，例如 `1.0 if abs(v - 1) < 0.5 else 0.0`（不要用 `int()` 等需要 Python 的写法）。
- **嘴** `XB_Mouth`：一条细横线，`mouth_open` 驱动 Z 缩放（从一条线变成扁圆角矩形）。
- **图标** `XB_Icon_Question` / `_Exclamation` / `_Bulb` / `_Heart` / `_Loading`：用曲线或网格做的简单发光图形。显示方式用驱动器控制缩放（`icon_id` 等于自己的编号时缩放为 1，否则为 0）；有图标时眼睛缩放为 0。
- **发光颜色**：所有脸部发光件共用材质 `XB_FaceEmit`，其发光颜色的 3 个分量由驱动器读 `face_color[0..2]`；`XB_FaceLight` 的颜色同样由驱动器读取。
- **扫描线**：在玻璃面板材质上叠一层沿 Z 方向的细条纹（波浪纹理），强度由 `scanline` 驱动。
- **开关机**：`screen_on` 驱动整个脸部组的 Z 缩放（0 时是一条横线）和发光强度。

也可以用纯着色器（距离场）实现，只要属性接口和效果一致即可。

## 骨架

`XB_Rig`，骨骼名和轴向约定见 `docs/04_rig_interface.md`。**静止姿态：双臂自然下垂**（不要 T 字形）。零件用 `_common.parent_to_bone()` 绑到骨骼上。手臂 IK：在 `arm_lower.L/R` 上加 IK 约束，目标 `ik_hand.L/R`，链长 2。天线：`antenna_ext` 驱动 `antenna_tip` 沿骨骼方向的位移（或缩放）。

所有自定义属性用 `_common.add_prop()` 加在 `XB_Rig` 上，默认值：face_expr 0、icon_id 0、eye_open 1、mouth_open 0、look_x 0、look_y 0、screen_on 1、scanline 0.3、antenna_ext 0.5、face_color = 色板 teal 的线性 RGB。

## 动作

11 个动作，名字和时长参考见 `docs/04_rig_interface.md`。要求：

- 只给 `XB_Rig` 打关键帧（骨骼变换和需要的自定义属性）。
- 除循环动作外，首帧和末帧回到静止姿态。
- 动作要有弹性和惯性（缓入缓出、轻微过冲），不要机械地匀速移动。
- 每个动作 `use_fake_user = True`，最后让 `XB_Rig` 的当前动作为 `XB_idle`，`frame_set(1)` 后再保存。
- 指向类动作假设小波站在 `MARK_Host` 面朝 -Y：挂图在左侧偏后（-X），电视在右后方（+X、+Y），工作台在右前方（+X、-Y）。

## 表情与动作检查图（xiaobo_sheet.py）

写一个脚本，打开 `assets/xiaobo.blend`，用正面近景相机渲染：

- 8 张表情图（face_expr 0–7，face_color 按 `style.json → face.expressions` 取色）→ `tasks/reports/validation/xiaobo/expr_<id>.png`
- 5 张图标图（icon_id 1–5）→ `icon_<id>.png`
- 每个动作的首帧、中间帧、末帧三张 → `action_<name>_<frame>.png`

运行：`bash tools/blender.sh assets/build/xiaobo_sheet.py`

## 验收

```bash
bash tools/blender.sh assets/build/build_xiaobo.py
bash tools/validate.sh assets/xiaobo.blend contracts/xiaobo.json
bash tools/blender.sh assets/build/xiaobo_sheet.py
```

- [ ] 验收 PASS，三角面 ≤ 60,000
- [ ] 四视图预览：比例 Q 版，头部轮廓一眼能认出（胶囊头 + 两侧网罩 + 单根天线）
- [ ] 8 张表情图各不相同且一眼能读懂情绪；5 张图标图清晰
- [ ] 改 `mouth_open`、`eye_open`、`look_x` 时脸部确实变化（报告里附对比图）
- [ ] 动作三帧图里姿态合理，没有穿模、没有零件脱离骨骼
- [ ] 屏幕脸是整个角色最亮的部分，面光让胸前和桌面有一点青绿反光
