# 参考素材

这里的内容只作参考，不在建模流程里直接使用。

## k31_arm_app/

K3.1 机械臂网页项目（Three.js），原位于 `~/Desktop/K3.1素材/K3.1Pro素材/K3.1前端网页产物/app`。

- 内容：7 轴机械臂 + 20 个自由度的五指灵巧手，透明外壳展示内部电路和走线；带姿态库、爆炸图、逐帧精确渲染（`render-film.html`）和 GLB 导出。
- 运行：`node references/k31_arm_app/server.mjs`，然后在浏览器打开 http://127.0.0.1:8807/
- 实测：约 244 万三角面、3830 个网格、34 种材质。
- 结论：**不直接复用**。原因是太重、风格与复古客厅不符，五指手也不适合批量化抓取。新机械臂按 `tasks/T04_arm.md` 重做，只借用这里的比例（大臂 0.244 m、小臂 0.191 m）、关节限位（`src/params.js`）、姿态库思路（`src/pose.js`）和逐帧渲染思路。完整评估见 `docs/00_技术方案.md`。
- `vendor/` 下是 three.js 及其扩展，MIT 许可，见 `vendor/THREE-LICENSE.txt`。
