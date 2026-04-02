"""Compact sketch wrappers."""

from __future__ import annotations

from fusion_sparse.compact._surface import invoke_generated_method
from fusion_sparse.compact.sketch_text import add_multiline_text, add_path_text
from fusion_sparse.runtime.refs import Ref


class SketchRef(Ref):
    """Thin ergonomic view over a Fusion sketch."""

    def point(self, at):
        return invoke_generated_method(self.raw, "SketchRef.point", at)

    def line(self, a, b):
        return invoke_generated_method(self.raw, "SketchRef.line", a, b)

    def circle(self, center, r):
        return invoke_generated_method(self.raw, "SketchRef.circle", center, r)

    def arc(self, center, start, sweep):
        return invoke_generated_method(self.raw, "SketchRef.arc", center, start, sweep)

    def arc3p(self, a, b, c):
        return invoke_generated_method(self.raw, "SketchRef.arc3p", a, b, c)

    def ellipse(self, center, major, through):
        return invoke_generated_method(self.raw, "SketchRef.ellipse", center, major, through)

    def spline(self, *fit_points):
        if len(fit_points) == 1 and isinstance(fit_points[0], (list, tuple)):
            fit_points = tuple(fit_points[0])
        return invoke_generated_method(self.raw, "SketchRef.spline", fit_points)

    def rect(self, a, b):
        return invoke_generated_method(self.raw, "SketchRef.rect", a, b)

    def rect_center(self, center, corner):
        return invoke_generated_method(self.raw, "SketchRef.rect_center", center, corner)

    def rect3p(self, a, b, c):
        return invoke_generated_method(self.raw, "SketchRef.rect3p", a, b, c)

    def circle2p(self, a, b):
        return invoke_generated_method(self.raw, "SketchRef.circle2p", a, b)

    def circle3p(self, a, b, c):
        return invoke_generated_method(self.raw, "SketchRef.circle3p", a, b, c)

    def text(self, text, corner, diagonal, height, *, h_align="left", v_align="top", spacing=0, font=None, hflip=False, vflip=False):
        return add_multiline_text(
            self.raw,
            text,
            corner,
            diagonal,
            height,
            h_align=h_align,
            v_align=v_align,
            spacing=spacing,
            font=font,
            hflip=hflip,
            vflip=vflip,
        )

    def text_path(self, text, path, height, *, above=False, align="center", spacing=0, font=None, hflip=False, vflip=False):
        return add_path_text(
            self.raw,
            text,
            path,
            height,
            above=above,
            align=align,
            spacing=spacing,
            font=font,
            hflip=hflip,
            vflip=vflip,
        )

    def text_fit(self, text, path, height, *, above=False, font=None, hflip=False, vflip=False):
        return add_path_text(
            self.raw,
            text,
            path,
            height,
            above=above,
            fit=True,
            font=font,
            hflip=hflip,
            vflip=vflip,
        )

    def profile(self, i=0):
        return invoke_generated_method(self.raw, "SketchRef.profile", i)

    def profiles(self):
        return invoke_generated_method(self.raw, "SketchRef.profiles")


__all__ = ["SketchRef"]
