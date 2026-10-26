# T03 滚滚（滚球宠物）

## 拥有的文件

`assets/build/build_gungun.py`、`assets/build/gungun_motion.py`、`assets/build/gungun_sheet.py`、`assets/gungun.blend`、`tasks/reports/T03.md`、`tasks/reports/validation/gungun/`

## 先读

`docs/01_show_bible.md`（滚滚一节）、`docs/02_conventions.md`、`docs/04_rig_interface.md`（滚滚一节）、`contracts/gungun.json`。

## 目标

一个原创的圆球宠物：好动、可爱、靠滚动和弹跳表达情绪；外壳会滚，屏幕和天线始终朝上朝前。**不要做得像任何已知的动画或游戏角色。**

## 造型规格（米，底部在 z = 0）

| 部件 | 对象名 | 规格 | 材质 |
| --- | --- | --- | --- |
| 外壳 | GG_Shell | 直径 0.30 的球，两条凹陷的分型线，中间一圈奶油色分色带 | GG 专属芥末黄（用 MAT_Mustard）+ MAT_Cream |
| 屏幕 | GG_Screen | 正面略外凸的圆角小屏 0.12 × 0.07，中心约 z 0.17 | 深色玻璃 GG_ScreenGlass |
| 眼睛 | GG_Eye_L / R | 两个发光小圆点（直径约 0.018），在屏幕后 2 毫米 | GG_EyeEmit（teal） |
| 天线 | GG_Antenna | 从顶部伸出的细杆，长约 0.12，两节；顶端小球 GG_AntennaTip 直径 0.025 | MAT_Brass；小球 teal 发光 |

**关键结构**：外壳和分型线挂在 `shell` 骨骼上；屏幕、眼睛、天线挂在 `upright` 骨骼上（`upright` 是 `root` 的子骨骼，不是 `shell` 的子骨骼）。屏幕看起来"嵌在"球里，但它是独立部件，球滚动时屏幕保持朝前。屏幕外缘加一圈薄薄的芥末黄边框，挂在 `upright` 上，能遮住屏幕和外壳之间的缝隙。

## 骨架与属性

`GG_Rig`（骨骼轴向见 `docs/04_rig_interface.md`；`shell` 的头在球心 (0, 0, 0.15)），骨骼 `root` → `shell`、`root` → `upright` → `antenna_1` → `antenna_2`。属性和默认值：face_expr 0、eye_open 1、look_x 0、look_y 0、squash 0、antenna_glow 0.7。

- `squash` 驱动 `root` 下一层的缩放：Z 缩放 = 1 − 0.25 × squash，X/Y 缩放 = 1 + 0.12 × squash（保持底部贴地）。
- `face_expr` 通过眼睛的形态键或缩放驱动：1 开心（眼睛变成向上的弧线 ^^）、2 困（一字线）、3 害怕（眼睛缩小）。
- `antenna_glow` 驱动天线小球的发光强度。

## 动作

`GG_idle`（90 帧循环）、`GG_bounce2`（约 36 帧）、`GG_spin`（约 30 帧，绕 Z 转一圈半再回正）、`GG_sleep`（120 帧循环）、`GG_curious`（约 45 帧）、`GG_scared`（约 40 帧）。弹跳要有挤压和拉伸（用 `squash` 属性），落地有一点回弹；天线有滞后的摆动。只给 `GG_Rig` 打关键帧。

## 运行时函数（gungun_motion.py）

```python
def roll_along(rig, points, frame_start, speed=0.6, fps=30):
    """沿折线 points [(x, y), ...]（世界坐标 XY，地面 z = rig 当前高度）滚动。移动 root，按距离 / 半径转动 shell（绕与运动方向垂直的水平轴），
    root 朝向运动方向（upright 跟着转）。返回结束帧。转角必须由路程精确算出，不能打滑。"""

def antenna_follow(rig, frame_start, frame_end, stiffness=0.6, damping=0.25):
    """按 root 的加速度给 antenna_1 / antenna_2 烘焙一个衰减摆动（逐帧计算后打关键帧）。"""
```

写一个演示 `gungun_sheet.py`：渲染 4 张表情图、6 个动作各 3 帧，再做一段滚动演示（从 (-0.5, -0.5) 滚到 (0.5, -0.2) 再滚回来），每 3 帧渲一张到 `tasks/reports/validation/gungun/roll/`。

## 验收

```bash
bash tools/blender.sh assets/build/build_gungun.py
bash tools/validate.sh assets/gungun.blend contracts/gungun.json
bash tools/blender.sh assets/build/gungun_sheet.py
```

- [ ] 验收 PASS，三角面 ≤ 20,000
- [ ] 滚动演示里外壳分型线在转、屏幕始终朝运动方向且保持正立、球不打滑（分型线转过的弧长 ≈ 移动距离）
- [ ] 4 张表情图可以区分
- [ ] 弹跳有挤压拉伸，落地时底部不穿进地面
