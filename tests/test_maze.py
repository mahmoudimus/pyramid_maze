from __future__ import unicode_literals

from pyramid_maze import Node, Maze, Graph

import pytest


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


def printer(node):
    p = 'visiting: %s' % node
    if node.__parent__:
        p += ', child of: %s' % node.__parent__
    print p


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

#
# @pytest.fixture()
# def app():
#     from webtest import TestApp
#     from .testapp import main
#     app = main({})
#     test_app = TestApp(app)
#     return test_app
#
# def test_maze_with_resources(app):
#     res = app.get('/mp/1/accts/2/cards')
#     print res.body