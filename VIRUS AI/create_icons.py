import os
import struct
import zlib


def png_chunk(chunk_type, data):
    chunk = chunk_type + data
    return struct.pack(">I", len(data)) + chunk + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)


def rounded_rectangle_contains(x, y, left, top, right, bottom, radius):
    nearest_x = min(max(x, left + radius), right - radius)
    nearest_y = min(max(y, top + radius), bottom - radius)
    return (x - nearest_x) ** 2 + (y - nearest_y) ** 2 <= radius ** 2


def draw_icon(size):
    background = (8, 13, 24)
    outline = (25, 191, 255)
    symbol = (85, 216, 255)
    pixels = bytearray(background * (size * size))

    margin = int(size * 0.1)
    right = size - margin
    bottom = size - margin
    radius = int(size * 0.2)
    border = max(3, int(size * 0.025))
    inner_radius = max(0, radius - border)

    def set_pixel(x, y, color):
        if 0 <= x < size and 0 <= y < size:
            offset = (y * size + x) * 3
            pixels[offset:offset + 3] = bytes(color)

    for y in range(margin, bottom):
        for x in range(margin, right):
            if rounded_rectangle_contains(x + 0.5, y + 0.5, margin, margin, right, bottom, radius):
                if not rounded_rectangle_contains(
                    x + 0.5, y + 0.5, margin + border, margin + border,
                    right - border, bottom - border, inner_radius
                ):
                    set_pixel(x, y, outline)

    points = (
        (int(size * 0.27), int(size * 0.30)),
        (int(size * 0.48), int(size * 0.72)),
        (int(size * 0.73), int(size * 0.30)),
    )
    line_radius = max(8, int(size * 0.085)) / 2
    for start, end in zip(points, points[1:]):
        x1, y1 = start
        x2, y2 = end
        min_x = max(0, int(min(x1, x2) - line_radius - 1))
        max_x = min(size - 1, int(max(x1, x2) + line_radius + 1))
        min_y = max(0, int(min(y1, y2) - line_radius - 1))
        max_y = min(size - 1, int(max(y1, y2) + line_radius + 1))
        dx, dy = x2 - x1, y2 - y1
        length_squared = dx * dx + dy * dy
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                projection = ((x + 0.5 - x1) * dx + (y + 0.5 - y1) * dy) / length_squared
                projection = min(1, max(0, projection))
                nearest_x = x1 + projection * dx
                nearest_y = y1 + projection * dy
                if (x + 0.5 - nearest_x) ** 2 + (y + 0.5 - nearest_y) ** 2 <= line_radius ** 2:
                    set_pixel(x, y, symbol)

    raw = b"".join(b"\0" + pixels[y * size * 3:(y + 1) * size * 3] for y in range(size))
    png = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">2I5B", size, size, 8, 2, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(raw))
        + png_chunk(b"IEND", b"")
    )
    return png

folder = "frontend"
os.makedirs(folder, exist_ok=True)

for size in [192, 512]:
    with open(f"{folder}/icon-{size}.png", "wb") as icon_file:
        icon_file.write(draw_icon(size))

print("Offline Helper icons created successfully!")