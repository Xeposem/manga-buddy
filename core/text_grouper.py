"""Group nearby TextRegions that likely belong to the same speech bubble."""

from models.text_region import TextRegion


def _gap(a: TextRegion, b: TextRegion) -> float:
    """Compute the minimum edge-to-edge gap between two regions.

    Returns 0 if they overlap.  For non-overlapping boxes the gap is the
    shortest distance between any pair of edges (horizontal or vertical).
    """
    h_gap = max(0, max(a.x, b.x) - min(a.x + a.w, b.x + b.w))
    v_gap = max(0, max(a.y, b.y) - min(a.y + a.h, b.y + b.h))
    return max(h_gap, v_gap)


def _merge_threshold(a: TextRegion, b: TextRegion) -> float:
    """Adaptive threshold: regions should merge if the gap between them is
    less than the average line height of the two.  This handles both large
    and small text naturally."""
    avg_h = (a.h + b.h) / 2
    return avg_h * 1.8


def group_regions(regions: list) -> list:
    """Cluster a flat list of TextRegions into groups (list of lists).

    Uses single-linkage clustering: two regions join the same group when
    the gap between them is smaller than the adaptive threshold.
    Regions are also checked for horizontal alignment (same column for
    vertical text) or vertical alignment (same row for horizontal text).
    """
    if not regions:
        return []

    n = len(regions)
    # Union-Find
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(n):
        for j in range(i + 1, n):
            a, b = regions[i], regions[j]
            gap = _gap(a, b)
            threshold = _merge_threshold(a, b)
            if gap > threshold:
                continue

            # Check alignment — must share a horizontal or vertical band
            h_overlap = min(a.x + a.w, b.x + b.w) - max(a.x, b.x)
            v_overlap = min(a.y + a.h, b.y + b.h) - max(a.y, b.y)
            min_w = min(a.w, b.w)
            min_h = min(a.h, b.h)

            horizontally_aligned = h_overlap > min_w * 0.3
            vertically_aligned = v_overlap > min_h * 0.3

            if horizontally_aligned or vertically_aligned:
                union(i, j)

    # Collect groups, preserving reading order within each group
    groups_map = {}
    for i in range(n):
        root = find(i)
        groups_map.setdefault(root, []).append(i)

    groups = []
    for indices in groups_map.values():
        group = [regions[i] for i in indices]
        # Sort by reading order: top-to-bottom for vertical, left-to-right for horizontal
        any_vertical = any(r.is_vertical for r in group)
        if any_vertical:
            group.sort(key=lambda r: r.y)
        else:
            group.sort(key=lambda r: (r.y, r.x))
        groups.append(group)

    return groups


def group_text(group: list) -> str:
    """Concatenate the text of a group into a single string for translation."""
    return "".join(r.text for r in group)


def group_bbox(group: list) -> tuple:
    """Compute the bounding box that encloses all regions in a group.

    Returns (x, y, w, h).
    """
    x1 = min(r.x for r in group)
    y1 = min(r.y for r in group)
    x2 = max(r.x + r.w for r in group)
    y2 = max(r.y + r.h for r in group)
    return x1, y1, x2 - x1, y2 - y1
