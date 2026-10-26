# 04 绑定与动画接口

后续的自动化管线只通过这里列出的名字驱动资产。

## 骨骼轴向约定（所有骨架通用）

- `root` 骨骼：头 (0, 0, 0)，尾 (0, 0.25, 0)，roll 0。管线移动 `root` 的位置、绕 Z 旋转它来转向。
- 角色面朝 -Y；`.L` 在 +X 一侧（角色自己的左边），`.R` 在 -X 一侧。
- 滚滚 `shell` 骨骼：头 (0, 0, 0.15)（球心），尾 (0, 0.15, 0.15)（沿 +Y），roll 0。向前（-Y）滚动 = 绕 X 轴正向旋转。
- 机械臂 `base_yaw`：头 (0, 0, 0)，尾 (0, 0, 0.08)（沿 +Z），绕自身 Y 轴（即世界 Z）转动。机器可读版本在 `contracts/<asset>.json`，验收脚本按它检查。可以额外增加对象、骨骼、属性，**不能少，不能改名**。

## 小波 XB（`assets/xiaobo.blend`）

**骨架 `XB_Rig`（根，位于原点）的骨骼**

| 骨骼 | 作用 |
| --- | --- |
| root | 整体移动和转向（滑行） |
| body | 躯干前后左右微倾 |
| head | 头部转动、点头 |
| antenna_base / antenna_tip | 天线两节；`antenna_ext` 驱动伸缩 |
| arm_upper.L / arm_lower.L / hand.L | 左臂 |
| arm_upper.R / arm_lower.R / hand.R | 右臂 |
| ik_hand.L / ik_hand.R | 手臂 IK 目标（IK 约束加在 arm_lower 上，链长 2） |

**`XB_Rig` 上的自定义属性**

| 属性 | 范围 | 含义 |
| --- | --- | --- |
| face_expr | 0–7 整数 | 表情编号（见设定文档） |
| icon_id | 0–5 整数 | 图标编号，0 = 不显示图标；非 0 时图标替换眼睛 |
| eye_open | 0–1 | 0 闭眼，1 正常睁眼（用来眨眼） |
| mouth_open | 0–1 | 嘴的张开程度，管线逐帧写入 |
| look_x / look_y | -1–1 | 眼睛在屏幕上的偏移（看左右、上下） |
| screen_on | 0–1 | 屏幕开关；0→1 播放"从一条横线展开"的开机效果 |
| scanline | 0–1 | 扫描线强度 |
| antenna_ext | 0–1 | 天线伸出程度（1 = 竖起） |
| face_color | RGB 颜色 | 屏幕发光颜色；管线按 `face_expr` 从色板取色写入 |

**必须有的对象**：`XB_Head`、`XB_FaceScreen`、`XB_Body`、`XB_Base`、`XB_Antenna`、`XB_Hand_L`、`XB_Hand_R`、`XB_FaceLight`（贴着脸的小面光，颜色由驱动器读 `face_color`）。

**动作**（都只作用于 `XB_Rig`，首尾帧回到静止姿态，方便拼接）

| 动作 | 时长参考 | 说明 |
| --- | --- | --- |
| XB_idle | 90 帧，循环 | 呼吸感的轻微起伏、头部微动 |
| XB_talk_A / XB_talk_B | 各 60–90 帧 | 两套讲解手势 |
| XB_point_flipchart | 约 45 帧 | 站在 MARK_Host 时指向左侧挂图 |
| XB_point_tv | 约 45 帧 | 指向右后方电视 |
| XB_point_bench | 约 45 帧 | 指向右前方工作台 |
| XB_wave | 约 60 帧 | 挥手（开场 / 结尾） |
| XB_nod | 约 30 帧 | 点头 |
| XB_shake | 约 40 帧 | 无奈摇头 |
| XB_look_pet | 约 50 帧 | 低头看向左前方的滚滚 |
| XB_flip_page | 约 40 帧 | 站在 MARK_Flipchart_Stand 时抬手翻页 |

## 滚滚 GG（`assets/gungun.blend`）

**骨架 `GG_Rig` 的骨骼**：`root`（移动和朝向）、`shell`（只有外壳绕它滚动）、`upright`（屏幕和天线挂在它上面，不随外壳滚，可前后倾、弹跳）、`antenna_1`、`antenna_2`（天线两节，用于摆动）。

**`GG_Rig` 上的自定义属性**

| 属性 | 范围 | 含义 |
| --- | --- | --- |
| face_expr | 0–3 整数 | 0 普通、1 开心、2 困、3 害怕 |
| eye_open | 0–1 | 眨眼 |
| look_x / look_y | -1–1 | 眼睛偏移 |
| squash | -1–1 | 正值压扁（落地），负值拉长（起跳）；体积大致守恒 |
| antenna_glow | 0–1 | 天线顶端小球的亮度 |

**必须有的对象**：`GG_Shell`、`GG_Screen`、`GG_Antenna`。

