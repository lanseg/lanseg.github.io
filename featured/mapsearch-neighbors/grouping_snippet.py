def powerset(iterable):
    s = list(iterable)
    powerset = list(chain.from_iterable(combinations(s, r) for r in range(1, len(s) + 1)))
    return powerset

def groupNeighbours(geoms):
    tri = Delaunnay([(g.centroid.x, g.centroid.y) for g in geoms])
    grouped = collections.defaultdict(set)
    for i, j, k in tri.simplices:
        grouped[i] |= {j, k}
        grouped[j] |= {i, k}
        grouped[k] |= {i, j}
    return sorted(grouped.items())

# In case we want to preserve OSM data across transformations.
def map_union(original, grouped):
    if not original or not grouped:
        return []
    tree = strtree.STRtree(original)
	return [
		(i, sorted(tree.query(component, predicate="intersects")))
		for i, component in enumerate(grouped)
	]

def get_neighbors(geoms: list[Geometry]) -> list[tuple[int, ...]]:
    if len(geoms) < 4:
        return powerset(range(len(geoms)))
    grouped = groupNeighbours(geoms)
    return list(
        set(
            tuple(sorted(subgroup))
            for root, other in grouped
            for subgroup in powerset({root} | other)
        )
    )
