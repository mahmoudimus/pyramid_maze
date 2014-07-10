from __future__ import unicode_literals
from itertools import imap
from cStringIO import StringIO

from pyramid.location import lineage

import pytest



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

    def _optimal_path(self, is_solution):
        possible_solutions = []

        def on_visit(path):
            if not is_solution(path):
                # current path does not satisfy our constraints, so
                # a possible solution might exist if the current path's
                # last node has children, so we return it to be explored
                return decorate_leaves(path)

            # if we've satisified our reason for traversal
            # then we've hit a potential path!
            possible_solutions.append(path)

        _traverse([self.graph.root], on_visit)

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


def printer(node):
    p = 'visiting: %s' % node
    if node.__parent__:
        p += ', child of: %s' % node.__parent__
    print p


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

        _traverse(self.root, on_visit)
        self._nodes = uniq_nodes
        return self._nodes


def _traverse(start, on_visit):
    """
    Performs a depth-first serach on a tree.

    :param start: The starting node to begin the search
    :param on_visit: A callback function that will be invoked after visiting
                     a potential path.

                     If this method does not return a path, then the search
                     will continue to exhaust the next path in the stack.

                     If a path is returned, it must satisfy a ``children``
                     iterable attribute. This attribute must yield the
                     next paths to push on to the stack.
    :return: None
    """
    paths_to_explore = [start]
    while paths_to_explore:
        path = paths_to_explore.pop(0)
        path = on_visit(path)
        if not path:
            continue

        assert (getattr(path, 'children'),
                "Path %s must have a iterable attribute 'children'" % (path))

        for child in path.children:
            paths_to_explore.append(child)


def decorate_leaves(path):
    """
    Decorates a node's children list with the full absolute path
    to that node.

    :param path: A list containing individual nodes leading up to the
                last node.
    :return: A decorated node that contains a modified children
             iterable attribute, where every child node has every
             intermediary node.
    """
    ln = path[-1]
    decorated = Node(ln.name)
    decorated.children = imap(lambda c: path[:] + [c], ln.children)
    return decorated


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
