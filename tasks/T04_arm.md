# T04 桌面机械臂

## 拥有的文件

`assets/build/build_arm.py`、`assets/build/arm_motion.py`、`assets/build/arm_demo.py`、`assets/arm.blend`、`tasks/reports/T04.md`、`tasks/reports/validation/arm/`

## 先读

`docs/01_show_bible.md`（机械臂一节）、`docs/02_conventions.md`、`docs/04_rig_interface.md`（机械臂一节）、`docs/03_room_layout.md`（工作台、落点、取件点坐标）、`contracts/arm.json`。

## 背景

项目里有一份外部机械臂资产（7 轴 + 五指灵巧手，约 244 万三角面，透明外壳展示内部电路）。评估结论是**不复用**：太重、风格不符、五指手不适合批量化抓取。只借用它的比例：大臂约 0.24 米、小臂约 0.19 米。本任务从零做一个复古简化版。

## 造型规格（米，底座底面在 z = 0，默认朝向 -Y）

| 部件 | 对象名 | 规格 | 材质 |
| --- | --- | --- | --- |
| 底座 | ARM_Base | 直径 0.18、高 0.05 的圆盘 + 黄铜装饰环 | MAT_OrangePaint、MAT_Brass |
| 转台 | ARM_Turret | 直径 0.13、高 0.08，随 base_yaw 转 | MAT_OrangePaint |
| 肩关节 | ARM_Shoulder | 横置圆柱关节，中心 z ≈ 0.14 | MAT_Brass |
| 大臂 | ARM_Upper | 长 0.25，圆角截面 0.06 × 0.05 | MAT_OrangePaint |
| 肘关节 | ARM_Elbow | 横置圆柱 | MAT_Brass |
| 小臂 | ARM_Fore | 长 0.20，略细 | MAT_OrangePaint |
| 手腕 | ARM_Wrist | 腕俯仰 + 腕旋转两段，共长约 0.06 | MAT_Brass、MAT_OrangePaint |
| 夹爪座 + 两指 | ARM_Gripper、ARM_Finger_L / R | 平行两指，指长 0.06，最大张开 0.10，指尖有橡胶垫 | MAT_OrangePaint、MAT_Rubber |

圆润的中古风外形，倒角要大；不要做成冷硬的工业风。夹爪朝下时最大水平臂展约 0.45 米（大臂 + 小臂）；房间里所有抓放点都在底座 0.40 米以内（落点 0.30–0.39 米，取件点 0.38 米），不要在完全伸直的位置工作。

## 骨架

`ARM_Rig`，骨骼：`base_yaw`（只绕 Z）→ `shoulder` → `elbow` → `wrist_pitch` → `wrist_roll` → `finger_L`、`finger_R`、`grip_socket`；另外 `ik_target`、`ik_pole` 是不在链上的控制骨骼。

- **`ik_target` 的含义：`grip_socket` 期望到达的位置。** 管线只移动 `ik_target`，然后检查 `grip_socket` 是否到位。
- 实现方式自选，推荐：`base_yaw` 用"阻尼追踪 / 锁定追踪"朝向 `ik_target` 的水平方向；IK 加在 `elbow` 上（链长 2：shoulder + elbow），目标是一根位于 `ik_target` 正上方固定距离（腕部 + 夹爪长度）的辅助骨骼 `wrist_target`；`wrist_pitch` 用约束保持夹爪竖直朝下。
- 静止姿态（rest pose）就是收起的 `ARM_home` 姿态，不要水平伸直（否则包围盒超出契约）。
- `grip` 属性驱动两根手指沿局部 X 轴对向移动（0 → 张开 0.10，1 → 合拢）。
- `grip_socket` 在两指中间、指尖往上 2 厘米处。

动作 `ARM_home`：收起待机姿态（夹爪在底座前上方约 0.25 米处）。`ARM_idle`：90 帧循环，幅度 1–2 毫米和 0.5° 以内的伺服微动，`servo_jitter` 缩放幅度。

## 运行时函数（arm_motion.py）

```python
def pick_place(rig, prop, grab_empty, src, dst, t_land, fps=30, grip_close=None):
    """rig: ARM_Rig（可以有任意世界变换，例如舞台里在 MARK_Arm_Base、绕 Z 转了 -90°）；
    prop: 道具根对象，或道具的集合实例空对象（instance_type == 'COLLECTION'）。是实例时，
          抓取点位置 = prop.matrix_world @ (grab 在集合里的位置 − instance_collection.instance_offset)，
          grip_width 从实例集合里的根对象 PROP_<id> 读取；
    grab_empty: 道具的抓取点对象（prop 是实例时传 None，由函数自己从集合里找 PROP_<id>_grab）；
    src / dst: 世界坐标 (x, y, z)，道具底部所在位置；t_land: 道具在 dst 落稳的帧号。
    返回 (第一帧, 最后一帧)。"""
```

分段（从 t_land 倒推）：待机 → 移到 src 上方 0.12 米 → 下降 → 夹紧（6 帧，grip 0→目标值，目标值由道具 `grip_width` 换算）→ 抬起 0.12 米 → 走弧线到 dst 上方 → 下降，**t_land 这一帧落到 dst** → 松开（6 帧）→ 抬起 → 回待机。移动时长按距离算（约 0.6 米/秒，单段至少 10 帧），全部用缓入缓出。

道具跟随的推荐做法是**逐帧烘焙**：在抓住到松开之间，逐帧 `scene.frame_set(f)`，读 `grip_socket` 的世界矩阵，乘上抓住那一刻记录下的相对矩阵，给道具的位置和旋转打关键帧。这样没有约束跳变，结果确定。松开后道具保持在 dst 不动。

## 演示（arm_demo.py）

新建场景，按舞台里的真实情况摆放：机械臂根放在 (2.30, -0.95, 0.90)、绕 Z 转 -90°（和 MARK_Arm_Base 一致）。测试道具做成**集合实例**：一个集合里放 4 厘米方块 + 抓取点（离底面 0.022 米）+ 根对象上的 `grip_width = 0.04`，再用一个集合实例空对象放进场景。道具从取件点 (2.30, -1.33, 0.90) 搬到落点 (2.00, -0.95, 0.90)，`t_land = 90`。每 2 帧渲一张 540p 到 `tasks/reports/validation/arm/pickplace/`，并在脚本末尾**断言**：

- 第 90 帧方块底部中心距 dst 小于 2 毫米；
- 全程指尖最低点不低于台面（z ≥ 0.899）；
- 第 90 帧之后方块不再移动；
- 抓住期间方块与夹爪的相对位置不变（误差小于 1 毫米）。

## 验收

```bash
bash tools/blender.sh assets/build/build_arm.py
bash tools/validate.sh assets/arm.blend contracts/arm.json
bash tools/blender.sh assets/build/arm_demo.py
```

- [ ] 验收 PASS，三角面 ≤ 20,000
- [ ] 演示断言全部通过；逐帧图里道具跟随自然，手指合拢在道具两侧，没有明显穿模
- [ ] 移动 `ik_target` 到工作半径内任意点，机械臂都能稳定到达，不翻转
