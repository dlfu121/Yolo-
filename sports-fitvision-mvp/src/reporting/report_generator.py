import json
import numpy as np
from datetime import datetime


class ReportGenerator:
    """评估报告生成器"""
    
    def __init__(self, config):
        """
        初始化报告生成器
        
        Args:
            config (dict): 动作配置字典
        """
        self.config = config
    
    def generate_report(self, session_data):
        """
        生成最终评估报告
        
        Args:
            session_data (dict): 会话数据
                {
                    'total_reps': int,
                    'valid_reps': int,
                    'rep_scores': [scores],
                    'avg_eccentric_time': float,
                    'avg_concentric_time': float,
                    'avg_elbow_angle_at_bottom': float,
                    'common_issues': [...],
                    'duration': float,
                    'average_score': float
                }
        
        Returns:
            dict: 结构化报告
        """
        rep_scores = session_data.get('rep_scores', [])
        rep_scores = [s for s in rep_scores if not np.isnan(s)]
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'action': self.config['action'],
            'summary': {
                'total_reps': session_data['total_reps'],
                'valid_reps': session_data['valid_reps'],
                'completion_rate': f"{100 * session_data['valid_reps'] / max(session_data['total_reps'], 1):.1f}%",
                'session_duration': f"{session_data['duration']:.1f}s"
            },
            'performance': {
                'avg_score': f"{np.mean(rep_scores) if rep_scores else 0:.1f}/100",
                'min_score': f"{min(rep_scores) if rep_scores else 0:.1f}/100",
                'max_score': f"{max(rep_scores) if rep_scores else 0:.1f}/100",
                'avg_eccentric_time': f"{session_data.get('avg_eccentric_time', 0):.2f}s",
                'avg_concentric_time': f"{session_data.get('avg_concentric_time', 0):.2f}s",
            },
            'biomechanics': {
                'avg_elbow_angle_at_bottom': f"{session_data.get('avg_elbow_angle_at_bottom', 0):.1f}°",
                'range_of_motion': "Good" if session_data.get('avg_elbow_angle_at_bottom', 0) < 70 else "Limited"
            },
            'feedback': {
                'common_issues': session_data.get('common_issues', []),
                'suggestions': self._generate_suggestions(session_data)
            }
        }
        return report
    
    def _generate_suggestions(self, session_data):
        """根据数据生成改进建议"""
        suggestions = []
        common_issues = session_data.get('common_issues', [])
        total_reps = max(1, session_data.get('total_reps', 1))
        
        # 分析issue频率
        issue_count = {}
        for issue in common_issues:
            issue_count[issue] = issue_count.get(issue, 0) + 1
        
        # 生成针对性建议
        if issue_count.get('speed_too_fast', 0) > total_reps * 0.5:
            suggestions.append("加强离心阶段的肌肉控制，建议进行【减速训练】和【顿留训练】")
        
        if issue_count.get('arm_deviation', 0) > 0:
            suggestions.append("保持大臂贴近躯干，可在两臂间夹一本书进行持久训练")
        
        if issue_count.get('wrist_movement', 0) > 0:
            suggestions.append("稳定腕部，避免在动作过程中旋转或摆动，可使用腕部护具")
        
        if issue_count.get('incomplete_range', 0) > total_reps * 0.3:
            suggestions.append("增大活动范围，在最低点充分伸直手臂，充分收缩二头肌")
        
        if not suggestions:
            suggestions.append("动作质量良好，保持持续训练")
        
        return suggestions
    
    def save_report(self, report, output_path):
        """
        保存为 JSON 和文本格式
        
        Args:
            report (dict): 报告字典
            output_path (str): 输出路径（不含扩展名）
        """
        # JSON 格式
        json_path = f"{output_path}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"[ReportGenerator] JSON 报告已保存: {json_path}")
        
        # 文本格式
        txt_path = f"{output_path}.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("           🏋️ FitVision MVP - 健身动作质量评估报告\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"评估时间: {report['timestamp']}\n")
            f.write(f"动作类型: {report['action']}\n")
            f.write("\n" + "-" * 70 + "\n")
            
            f.write("\n【摘要 Summary】\n")
            for k, v in report['summary'].items():
                f.write(f"  • {k}: {v}\n")
            
            f.write("\n【性能指标 Performance】\n")
            for k, v in report['performance'].items():
                f.write(f"  • {k}: {v}\n")
            
            f.write("\n【生物力学 Biomechanics】\n")
            for k, v in report['biomechanics'].items():
                f.write(f"  • {k}: {v}\n")
            
            f.write("\n【反馈与建议 Feedback & Suggestions】\n")
            if report['feedback'].get('common_issues'):
                f.write("  常见问题:\n")
                for i, issue in enumerate(set(report['feedback']['common_issues']), 1):
                    f.write(f"    {i}. {issue}\n")
            
            if report['feedback'].get('suggestions'):
                f.write("\n  改进建议:\n")
                for i, suggestion in enumerate(report['feedback']['suggestions'], 1):
                    f.write(f"    ✓ {suggestion}\n")
            
            f.write("\n" + "=" * 70 + "\n")
        
        print(f"[ReportGenerator] 文本报告已保存: {txt_path}")
