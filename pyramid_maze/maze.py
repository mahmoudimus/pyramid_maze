from itertools import imap
from .helpers import traverse, draw_tree


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
                return Node.decorate_leaves_with_lineage(path)

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


class Node(object):
    def __init__(self, name):
        self.name = name
        self.children = []

    def add_child(self, node):
        self.children.append(node)

    def find(self, child_name):
        for child in self.children:
            if child.name == child_name:
                return child

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Node(%s)' % self.name

    def draw(self):
        print '\n' + draw_tree(self)

    @classmethod
    def decorate_leaves_with_lineage(cls, path):
        """
        Decorates a node's children list with the full absolute path
        to that node.

        :param path: A list containing the last node seen, prepended with its
                     lineage.

        :return: A decorated :ref:`Node` that contains a modified children
                 iterable attribute, where every child node is prepended with
                 its lineage (in this case, the path).
        """
        ln = path[-1]
        decorated = cls(ln.name)
        decorated.children = imap(lambda c: path[:] + [c], ln.children)
        return decorated


class Graph(object):
    """
    Represents a collection of :ref:`Node`s. Acts as a fascade to operate
    on a set of nodes.

    """
    def __init__(self, root):
        self.root = root
        self._nodes = None

    def draw(self):
        self.root.draw()

    @property
    def nodes(self):
        """
        Returns a unique set of nodes seen after traversing the entire graph.
        """
        if self._nodes:
            return self._nodes

        uniq_nodes = set()

        def on_visit(node):
            uniq_nodes.add(node)
            return node

        traverse(self.root, on_visit)
        self._nodes = uniq_nodes
        return self._nodes
