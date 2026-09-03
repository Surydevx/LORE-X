def detect_cycles(depends_map: dict[int, set[int]], id_set: set[int]) -> list[list[int]]:
    """
    Return a list of cycles found via DFS on the dependency graph.
    
    Args:
        depends_map: A mapping of node ID to a set of node IDs it depends on.
        id_set: The set of all valid node IDs in the graph.
        
    Returns:
        A list of cycles, where each cycle is represented as a list of node IDs.
    """
    visited: set[int] = set()
    rec_stack: set[int] = set()
    cycles: list[list[int]] = []
    path: list[int] = []

    def dfs(node: int) -> None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in depends_map.get(node, set()):
            if neighbor not in id_set:
                continue
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in rec_stack:
                # Extract the cycle from path.
                idx = path.index(neighbor)
                cycles.append(path[idx:] + [neighbor])

        path.pop()
        rec_stack.discard(node)

    for node in sorted(id_set):
        if node not in visited:
            dfs(node)

    return cycles
