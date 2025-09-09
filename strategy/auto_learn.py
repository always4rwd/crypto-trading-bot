# strategy/auto_learn.py
import json
import numpy as np

class AutoLearner:
    def __init__(self, log_file='logs/trade_logs.json', learning_rate=0.05):
        self.log_file = log_file
        self.learning_rate = learning_rate

    def apply_learning(self, config):
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except Exception:
            return config
        results = [1 if l.get('result') == 'win' else 0 for l in logs if 'result' in l]
        if len(results) >= 50:
            win_rate = float(np.mean(results[-50:]))
            if win_rate < 0.5:
                config['min_confidence'] = min(config.get('min_confidence', 0.65) + self.learning_rate, 0.95)
            else:
                config['min_confidence'] = max(config.get('min_confidence', 0.65) - self.learning_rate, 0.4)
        return config
