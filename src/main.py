import cv2
import yaml
import numpy as np
from datetime import datetime
import sys
import os
import time

# 添加 src 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vision.pose_detector import PoseDetector
from vision.frame_processor import FrameProcessor
from kinematics.angle_calculator import AngleCalculator
from kinematics.joints import JointManager
from engine.state_machine import BicepCurlStateMachine
from engine.rule_evaluator import RuleEvaluator
from ui.render import PoseRenderer
from reporting.report_generator import ReportGenerator


def load_config(config_path):
    """加载 YAML 配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def open_video_capture(source, width, height, fps):
    """在 Windows 上优先尝试更稳定的摄像头后端"""
    if isinstance(source, str) and os.path.exists(source):
        cap = cv2.VideoCapture(source)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, fps)
        return cap, f"视频文件: {source}"

    backends = []
    if os.name == 'nt':
        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
    else:
        backends = [cv2.CAP_ANY]

    last_cap = None
    for backend in backends:
        cap = cv2.VideoCapture(source, backend)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, fps)
        if cap.isOpened():
            backend_name = {
                cv2.CAP_DSHOW: 'DSHOW',
                cv2.CAP_MSMF: 'MSMF',
                cv2.CAP_ANY: 'ANY'
            }.get(backend, str(backend))
            return cap, f"摄像头: {source} (backend={backend_name})"
        last_cap = cap

    return last_cap, f"摄像头: {source}"


def main():
    """主程序入口"""
    print("[Main] 正在初始化 FitVision MVP 系统...")
    
    # 加载配置
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    action_config = load_config(os.path.join(project_root, 'config/bicep_curl_config.yaml'))
    camera_config = load_config(os.path.join(project_root, 'config/camera_config.yaml'))
    
    # 初始化各模块
    print("[Main] 初始化视觉检测模块...")
    detector = PoseDetector(
        model_name=camera_config['pose_detection']['model_name'],
        device=camera_config['pose_detection']['device']
    )
    
    print("[Main] 初始化帧处理器...")
    frame_processor = FrameProcessor(smooth_window=camera_config['processing']['smooth_frames'])
    
    print("[Main] 初始化状态机和规则引擎...")
    state_machine = BicepCurlStateMachine(action_config)
    rule_evaluator = RuleEvaluator(action_config)
    
    print("[Main] 初始化渲染器...")
    renderer = PoseRenderer(action_config)
    
    print("[Main] 初始化报告生成器...")
    report_gen = ReportGenerator(action_config)

    skip_frames = camera_config['processing'].get('skip_frames', 0)
    infer_interval = max(1, skip_frames + 1)
    
    # 打开摄像头或视频文件
    print("[Main] 打开视频源...")
    source = camera_config['camera']['source']

    cap, source_desc = open_video_capture(
        source,
        camera_config['camera']['resolution_width'],
        camera_config['camera']['resolution_height'],
        camera_config['camera']['fps']
    )
    
    if not cap.isOpened():
        print("[Error] 无法打开视频源！")
        return

    print(f"[Main] 使用{source_desc}")
    
    print("[Main] 系统初始化完成，按 'Q' 键退出程序...")
    print("=" * 70)
    
    # 数据记录
    session_start = datetime.now()
    all_rep_data = []
    current_rep = {}
    warnings_buffer = []
    frame_idx = 0
    
    prev_elbow_angles = []
    prev_wrist_positions = []
    prev_arm_deviations = []
    last_keypoints = None
    last_confidences = None
    last_elbow_angle = 0
    last_score = 100
    last_state = state_machine.state

    fps_smoothed = 0.0
    fps_alpha = 0.1
    last_frame_time = time.perf_counter()
    
    # 超时清零逻辑
    last_activity_time = time.time()  # 上次有效运动的时间
    no_action_timeout = 60  # 60 秒无动作则清零

    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("[Main] 视频读取完成")
                break
            
            frame_idx += 1

            now = time.perf_counter()
            current_fps = 1.0 / max(now - last_frame_time, 1e-6)
            last_frame_time = now
            fps_smoothed = current_fps if fps_smoothed == 0 else (fps_alpha * current_fps + (1 - fps_alpha) * fps_smoothed)
            
            # 姿态检测：按跳帧策略减少推理次数
            if frame_idx % infer_interval == 0 or last_keypoints is None:
                keypoints, confidences = detector.detect(frame)
                if len(keypoints) > 0:
                    last_keypoints = keypoints[0]
                    last_confidences = confidences[0]
            
            if last_keypoints is None or last_confidences is None:
                cv2.imshow('FitVision MVP - Bicep Curl', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue

            keypoints = last_keypoints
            confidences = last_confidences
            
            # 坐标平滑
            keypoints = frame_processor.smooth_keypoints(keypoints)
            
            # 提取关节
            joint_mgr = JointManager(
                keypoints,
                confidences,
                confidence_threshold=camera_config['pose_detection']['confidence_threshold']
            )
            joints = joint_mgr.joints
            
            elbow_angle = last_elbow_angle
            arm_deviation = 0
            wrist_movement = 0
            
            # 计算关键指标（左臂或右臂任意一个符合条件就行）
            # 优先检测右臂，如果右臂无法检测则降级到左臂
            use_arm = None
            elbow_confidence_idx = None
            
            if joint_mgr.is_arm_complete('right'):
                use_arm = 'right'
                elbow_confidence_idx = 7  # 右肘在 YOLO 中的索引
            elif joint_mgr.is_arm_complete('left'):
                use_arm = 'left'
                elbow_confidence_idx = 8  # 左肘在 YOLO 中的索引
            
            if use_arm:
                shoulder = joints[f'{use_arm}_shoulder'].position
                elbow = joints[f'{use_arm}_elbow'].position
                wrist = joints[f'{use_arm}_wrist'].position
                
                # 肘关节角度
                elbow_angle = AngleCalculator.angle_between_three_points(shoulder, elbow, wrist)
                
                # 大臂偏离
                arm_deviation = AngleCalculator.horizontal_deviation(shoulder, elbow)
                
                # 腕部稳定性
                prev_wrist_positions.append(wrist)
                prev_wrist_positions = prev_wrist_positions[-5:]  # 保留最后 5 帧
                if len(prev_wrist_positions) > 1:
                    wrist_movement = AngleCalculator.coordinate_variance(prev_wrist_positions)
                
                # 状态机更新
                is_arm_away = arm_deviation > action_config['thresholds']['arm_deviation']
                is_wrist_stable = wrist_movement < action_config['thresholds']['wrist_stability']
                
                state = state_machine.update(
                    elbow_angle, 
                    confidences[elbow_confidence_idx],
                    is_arm_away, 
                    is_wrist_stable
                )
                
                # 记录当前动作数据
                current_rep['elbow_angles'] = current_rep.get('elbow_angles', []) + [elbow_angle]
                prev_elbow_angles.append(elbow_angle)
                prev_arm_deviations.append(arm_deviation)
                last_elbow_angle = elbow_angle
                
                # 动作完成时评估（只在状态刚转移到 PREPARATION 时评估，防止重复计数）
                if state != last_state and state.value == 'preparation' and len(current_rep) > 0:
                    # 计算阶段时长
                    ecc_frames = state_machine.get_stage_duration()
                    
                    current_rep['eccentric_duration'] = ecc_frames
                    current_rep['concentric_duration'] = ecc_frames  # 简化处理
                    current_rep['arm_deviation'] = prev_arm_deviations[-ecc_frames:] if ecc_frames > 0 else []
                    current_rep['wrist_movement'] = [wrist_movement] * max(1, ecc_frames)
                    
                    # 规则评估
                    eval_result = rule_evaluator.evaluate_rep(current_rep)
                    all_rep_data.append(eval_result)
                    
                    # 统计有效次数
                    if eval_result['is_valid']:
                        state_machine.valid_rep_count += 1
                        last_score = eval_result['score']
                    else:
                        last_score = eval_result['score']
                    
                    # 记录反馈/警告
                    for feedback in eval_result.get('feedback', []):
                        warnings_buffer.append(feedback)
                    
                    # 清空当前动作数据
                    current_rep = {}
                    prev_arm_deviations = []
                
                # 更新最后活动时间（非 IDLE 状态）
                if state.value != 'idle':
                    last_activity_time = time.time()
                
                last_state = state
                
                # 检查超时清零逻辑
                current_time = time.time()
                if current_time - last_activity_time > no_action_timeout and state.value == 'idle':
                    # 超过 60 秒无动作，直接清零
                    if state_machine.rep_count > 0 or state_machine.valid_rep_count > 0:
                        print(f"\n[Main] ⏱️ 检测到 {no_action_timeout} 秒无动作，清零计数")
                        state_machine.rep_count = 0
                        state_machine.valid_rep_count = 0
                        last_activity_time = time.time()  # 重置计时器
            
            # 渲染
            frame = renderer.draw_skeleton(frame, keypoints, confidences, threshold=0.5)
            frame = renderer.draw_hud(
                frame, 
                state_machine.state, 
                state_machine.rep_count,
                state_machine.valid_rep_count, 
                elbow_angle,
                last_score,
                warnings_buffer[-5:],  # 显示最近 5 个警告
                frame_idx,
                fps_smoothed
            )
            
            # 显示
            cv2.imshow('FitVision MVP - Bicep Curl', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n[Main] 用户按下退出键")
                break
    
    except Exception as e:
        print(f"[Error] 程序运行出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 生成最终报告
        print("\n" + "=" * 70)
        print("[Main] 正在生成最终评估报告...")
        
        session_duration = (datetime.now() - session_start).total_seconds()
        
        rep_scores = [r['score'] for r in all_rep_data]
        avg_angle_at_bottom = np.nanmin(prev_elbow_angles) if prev_elbow_angles else 0
        
        session_data = {
            'total_reps': state_machine.rep_count,
            'valid_reps': state_machine.valid_rep_count,
            'rep_scores': rep_scores,
            'avg_eccentric_time': 0.5,  # TODO: 实际计算
            'avg_concentric_time': 0.35,
            'avg_elbow_angle_at_bottom': avg_angle_at_bottom,
            'common_issues': warnings_buffer,
            'duration': session_duration,
            'average_score': np.mean(rep_scores) if rep_scores else 0
        }
        
        report = report_gen.generate_report(session_data)
        
        # 创建输出路径
        os.makedirs(os.path.join(project_root, 'data/output_reports'), exist_ok=True)
        report_path = os.path.join(
            project_root, 
            f"data/output_reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        report_gen.save_report(report, report_path)
        
        print("\n" + "=" * 70)
        print("✅ 评估完成！报告已保存。")
        print("=" * 70)
        print(f"\n最终统计:")
        print(f"  • 总次数: {session_data['total_reps']}")
        print(f"  • 有效次数: {session_data['valid_reps']}")
        print(f"  • 平均得分: {session_data['average_score']:.1f}/100")
        print(f"  • 会话时长: {session_data['duration']:.1f}秒")
        print(f"\n报告保存位置: {report_path}")
        print("=" * 70 + "\n")
        
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
