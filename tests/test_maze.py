from __future__ import unicode_literals
from itertools import count
from cStringIO import StringIO
from collections import defaultdict

import pytest
from pyramid.location import lineage


def draw_tree(node,
              child_iter=lambda n: n.children,
              text_str=str):
    return _draw_tree(node, '', child_iter, text_str)


def _draw_tree(node, prefix, child_iter, text_str):
    buf = StringIO()

    children = list(child_iter(node))

    # check if root node
    if prefix:
        buf.write(prefix[:-3])
        buf.write('  +--')
    buf.write(text_str(node))
    buf.write('\n')

    for index, child in enumerate(children):
        if index + 1 == len(children):
            sub_prefix = prefix + '   '
        else:
            sub_prefix = prefix + '  |'

        buf.write(
            _draw_tree(child, sub_prefix, child_iter, text_str)
        )

    return buf.getvalue()


class Node(object):
    def __init__(self, name):
        self.name = name
        self.children = []
        self.__parent__ = None

    @property
    def parent(self):
        return self.__parent__

    @parent.setter
    def parent(self, value):
        self.__parent__ = value

    def add_child(self, node):
        node.parent = self
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


@pytest.fixture()
def nodes():
    return (Node('root'),
            Node('mp'),
            Node('accts'),
            Node('cards'))


@pytest.fixture()
def routes(nodes):
    root, mp, accts, cards = nodes

    root.add_child(mp)
    root.add_child(accts)
    root.add_child(cards)

    mp.add_child(accts)
    mp.add_child(cards)

    accts.add_child(cards)
    return root


class Maze(object):

    def __init__(self, graph):
        self.graph = graph

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
        if include is not None:
            include = set(include)
        else:
            include = set()
        # return depth_first_search(self.graph, node, include)

        def solution_predicate(path):
            last_node = path[-1]
            # set of visited nodes in path
            remaining_nodes = set(path[:-1])

            # see if there is any path in current_paths
            # already statifies our requirements
            return last_node == node and remaining_nodes.issuperset(include)

        dft = DepthFirstTraverser(self.graph, printer)
        return dft.optimal_path(solution_predicate)


def printer(node):
    p = 'visiting: %s' % node
    if node.__parent__:
        p += ', child of: %s' % node.__parent__
    print p


class Graph(object):

    def __init__(self, root):
        self.root = root
        self.edges = defaultdict(list)
        self.distance = {}
        self._nodes = None

    def draw(self):
        self.root.draw()

    @property
    def nodes(self):
        if not self._nodes:
            self._nodes = DepthFirstTraverser(self, printer).nodes
        return self._nodes

    def add_directed_edge(self, from_node, to_node, weight=1):
        self.edges[from_node].append(to_node)
        self.distance[(from_node, to_node)] = weight


class GraphTraverser(object):

    def __init__(self, graph, visitor=None):
        self.graph = graph
        self.visitor = visitor or self._noop

    @staticmethod
    def _noop(node):
        return node


class DepthFirstTraverser(GraphTraverser):

    @property
    def nodes(self):
        """
        Returns a unique set of nodes seen after traversing the entire graph.
        """
        targets = [self.graph.root]
        uniq_nodes = set(targets)

        while targets:
            visiting = targets.pop(0)
            self.visitor(visiting)
            for child in visiting.children:
                if child not in uniq_nodes:
                    targets.append(child)
            uniq_nodes.add(visiting)
        return uniq_nodes

    def optimal_path(self, satisfies=None, start=None):
        if not satisfies:
            satisfies = self._noop

        if not start:
            start = self.graph.root

        targets = [[start]]
        possible_solutions = []

        while targets:

            solution = targets.pop(0)
            if satisfies(solution):
                # if we've satisified our reason for traversal
                # then we've hit a potential path!
                possible_solutions.append(solution)
                continue

            last_node = solution[-1]
            for child in last_node.children:
                # a possible solution might exist if the current solution's
                # last node has children, so we append it to explore
                targets.append(solution[:] + [child])

        # sort possible solutions on length, since weight is assumed to be one,
        # return smallest.
        possible_solutions.sort(cmp=lambda x, y: len(x) > len(y))
        return possible_solutions[0]


def shortest_paths(graph, destination):
    """
    Given a graph, assume that all edges are weighted equally,
    find the shorest path, minimizing the weight to the desired
    node.

    """
    start = graph.root
    visited = {start: 0}
    path = {}

    nodes = graph.nodes
    while nodes:
        min_node = None
        for node in nodes:
            if node in visited:
                if min_node is None:
                    min_node = node
                elif visited[node] < visited[min_node]:
                    min_node = node

        if min_node is None:
            break

    nodes.remove(min_node)
    current_weight = visited[min_node]

    for edge in graph.edges[min_node]:
        weight = current_weight + graph.distance[(min_node, edge)]
        if edge not in visited or weight < visited[edge]:
            visited[edge] = weight
            path[edge] = min_node

    return visited, path

def breadth_first_search(graph):
    targets = [graph.root]
    seen = set([graph.root])

    while targets:
        visiting = targets.pop(0)
        print 'visiting %s' % visiting
        for child in visiting.children:
            if child not in seen:
                targets.insert(0, child)
                print 'havent seen %s, child of %s' % (child, visiting)
            graph.add_directed_edge(visiting, child)
        seen.add(visiting)
        print 'marking %s as seen' % visiting
    return seen


def test_graph(nodes, routes):
    g = Graph(routes)
    g.draw()
    assert g.nodes == set(nodes)


def test_maze(routes):
    routes.draw()
    cards = routes.find('cards')
    r = Maze(Graph(routes))

    def path_to_url(path):
        return '/' + '/'.join(node.name for node in path)

    assert '/root/cards' == path_to_url(r.route(cards))
    assert '/root/mp/cards' == path_to_url(
        r.route(cards, include=[routes.find('mp')]),
    )
    assert '/root/accts/cards' == path_to_url(
        r.route(cards, include=[routes.find('accts')])
    )
    assert '/root/mp/accts/cards' == path_to_url(
        r.route(cards, include=[
            routes.find('accts'), routes.find('mp')
        ])
    )
