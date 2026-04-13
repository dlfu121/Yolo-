"""
FitVision MVP - 快速演示脚本（模拟整个工作流程）
不需要摄像头，直接生成测试报告
"""

import sys
import os
import numpy as np
from datetime import datetime

# 添加 src 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from engine.state_machine import BicepCurlStateMachine, RepState
from engine.rule_evaluator import RuleEvaluator
from reporting.report_generator import ReportGenerator
import yaml


def load_config(config_path):
    """加载 YAML 配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def simulate_bicep_curl_workout():
    """
    模拟一次完整的二头肌弯举训练
    生成 8 次动作数据（包括标准和非标准动作）
    """
    print("\n" + "="*70)
    print("🏋️ FitVision MVP - 演示模式 (模拟工作流程)")
    print("="*70 + "\n")
    
    # 加载配置
    script_dir = os.path.dirname(os.path.abspath(__file__))
    action_config = load_config(os.path.join(script_dir, 'config/bicep_curl_config.yaml'))
    
    # 初始化引擎
    state_machine = BicepCurlStateMachine(action_config)
    rule_evaluator = RuleEvaluator(action_config)
    report_gen = ReportGenerator(action_config)
    
    print("[Simulation] 初始化模拟数据...")
    print(f"[Simulation] 规则配置: {action_config['action']}\n")
    
    # 模拟 8 次动作
    reps_data = [
        {
            'name': '第 1 次 (标准)',
            'elbow_angles': [170, 165, 150, 120, 80, 50, 45, 60, 100, 145, 165, 170],
            'eccentric_duration': 30,
            'concentric_duration': 25,
            'arm_deviation': [2, 2, 3, 3, 2, 2, 3, 2, 3, 2, 2, 2],
            'wrist_movement': [1.2, 1.1, 1.3, 1.2, 1.1, 1.2, 1.3, 1.1],
        },
        {
            'name': '第 2 次 (速度过快)',
            'elbow_angles': [170, 160, 120, 60, 45, 80, 140, 165, 170],
            'eccentric_duration': 8,  # 太快
            'concentric_duration': 10,
            'arm_deviation': [2, 2, 2, 3, 2, 3, 2, 2, 2],
            'wrist_movement': [1.1, 1.2, 1.3, 1.2, 1.1, 1.2, 1.3, 1.1],
        },
        {
            'name': '第 3 次 (标准)',
            'elbow_angles': [170, 165, 145, 110, 75, 50, 48, 70, 120, 150, 165, 170],
            'eccentric_duration': 28,
            'concentric_duration': 24,
            'arm_deviation': [2, 2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 2],
            'wrist_movement': [1.1, 1.2, 1.1, 1.2, 1.1, 1.2, 1.1, 1.2],
        },
        {
            'name': '第 4 次 (大臂脱离)',
            'elbow_angles': [170, 160, 135, 90, 60, 45, 50, 85, 130, 160, 168, 170],
            'eccentric_duration': 28,
            'concentric_duration': 26,
            'arm_deviation': [3, 5, 8, 12, 15, 14, 12, 8, 5, 3, 2, 2],  # 脱离躯干
            'wrist_movement': [1.2, 1.1, 1.3, 1.2, 1.1, 1.2, 1.3, 1.1],
        },
        {
            'name': '第 5 次 (活动范围不足)',
            'elbow_angles': [170, 165, 150, 120, 95, 85, 85, 100, 130, 160, 168, 170],
            'eccentric_duration': 28,
            'concentric_duration': 24,
            'arm_deviation': [2, 2, 2, 2, 3, 2, 2, 2, 2, 2, 2, 2],
            'wrist_movement': [1.1, 1.2, 1.1, 1.2, 1.1, 1.2, 1.1, 1.2],
        },
        {
            'name': '第 6 次 (标准)',
            'elbow_angles': [170, 164, 142, 105, 72, 48, 46, 75, 125, 155, 167, 170],
            'eccentric_duration': 30,
            'concentric_duration': 26,
            'arm_deviation': [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
            'wrist_movement': [1.0, 1.1, 1.0, 1.1, 1.0, 1.1, 1.0, 1.1],
        },
        {
            'name': '第 7 次 (腕部摆动)',
            'elbow_angles': [170, 165, 145, 105, 70, 48, 50, 80, 135, 160, 168, 170],
            'eccentric_duration': 30,
            'concentric_duration': 25,
            'arm_deviation': [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
            'wrist_movement': [2.5, 3.2, 4.1, 3.8, 3.5, 2.8, 3.0, 2.6],  # 腕部活动过大
        },
        {
            'name': '第 8 次 (标准)',
            'elbow_angles': [170, 166, 148, 115, 78, 50, 47, 72, 128, 158, 167, 170],
            'eccentric_duration': 30,
            'concentric_duration': 25,
            'arm_deviation': [2, 2, 2, 3, 2, 2, 2, 2, 3, 2, 2, 2],
            'wrist_movement': [1.1, 1.0, 1.2, 1.1, 1.0, 1.1, 1.2, 1.0],
        },
    ]
    
    # 评估每一次动作
    all_scores = []
    all_issues = []
    all_feedback = []
    
    for rep_idx, rep in enumerate(reps_data, 1):
        print(f"\n[Simulation] 正在评估 {rep['name']}...")
        
        # 评估该次动作
        eval_result = rule_evaluator.evaluate_rep(rep)
        score = eval_result['score']
        is_valid = eval_result['is_valid']
        
        all_scores.append(score)
        
        # 记录问题和反馈
        for feedback in eval_result.get('feedback', []):
            all_issues.append(feedback)
            all_feedback.append(feedback)
        
        # 显示结果
        status = "✓ 有效" if is_valid else "✗ 无效"
        print(f"  得分: {score}/100 | {status}")
        if eval_result.get('deductions'):
            for issue, points in eval_result['deductions']:
                print(f"    - {issue}: -{points} 分")
    
    # 生成最终报告
    print("\n" + "="*70)
    print("[Simulation] 生成最终报告...")
    print("="*70)
    
    valid_count = sum(1 for s in all_scores if s >= action_config['validity']['min_score'])
    avg_angle = np.mean([min(rep.get('elbow_angles', [90])) for rep in reps_data])
    
    session_data = {
        'total_reps': len(reps_data),
        'valid_reps': valid_count,
        'rep_scores': all_scores,
        'avg_eccentric_time': np.mean([rep['eccentric_duration'] for rep in reps_data]) / 30,
        'avg_concentric_time': np.mean([rep['concentric_duration'] for rep in reps_data]) / 30,
        'avg_elbow_angle_at_bottom': avg_angle,
        'common_issues': all_feedback,
        'duration': 120,  # 模拟 2 分钟会话
        'average_score': np.mean(all_scores)
    }
    
    report = report_gen.generate_report(session_data)
    
    # 保存报告
    os.makedirs(os.path.join(script_dir, 'data/output_reports'), exist_ok=True)
    report_path = os.path.join(
        script_dir,
        f"data/output_reports/report_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    report_gen.save_report(report, report_path)
    
    # 打印摘要
    print("\n" + "="*70)
    print("✅ 演示完成！")
    print("="*70)
    print(f"\n【最终统计】")
    print(f"  • 总次数: {session_data['total_reps']}")
    print(f"  • 有效次数: {session_data['valid_reps']}")
    print(f"  • 平均得分: {session_data['average_score']:.1f}/100")
    print(f"  • 完成率: {100*session_data['valid_reps']/session_data['total_reps']:.1f}%")
    print(f"\n【报告位置】")
    print(f"  • JSON: {report_path}.json")
    print(f"  • 文本: {report_path}.txt")
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    simulate_bicep_curl_workout()
