"""Cámara orbital suave: arrastra con el botón derecho para girar, rueda para acercar."""
import math
import builtins
from ursina import camera, Vec3, Vec2, time, mouse, held_keys, lerp

class CameraRig:
    def __init__(self):
        self.target = Vec3(0, 3, 2)
        self.yaw, self.pitch, self.dist = 0.0, 24.0, 40.0
        self.goal = dict(target=Vec3(self.target), yaw=self.yaw, pitch=self.pitch, dist=self.dist)
        self.film = Vec2(0, 0); self.film_goal = Vec2(0, 0)
        self.auto_orbit = 0.0
        self.sway = True
        self.t = 0.0
        self.user = False
        camera.fov = 48
        camera.clip_plane_far = 1200

    def set_goal(self, target=None, yaw=None, pitch=None, dist=None):
        if target is not None: self.goal["target"] = Vec3(target)
        if yaw is not None: self.goal["yaw"] = yaw
        if pitch is not None: self.goal["pitch"] = pitch
        if dist is not None: self.goal["dist"] = dist

    def snap(self):
        self.target = Vec3(self.goal["target"]); self.yaw = self.goal["yaw"]; self.pitch = self.goal["pitch"]; self.dist = self.goal["dist"]

    def working_view(self):
        self.user = False
        self.set_goal(target=(0, 3.4, 2.5), yaw=0, pitch=24, dist=54)

    def drag(self, dx, dy):
        self.user = True
        self.goal["yaw"] += dx * 160
        self.goal["pitch"] = max(6, min(70, self.goal["pitch"] - dy * 120))

    def zoom(self, k):
        self.goal["dist"] = max(18, min(110, self.goal["dist"] * k))

    def update(self):
        dt = min(time.dt, .05); self.t += dt
        if self.auto_orbit:
            self.goal["yaw"] += self.auto_orbit * dt
        k = 1 - math.exp(-dt * 3.2)
        self.target = lerp(self.target, self.goal["target"], k)
        self.yaw += (self.goal["yaw"] - self.yaw) * k
        self.pitch += (self.goal["pitch"] - self.pitch) * k
        self.dist += (self.goal["dist"] - self.dist) * k
        self.film = lerp(self.film, self.film_goal, k)
        sway = math.sin(self.t * .35) * 1.2 if (self.sway and not self.user) else 0
        y, p = math.radians(self.yaw + sway), math.radians(self.pitch)
        off = Vec3(math.sin(y) * math.cos(p), math.sin(p), -math.cos(y) * math.cos(p)) * self.dist
        camera.position = self.target + off
        camera.look_at(self.target)
        builtins.base.camLens.setFilmOffset(self.film.x, self.film.y)