**动作**：`GG_idle`（循环，轻微呼吸和天线晃动）、`GG_bounce2`（原地弹跳两下）、`GG_spin`（快速原地转圈）、`GG_sleep`（闭眼、天线耷拉，循环）、`GG_curious`（前倾、歪头、眼睛看上方）、`GG_scared`（后缩、眼睛变小、轻微颤抖）。
滚动移动不做成动作：管线沿路径移动 `root`，并按"转角 = 距离 ÷ 半径"转动 `shell`。

## 机械臂 ARM（`assets/arm.blend`）

**骨架 `ARM_Rig` 的骨骼**：`base_yaw`、`shoulder`、`elbow`、`wrist_pitch`、`wrist_roll`、`finger_L`、`finger_R`、`grip_socket`（两指之间的抓取点，道具挂在这里）、`ik_target`（夹爪目标位置，移动它整条臂跟随）、`ik_pole`（肘部朝向）。

**`ARM_Rig` 上的自定义属性**：`grip`（0 张开到 1 合拢，驱动两根手指）、`servo_jitter`（0–1，待机微动幅度）。

**动作**：`ARM_home`（静止待机姿态，单帧即可）、`ARM_idle`（循环的伺服微动）。

**运行时函数**（T04 交付，`assets/build/arm_motion.py`）：

```python
pick_place(rig, prop, grab_empty, src, dst, t_land, fps=30, grip_close=None) -> (start_frame, end_frame)
```

从 `src` 取起道具，放到 `dst`，保证道具在 `t_land` 那一帧刚好落下。`rig` 可以有任意世界变换（舞台里它在 MARK_Arm_Base，绕 Z 转了 -90°）；`prop` 可以是道具根对象，也可以是道具的集合实例空对象（这时抓取点和 `grip_width` 从 `prop.instance_collection` 里读取，并按 `instance_offset` 换算）。实现方式见 T04 任务卡。

## 翻页挂图 FC（`assets/flipchart.blend`）

- `FC_Root`（空对象，原点）、`FC_Easel`、`FC_Board`、`FC_MarkerCup`。
- 10 页纸 `FC_Page_00` … `FC_Page_09`，00 在最上面。每页有自定义属性 `flip`（0 = 平放在画板上，1 = 翻到画架背后），旋转轴是纸的上沿。
- 每页一个子空对象 `FC_Page_NN_Content`，位于该页左上角，局部 +X 向右、-Z 向下（纸面内坐标，单位米）。书写内容都挂在它下面，随纸一起翻。页与页间隔 2 毫米，内容离自己的纸面 0.5 毫米（不会穿到上一页）。
- **运行时函数**（T05 交付，`assets/build/flipchart_draw.py`）：`write_text`、`draw_path`、`draw_shape`、`flip_page`，签名见 T05 任务卡。

## 复古电视 TV（`assets/tv.blend`）

- `TV_Root`（空对象，原点）、`TV_Body`、`TV_Screen`（UV 0–1 铺满 4:3 屏幕）、`TV_PushTarget`（推进转场时相机的终点：从这里看出去，屏幕刚好铺满 16:9 画面）。
- 屏幕材质 `TV_ScreenMat` 里有一个名为 `TV_Media` 的图像纹理节点，管线往里面放图片或视频。
- `TV_Root` 上的自定义属性：`screen_on`（0–1）、`scanline`（0–1）、`glow`（0–2）。
- **运行时函数**（T06 交付，`assets/build/tv_media.py`）：`set_media(path, frame_start=1, kind="movie"|"image"|"sequence", material=None)`。`material` 为空时用 `bpy.data.materials["TV_ScreenMat"]`；在舞台里材质是链接进来的，调用方先把它本地化再传进来。

## 道具 PROPS（`assets/props.blend`）

- 每个道具一个子集合 `PROP_<id>`，根空对象 `PROP_<id>`，其下的几何体落在根对象的局部 z = 0 上。
- 每个道具有抓取点空对象 `PROP_<id>_grab`（机械臂的 `grip_socket` 对准它；`grip_socket` 在指尖上方 2 厘米，所以抓取点离道具底面至少 0.022 米，扁平道具也一样，否则指尖会插进桌面），根对象上有自定义属性 `grip_width`（夹爪需要张开的宽度，米）。
- 子集合的 `instance_offset` 设为根对象的位置，这样以集合实例的方式放进场景时，道具会出现在实例原点。
- `PROP_logo_tile` 的材质 `PROP_LogoMat` 里有图像纹理节点 `PROP_Logo_Image`，每期换图。

## 房间 ROOM_SET（`assets/room.blend`）

子集合：`ROOM_ARCH`（墙地窗）、`ROOM_FURNITURE`、`ROOM_DRESSING`（陈设）、`LIGHTS`、`CAMS`、`MARKS`、`PROXIES`。相机、灯光、标记点的名字见 `docs/03_room_layout.md`。
