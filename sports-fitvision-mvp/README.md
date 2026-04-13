# FitVision MVP

基于 YOLOv8-Pose + OpenCV 的实时二头肌弯举质量评估 Demo。

核心目标不是“只计数”，而是把动作拆解为可解释的技术链路：
姿态检测 -> 运动学特征 -> 状态机分段 -> 规则评分 -> 可视化反馈 -> 报告沉淀。

## 技术架构总览

### 分层架构

1. 视觉层（Vision）
- 输入摄像头或视频流。
- 使用 YOLOv8-Pose 产出 17 点关键点与置信度。
- 通过跳帧推理 + 关键点缓存降低 CPU 延迟。

2. 运动学层（Kinematics）
- 将关键点映射为肩/肘/腕关节对象。
- 计算肘角、大臂水平偏移、腕部稳定性等特征。

3. 时序引擎层（Engine）
- 状态机负责动作阶段划分与 reps 计数。
- 规则评估器负责扣分、有效性判定与反馈生成。

4. 表达层（UI + Reporting）
- UI 实时渲染骨架、状态、角度、分数、FPS、警告。
- Reporting 生成 JSON/TXT 训练报告。

### 端到端数据流

```text
Camera/Video Frame
  -> PoseDetector.detect()
  -> FrameProcessor.smooth_keypoints()
  -> JointManager.extract()
  -> AngleCalculator (角度/偏移/稳定性)
  -> BicepCurlStateMachine.update()
  -> RuleEvaluator.evaluate_rep()
  -> PoseRenderer.draw_hud()
  -> ReportGenerator.generate/save()
```

## 核心算法设计

### 1) 状态机：动作分段与 reps 计数

状态循环：

```text
IDLE -> PREPARATION -> ECCENTRIC -> BOTTOM -> CONCENTRIC -> TOP -> PREPARATION
```

- `rep_count` 在一次完整循环闭环时增加。
- 当前实现中，单次评估只在“状态刚切回 PREPARATION”时触发，避免重复评估导致 `valid > reps`。
- 已支持“左臂/右臂任意一侧完整可见即可参与评估”（右臂优先，右臂缺失时自动切左臂）。

### 2) 规则引擎：质量评分与有效性

每次动作从 100 分起，根据规则扣分：

| 规则 | 典型阈值 | 扣分 |
|---|---|---|
| speed_too_fast | 离心帧数 < `eccentric_min_frames` | 15 |
| arm_deviation | 偏移 > `arm_deviation` | 10 |
| wrist_movement | 波动 > `wrist_stability` | 8 |
| incomplete_range | 最小肘角 > `elbow_flexion` | 20 |
| uncontrolled_descent | 离心帧数 > `eccentric_max_frames` | 15 |

- `is_valid = score >= validity.min_score`（默认 70）。
- `reps` 是总完成次数，`valid` 是达标次数。

### 3) 实时性能策略（CPU 友好）

- 模型：默认 `yolov8n-pose`。
- 分辨率：默认 `512 x 384`。
- 跳帧：`skip_frames = 2`（每 3 帧推理一次）。
- 缓存：非推理帧复用上次关键点。
- Windows 摄像头后端回退：DSHOW -> MSMF -> ANY。
- HUD 显示平滑 FPS，便于在线调参。

## 关键模块职责

```text
src/
  main.py                     # 应用编排、主循环、超时清零逻辑
  vision/
    pose_detector.py          # YOLOv8-Pose 封装与设备选择
    frame_processor.py        # 关键点平滑与帧处理
  kinematics/
    joints.py                 # 关键点到关节语义映射
    angle_calculator.py       # 角度/距离/稳定性计算
  engine/
    state_machine.py          # 动作状态机与 reps 计数
    rule_evaluator.py         # 规则评分与 valid 判定
  ui/
    render.py                 # 骨架/HUD 渲染
  reporting/
    report_generator.py       # 训练报告输出(JSON/TXT)
```

## 配置驱动设计

### config/bicep_curl_config.yaml
- 定义动作阈值、时序阈值、评分规则、有效分数线。
- 调整阈值即可改变判定策略，无需改代码。

### config/camera_config.yaml
- 定义视频源、分辨率、目标 FPS、模型与推理参数。
- 可在“准确率/实时性”之间做工程化平衡。

## 运行方式

### 环境准备

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 启动

```bash
python src/main.py
```

### 退出

- 在窗口中按 `Q`。

## 工程特性（当前版本）

- 支持摄像头实时评估和报告落盘。
- 支持左/右臂任一侧满足条件即参与识别。
- 修复了重复评估导致的 `valid` 计数偏大问题。
- 增加“60 秒无动作自动清零 reps/valid”机制。

## 报告输出

输出目录：`data/output_reports/`

- `report_YYYYMMDD_HHMMSS.json`：结构化结果，便于后续接入前端/服务。
- `report_YYYYMMDD_HHMMSS.txt`：可直接阅读的训练总结与建议。

## 后续扩展建议

1. 多动作扩展：通过配置新增深蹲、推举等动作模板。
2. 多线程采集：采集/推理解耦，进一步降低卡顿。
3. 模型量化：提升 CPU 端吞吐。
4. 服务化：将报告和历史曲线接入 Web 后端。

## License

MIT

祝你训练愉快！💪

如有问题或建议，欢迎反馈！
