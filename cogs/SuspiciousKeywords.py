import discord

class SuspiciousKeywords:
    def __init__(self)
        self.known_keywords = self.load_keywords()

    def load_keywords(self):
        hashes = []
        with open(self."./threat_database/suspicious_keywords.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        hashes.append(line)
                    except Exception as e:
                        print(f"[Suspicious Keywords] Invalid keyword skipped: {line} ({e})")
        print(f"[Suspicious Keywords] Loaded {len(hashes)} hashes")
        return hashes