from __future__ import unicode_literals
from itertools import count
from cStringIO import StringIO

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


class Ramp(object):

    def __init__(self, graph):
        self.graph = graph

    def route(self, node, include=None):
        """
        Given an directed acyclical graph, ``self.graph``, this method
        will default to finding the shortest path to the desired
        ``node``.

        If ``include`` is passed in, this method will try to find out
        the shortest topologically sorted path that includes a visit
        to all desired nodes in ``include``, eventually, ending up to
        the leaf ``node``.

        """
        # TODO: runtime?
        if not include:
            return self._shortest(node)
        return self._traverse(node, include)


def test_ramp(routes):
    routes.draw()
    cards = routes.find('cards')
    r = Ramp(routes)

    assert '/root/cards' == r.route(cards)
    assert '/root/mp/cards' == r.route(cards, include=[routes.find('mp')])
    assert '/root/accts/cards' == r.route(cards,
                                          include=[routes.find('accts')])
    assert '/root/mp/accts/cards' == r.route(cards, include=[
        routes.find('accts'), routes.find('mp')
    ])
