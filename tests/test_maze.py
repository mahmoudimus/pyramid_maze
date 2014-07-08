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
        return 'Node(%s, parent=%s)' % (
            self.name,
            self.__parent__
        )

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
        # TODO: runtime?
        if not include:
            visited, path = self._shortest(node)
            print 'visited: ', visited
            print 'path: ', path
            return path
        return self._traverse(node, include)

    def _shortest(self, destination):
        """
        Given a graph, assume that all edges are weighted equally,
        find the shorest path, minimizing the weight to the desired
        node.

        """
        start = self.graph.root
        visited = {start: 0}
        path = {}

        nodes = self.graph.nodes
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

            for edge in self.graph.edges[min_node]:
                weight = current_weight + self.graph.distance[(min_node, edge)]
                if edge not in visited or weight < visited[edge]:
                    visited[edge] = weight
                    path[edge] = min_node

        return visited, path


class Graph(object):

    def __init__(self, root):
        self.root = root
        self.edges = defaultdict(list)
        self.distance = {}
        self._nodes = self._dfs()

    @property
    def nodes(self):
        if not self._nodes:
            self._nodes = self._dfs()
        return self._nodes

    def add_directed_edge(self, from_node, to_node, weight=1):
        self.edges[from_node].append(to_node)
        self.distance[(from_node, to_node)] = weight

    def _dfs(self):
        targets = [self.root]
        seen = set()

        while targets:
            visiting = targets.pop(0)
            print 'visiting %s' % visiting
            for child in visiting.children:
                if child not in seen:
                    print 'havent seen %s, child of %s' % (child, visiting)
                    self.add_directed_edge(visiting, child)
                    targets.insert(0, child)
            seen.add(visiting)
            print 'marking %s as seen' % visiting
        return seen


def test_maze(routes):
    routes.draw()
    cards = routes.find('cards')
    r = Maze(Graph(routes))

    assert '/root/cards' == r.route(cards)
    assert '/root/mp/cards' == r.route(cards, include=[routes.find('mp')])
    assert '/root/accts/cards' == r.route(cards,
                                          include=[routes.find('accts')])
    assert '/root/mp/accts/cards' == r.route(cards, include=[
        routes.find('accts'), routes.find('mp')
    ])
