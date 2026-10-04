"""Sugilite Swing — neon grappling arcade for ElbowOS. Python 3 + pygame."""
import math
import os
import subprocess
import sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/SUGILITE_SWING_ElbowOS.mp4")
INDIGO = (14, 6, 32)
VIOLET = (168, 86, 214)
MAGENTA = (255, 64, 176)
GOLD = (255, 198, 72)
MINT = (96, 255, 204)
CORAL = (255, 78, 92)
CREAM = (255, 236, 220)
INK = (8, 2, 18)


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        try:
            flags = 0 if PLAY else pygame.HIDDEN
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            self.screen = pygame.Surface((W, H))
        pygame.display.set_caption("Sugilite Swing")
        self.title_f = pygame.font.Font(None, 78)
        self.hud_f = pygame.font.Font(None, 54)
        self.tiny_f = pygame.font.Font(None, 36)
        self.reset()

    def reset(self):
        self.t = 0.0
        self.score = 0
        self.cam = 0.0
        self.anchors = []
        side = 1
        y = 280
        for i in range(28):
            x = 210 if side < 0 else W - 210
            self.anchors.append({"x": x, "y": y, "side": side, "i": i})
            y += 310
            side *= -1
        self.ai = 0
        self.hooked = True
        self.length = 360
        self.ang = -1.05
        self.ang_v = 0.4
        a = self.anchors[0]
        self.px = a["x"] + math.sin(self.ang) * self.length
        self.py = a["y"] + math.cos(self.ang) * self.length
        self.vx = self.vy = 0.0
        self.gems = []
        self.hazards = []
        for i, a in enumerate(self.anchors[:-1]):
            b = self.anchors[i + 1]
            mx = (a["x"] + b["x"]) * 0.5
            for k, col in enumerate((MINT, GOLD, MAGENTA)):
                self.gems.append({
                    "x": mx + (40 if k == 1 else -30),
                    "y": a["y"] + 120 + k * 62,
                    "got": False,
                    "c": col,
                })
            self.hazards.append({
                "x": W * 0.5 + (90 if a["side"] > 0 else -90),
                "y": a["y"] + 200,
            })
        self.trail = []
        self.sparks = []
        self.flash = 0.0
        self.pump = 0

    def latch(self, index):
        self.ai = index
        a = self.anchors[self.ai]
        self.hooked = True
        self.length = 340
        dx, dy = self.px - a["x"], max(40, self.py - a["y"])
        self.ang = math.atan2(dx, dy)
        self.ang = max(-1.25, min(1.25, self.ang))
        self.ang_v = 2.1 * a["side"]
        self.px = a["x"] + math.sin(self.ang) * self.length
        self.py = a["y"] + math.cos(self.ang) * self.length

    def update(self, dt, auto=False, keys=None):
        self.t += dt
        self.flash = max(0.0, self.flash - dt)
        a = self.anchors[self.ai]
        nxt = self.anchors[min(self.ai + 1, len(self.anchors) - 1)]
        if keys:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.ang_v -= 2.4 * dt
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.ang_v += 2.4 * dt
        if self.hooked:
            self.ang_v += -math.sin(self.ang) * (1680 / self.length) * dt
            self.ang_v *= 0.998
            self.ang += self.ang_v * dt
            self.px = a["x"] + math.sin(self.ang) * self.length
            self.py = a["y"] + math.cos(self.ang) * self.length
            toward = 1 if nxt["x"] > a["x"] else -1
            peak = abs(self.ang) > 0.95 and (self.ang * toward) > 0 and (self.ang_v * toward) > 0.2
            if auto and peak and self.ai < len(self.anchors) - 1:
                self.release()
        else:
            self.vy += 520 * dt
            self.px += self.vx * dt
            self.py += self.vy * dt
            if math.hypot(self.px - nxt["x"], self.py - nxt["y"]) < 110 or self.py > nxt["y"] + 30:
                if self.ai < len(self.anchors) - 1:
                    self.latch(self.ai + 1)
                    self.score += 25
        if auto and self.hooked and self.t > 0.4 and self.ai < len(self.anchors) - 1:
            # never stall the reel — force a release if a swing idles
            if abs(self.ang_v) < 0.15 and self.t % 1.6 < dt:
                self.ang_v = 2.2 * a["side"]
        for g in self.gems:
            if not g["got"] and math.hypot(self.px - g["x"], self.py - g["y"]) < 48:
                g["got"] = True
                self.score += 100
                self.flash = 0.18
                for n in range(8):
                    ang = n / 8 * math.tau
                    self.sparks.append([g["x"], g["y"], math.cos(ang) * 220, math.sin(ang) * 220, g["c"], 0.4])
        for hz in self.hazards:
            if math.hypot(self.px - hz["x"], self.py - hz["y"]) < 36:
                self.score = max(0, self.score - 5)
                self.flash = 0.12
        self.trail.append((self.px, self.py))
        if len(self.trail) > 18:
            self.trail.pop(0)
        alive = []
        for s in self.sparks:
            s[0] += s[2] * dt
            s[1] += s[3] * dt
            s[5] -= dt
            if s[5] > 0:
                alive.append(s)
        self.sparks = alive
        target = self.py - H * 0.42
        self.cam += (target - self.cam) * min(1.0, dt * 3.5)
        if self.ai >= len(self.anchors) - 2:
            self.wrap_world()

    def release(self):
        a = self.anchors[self.ai]
        self.hooked = False
        self.vx = math.cos(self.ang) * self.length * self.ang_v
        self.vy = -math.sin(self.ang) * self.length * self.ang_v + 180
        self.vy = max(220, min(720, self.vy))
        self.vx = max(-640, min(640, self.vx))
        self.px = a["x"] + math.sin(self.ang) * self.length
        self.py = a["y"] + math.cos(self.ang) * self.length

    def wrap_world(self):
        shift = self.anchors[6]["y"] - self.anchors[0]["y"]
        for a in self.anchors:
            a["y"] -= shift
        for g in self.gems:
            g["y"] -= shift
            if g["y"] < self.cam - 200:
                g["got"] = False
        for hz in self.hazards:
            hz["y"] -= shift
        self.py -= shift
        self.cam -= shift
        self.trail = [(x, y - shift) for x, y in self.trail]
        self.ai = max(0, self.ai - 6)

    def sy(self, y):
        return int(y - self.cam)

    def draw(self, surf):
        surf.fill(INDIGO)
        for i in range(14):
            yy = (i * 160 - int(self.cam * 0.35) % 160)
            shade = 22 + (i % 3) * 8
            pygame.draw.rect(surf, (shade, 8, 40), (0, yy, W, 80))
        for x in (0, W - 150):
            pygame.draw.rect(surf, (28, 10, 48), (x, 0, 150, H))
            for k in range(18):
                yy = (k * 120 - int(self.cam * 0.5) % 120)
                pygame.draw.polygon(surf, VIOLET, [(x + 150, yy), (x + 110, yy + 28), (x + 150, yy + 56)])
        for a in self.anchors:
            ay = self.sy(a["y"])
            if -80 < ay < H + 80:
                col = GOLD if a["i"] == self.ai else (120, 70, 150)
                pygame.draw.circle(surf, col, (a["x"], ay), 22)
                pygame.draw.circle(surf, CREAM, (a["x"], ay), 8)
        for hz in self.hazards:
            hy = self.sy(hz["y"])
            if -40 < hy < H + 40:
                pygame.draw.polygon(surf, CORAL, [
                    (hz["x"] - 28, hy + 18), (hz["x"], hy - 26), (hz["x"] + 28, hy + 18)
                ])
        for g in self.gems:
            if g["got"]:
                continue
            gy = self.sy(g["y"])
            if -30 < gy < H + 30:
                pulse = 12 + int(6 * math.sin(self.t * 5 + g["x"]))
                pygame.draw.circle(surf, g["c"], (int(g["x"]), gy), pulse)
                pygame.draw.circle(surf, CREAM, (int(g["x"]), gy), 5)
        if self.hooked:
            a = self.anchors[self.ai]
            pygame.draw.line(surf, GOLD, (a["x"], self.sy(a["y"])), (int(self.px), self.sy(self.py)), 4)
        if len(self.trail) > 1:
            pts = [(int(x), self.sy(y)) for x, y in self.trail]
            pygame.draw.lines(surf, MAGENTA, False, pts, 3)
        pygame.draw.circle(surf, VIOLET, (int(self.px), self.sy(self.py)), 26)
        pygame.draw.circle(surf, CREAM, (int(self.px), self.sy(self.py)), 10)
        for s in self.sparks:
            pygame.draw.circle(surf, s[4], (int(s[0]), self.sy(s[1])), 4)
        banner = pygame.Surface((W, 170), pygame.SRCALPHA)
        banner.fill((10, 2, 22, 180))
        surf.blit(banner, (0, 0))
        title = self.title_f.render("SUGILITE SWING", True, GOLD)
        surf.blit(title, title.get_rect(center=(W // 2, 62)))
        sub = self.tiny_f.render("grappling gem run", True, VIOLET)
        surf.blit(sub, sub.get_rect(center=(W // 2, 118)))
        score = self.hud_f.render(f"SCORE  {self.score}", True, CREAM)
        surf.blit(score, score.get_rect(center=(W // 2, 200)))
        foot = pygame.Surface((W, 90), pygame.SRCALPHA)
        foot.fill((10, 2, 22, 190))
        surf.blit(foot, (0, H - 90))
        tag = self.hud_f.render("x.com/ElbowOS", True, MINT)
        surf.blit(tag, tag.get_rect(center=(W // 2, H - 46)))
        if self.flash > 0:
            glow = pygame.Surface((W, H), pygame.SRCALPHA)
            glow.fill((255, 198, 72, int(70 * self.flash / 0.18)))
            surf.blit(glow, (0, 0))

    def play_interactive(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = clock.tick(FPS) / 1000
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_ESCAPE,):
                        running = False
                    if ev.key == pygame.K_SPACE and self.hooked:
                        self.release()
                    if ev.key == pygame.K_r:
                        self.reset()
            keys = pygame.key.get_pressed()
            self.update(dt, auto=False, keys=keys)
            self.draw(self.screen)
            pygame.display.flip()
        pygame.quit()

    def record(self):
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "veryfast", "-movflags", "+faststart", OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        frames = FPS * SECS
        try:
            for i in range(frames):
                self.update(1 / FPS, auto=True)
                self.draw(self.screen)
                proc.stdin.write(pygame.image.tobytes(self.screen, "RGB"))
                if i % 30 == 0:
                    print(f"frame {i}/{frames} score {self.score}", flush=True)
        finally:
            proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore")
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1500:]}")
        print("wrote", OUT)
        pygame.quit()


def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()


if __name__ == "__main__":
    main()
