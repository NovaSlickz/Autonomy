from collections import defaultdict
import time

class FlagManager:
    def __init__(self):
        self.user_scores = defaultdict(float)
        self.last_update = {}

    def add_score(self, user_id, amount):
        self.user_scores[user_id] += amount
        self.last_update[user_id] = time.time()

    def get_score(self, user_id):
        return self.user_scores[user_id]

    def decay(self):
        now = time.time()

        for user_id in list(self.scores.keys()):
            elapsed = now - self.last_update[user_id]

            # Goes down every minute
            self.scores[user_id] *= 0.95 ** (elapsed / 60)

            if self.scores[user_id] <= 0.5:
                del self.scores[user_id]
                del self.last_update[user_id]