"""Simple charts drawn on a Tkinter Canvas (no matplotlib needed)."""

FONT = ("Segoe UI", 8)
TITLE_FONT = ("Segoe UI", 11, "bold")


def _prepare(canvas, title):
    canvas.update_idletasks()
    canvas.delete("all")
    w, h = max(canvas.winfo_width(), 520), max(canvas.winfo_height(), 220)
    canvas.create_text(w / 2, 14, text=title, font=TITLE_FONT)
    return w, h


def _axes(canvas, w, h, left, right, top, bottom):
    ph = h - top - bottom
    for v in range(0, 101, 25):
        y = top + ph - ph * v / 100
        canvas.create_line(left, y, w - right, y, fill="#e5e7eb")
        canvas.create_text(left - 6, y, text=str(v), anchor="e", font=FONT)
    return ph


def bar_chart(canvas, labels, values, title, threshold=None):
    """Bar chart on a 0-100 scale. Bars below `threshold` are drawn in red."""
    w, h = _prepare(canvas, title)
    left, right, top, bottom = 40, 20, 34, 40
    ph = _axes(canvas, w, h, left, right, top, bottom)
    if not values:
        canvas.create_text(w / 2, h / 2, text="No data yet", fill="#6b7280")
        return
    slot = (w - left - right) / len(values)
    bw = min(slot * 0.6, 55)
    for i, (label, value) in enumerate(zip(labels, values)):
        value = value or 0
        x = left + slot * i + (slot - bw) / 2
        y = top + ph - ph * min(value, 100) / 100
        low = threshold is not None and value < threshold
        canvas.create_rectangle(x, y, x + bw, top + ph, fill="#ef4444" if low else "#3b82f6", outline="")
        canvas.create_text(x + bw / 2, y - 8, text=f"{value:.0f}", font=FONT)
        canvas.create_text(x + bw / 2, top + ph + 14, text=label[:11], font=FONT)
    if threshold is not None:
        y = top + ph - ph * threshold / 100
        canvas.create_line(left, y, w - right, y, fill="#f59e0b", dash=(5, 3), width=2)
        canvas.create_text(w - right, y - 8, text=f"{threshold:.0f}%", anchor="e", fill="#b45309", font=FONT)


def scatter_chart(canvas, points, fit, title):
    """Scatter plot of attendance (x) vs marks (y) with an optional regression line."""
    w, h = _prepare(canvas, title)
    left, right, top, bottom = 40, 20, 34, 40
    ph = _axes(canvas, w, h, left, right, top, bottom)
    pw = w - left - right
    if not points:
        canvas.create_text(w / 2, h / 2, text="Need attendance and marks data", fill="#6b7280")
        return

    def px(x):
        return left + pw * x / 100

    def py(y):
        return top + ph - ph * y / 100

    for v in range(0, 101, 25):
        canvas.create_text(px(v), top + ph + 14, text=str(v), font=FONT)
    canvas.create_text(w / 2, h - 8, text="Attendance %", font=FONT)
    if fit:
        slope, intercept = fit
        pts = [(x, slope * x + intercept) for x in (0, 100)]
        pts = [(x, min(100, max(0, y))) for x, y in pts]
        canvas.create_line(px(pts[0][0]), py(pts[0][1]), px(pts[1][0]), py(pts[1][1]),
                           fill="#10b981", width=2, dash=(6, 3))
    for x, y, name in points:
        canvas.create_oval(px(x) - 5, py(y) - 5, px(x) + 5, py(y) + 5, fill="#3b82f6", outline="white")
        canvas.create_text(px(x) + 8, py(y) - 8, text=name.split()[0], anchor="w", font=FONT)
