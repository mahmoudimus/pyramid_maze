from __future__ import unicode_literals

from pyramid_maze import Maze, Graph, Node

from webtest import TestApp
import pytest

import simple_app


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

@pytest.fixture(scope='module', autouse=True)
def create_models():
    simple_app.Base.metadata.drop_all()
    simple_app.Base.metadata.create_all()
    corporation = simple_app.CorporationsModel(pk='CR123', name='acme')
    simple_app.ses.add(corporation)
    department = simple_app.DepartmentsModel(
        pk='DP456', name='sales', corporation=corporation
    )
    simple_app.ses.add(department)
    simple_app.ses.commit()


@pytest.fixture()
def app():
    app_ = simple_app.make_app()
    test_app = TestApp(app_)
    return test_app


def test_maze_with_resources(app):
    res = app.get('/Corporations/CR123/Departments/DP456')
    assert res.status_code == 200
    assert res.json == {
        'uri': '/Departments/DP456',
        'under_corporations_uri': '/Corporations/CR123/Departments/DP456'
    }


def test_maze_graph_construction(app):
    assert len(app.app.registry.graph.nodes) == 4
    app.app.registry.graph.draw()
