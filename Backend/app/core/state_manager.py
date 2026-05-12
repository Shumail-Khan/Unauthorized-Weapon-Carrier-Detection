class ThreatMemory:
    def __init__(self, max_frames=15):
        self.counter = 0
        self.max_frames = max_frames

    def update(self, unauthorized_detected):
        if unauthorized_detected:
            self.counter = self.max_frames
        else:
            self.counter = max(0, self.counter - 1)

    def is_active(self):
        return self.counter > 0


threat_memory = ThreatMemory()