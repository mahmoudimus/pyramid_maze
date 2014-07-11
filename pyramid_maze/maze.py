from .helpers import decorate_leaves_with_lineage, traverse


class Maze(object):

    def __init__(self, graph):
        self.graph = graph

    def _optimal_path(self, is_solution):
        possible_solutions = []

        def on_visit(path):
            if not is_solution(path):
                # current path does not satisfy our constraints, so
                # a possible solution might exist if the current path's
                # last node has children, so we return it to be explored
                return decorate_leaves_with_lineage(path)

            # if we've satisified our reason for traversal
            # then we've hit a potential path!
            possible_solutions.append(path)

        traverse([self.graph.root], on_visit)

        # sort possible solutions on length, since weight is assumed to be one,
        # return smallest.
        possible_solutions.sort(cmp=lambda x, y: len(x) > len(y))
        return possible_solutions[0]

    def route(self, node, include=None):
        """
        Given an directed acyclic graph, ``self.graph``, this method
        will default to finding the shortest path to the desired
        ``node``.

        If ``include`` is passed in, this method will try to find out
        the shortest topologically sorted path that includes a visit
        to all desired nodes in ``include``, eventually, ending up to
        the leaf ``node``.

        """
        include = set(include) if include else set()

        def is_solution(path):
            last_node = path[-1]
            # set of visited nodes in path
            remaining_nodes = set(path[:-1])

            # see if there is any path in current_paths
            # already statifies our requirements
            return last_node == node and remaining_nodes.issuperset(include)

        return self._optimal_path(is_solution)
