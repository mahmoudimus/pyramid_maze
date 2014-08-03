from inspect import getmembers, ismethod
import os

from pyramid.config import Configurator
from pyramid.renderers import render_to_response
from pyramid.threadlocal import get_current_registry
from sqlalchemy import (
    create_engine, types as satype, schema as sa, orm as saorm
)
from sqlalchemy.inspection import inspect
from sqlalchemy.ext.declarative import declarative_base
import venusian

from pyramid_maze import Node, Graph, Maze


engine = create_engine('sqlite:///%s/pymaze.db' %
                       os.path.dirname(os.path.abspath(__file__)))
Base = declarative_base()


class RelationFetchMixin(object):
    def get_relation(self, target_relation):
        target_relation = target_relation.lower()
        relationships = inspect(self.__class__).relationships
        for rel in relationships.values():
            if rel.table.name == target_relation:
                return getattr(self, rel.key)


class CorporationsModel(Base, RelationFetchMixin):
    __tablename__ = 'corporations'
    pk = sa.Column(satype.Unicode, primary_key=True)
    name = sa.Column(satype.Unicode)


class DepartmentsModel(Base, RelationFetchMixin):
    __tablename__ = 'departments'
    pk = sa.Column(satype.Unicode, primary_key=True)
    name = sa.Column(satype.Unicode)
    corporation_pk = sa.Column(satype.Unicode, sa.ForeignKey(CorporationsModel.pk))

    corporation = saorm.relationship(CorporationsModel)


class EmployeesModel(Base, RelationFetchMixin):
    __tablename__ = 'employees'
    pk = sa.Column(satype.Unicode, primary_key=True)
    name = sa.Column(satype.Unicode)
    department_pk = sa.Column(satype.Unicode, sa.ForeignKey(DepartmentsModel.pk))

    department = saorm.relationship(DepartmentsModel, backref='employees')


conn = engine.connect()
Base.metadata.bind = conn

Session = saorm.scoped_session(saorm.sessionmaker(bind=engine))
ses = Session()
Base.query = Session.query_property()


def nest_under(resource):

    def callback(scanner, sub_resource_name, subresource):
        try:
            graph = getattr(scanner.config.registry, 'graph')
        except AttributeError:
            n = Node(resource.__name__)
            graph = Graph(n)
            scanner.config.registry.graph = graph
        else:
            n = graph.root.find(resource.__name__)

        if sub_resource_name in resource.nested_resources:
            sub_node = graph.root.find(sub_resource_name)
            if sub_node:
                n.add_child(sub_node)
            else:
                n.add_child(Node(sub_resource_name))

    def wrapped(nested_cls):
        resource.nested_resources[nested_cls.__name__] = nested_cls
        nested_cls.parents[resource.__name__] = resource
        venusian.attach(nested_cls, callback)
        return nested_cls

    return wrapped


class ResourcePredicate(object):
    """
    This resource predicate works as a way to choose the correct view callable
    where it is required to distinguish between operating on a resource item
    rather than a collection.

    """

    def __init__(self, val, config):
        self.resource_cls = val

    def text(self):
        return 'val=%s' % (self.resource_cls,)

    phash = text

    def __call__(self, context, request):
        # print '--', self.resource_cls
        # print '--', context.entity
        return self.resource_cls.is_item(context.entity)


class _LinkController(type):

    def __init__(cls, name, bases, dct):
        super(_LinkController, cls).__init__(name, bases, dct)
        venusian.attach(cls, cls.link_controller)

    @classmethod
    def link_controller(mcs, scanner, name, obj):
        if not obj.controller:
            return
        obj.controller.resource = obj


class Resource(object):

    __metaclass__ = _LinkController

    #: the ``controller`` class variable is the designated handler for
    #: all operations on the collection or item of a resource
    controller = None

    nested_resources = {}
    parents = {}

    def __init__(self, request, parent=None, name=None, entity=None, **kwargs):
        self.__name__ = name or ''
        self.__parent__ = parent
        self.request = request
        self.entity = entity
        self.attrs = kwargs

    def _create_resource_context(self, cls, key, entity=None):
        """
        Create a resource context with all the information about the current
        traversal.

        """
        if not cls:
            return
        # print (
        #     'Creating instance of %s while searching for %s (entity?: %s)' %
        #     (cls, key, entity)
        # )
        rv = cls(request=self.request, parent=self, name=key, entity=entity)
        # print 'Created: ', rv, entity
        return rv

    def __getitem__(self, key):
        # try to get nested resource.
        # if we get a keyerror, we check the view callables
        # with the resource as a context
        entity = None
        ctx_cls = type(self)
        try:
            ctx_cls = self.nested_resources[key]
        except KeyError:
            # we couldn't find a nested resource, so now we'll check
            # to see if there's a way to retrieve the entity based
            # on its identifier.
            entity = self.lookup(key)
            if not entity:
                # we couldn't find it, so we just re-raise KeyError telling
                # pyramid to continue with its view callable evaluation
                raise
        ctx = self._create_resource_context(ctx_cls, key, entity)
        return ctx

    @classmethod
    def lookup(cls, key):
        pass

    @classmethod
    def is_item(cls, entity):
        """
        Attempts to identify if `entity` is an instantiated item of the
        resource.
        """
        pass

    def lookup_parent_entity(self, parent_resource):
        pass

    def __resource_url__(self, request, info):
        #return urlparse.urljoin(info['physical_path'], info['virtual_path'])
        return ''

    def __repr__(self):
        attributes = dict(
            (key, value)
            for key, value in self.__dict__.iteritems()
            if key != '__name__' and value
        )
        return '<{name}({__name__})>'.format(
            name=self.__class__.__name__,
            __name__=self.__name__
        )


class NotFound(Exception):
    pass


class DymamicResource(Resource):

    model = None

    @classmethod
    def lookup(cls, key):
        if not cls.model:
            msg = (
                "Couldn't lookup {0:s} with pk={1:s}. Is lookup() implemented?"
                .format(cls, key))
            raise NotFound(msg)
        return cls.model.query.get(key)

    @classmethod
    def is_item(cls, entity):
        if not entity:
            return False
        return isinstance(entity, cls.model)

    def lookup_parent_entity(self, parent_resource):
        # XXX: this should really be an identity check not a string equals
        if parent_resource.name == 'Root':
            return self.request.root
        # print 'looking for: %s (i am %s)' % (parent_resource, self)
        # this should really be able to say give me the relationships
        # associated to this resource..
        #
        # there needs to be a way to maintain relationships between resources
        # and they delegate to the data store underneath
        #
        # dp.__table__.foreign_keys
        for related_object_name, related_object in self.parents.iteritems():
            # print 'parent of %s is %s' % (self, related_object)
            # if the type of the parent_resource is the same as the
            # related object, return that
            if related_object_name == parent_resource.name:
                parent_entity = self.entity.get_relation(related_object_name)
                # print 'found parent: ', parent_entity
                parent_object = related_object(
                    request=self.request,
                    parent=related_object,
                    name=parent_entity.pk,
                    entity=parent_entity
                )
                return parent_object

    def __resource_url__(self, request, info):
        return '/'.join([self.__parent__.__name__, self.entity.pk])


class _ViewBuilder(type):

    ops = {
        'index': ('GET', False),
        'create': ('POST', False),
        'show': ('GET', True),
        'update': (('PUT', 'PATCH'), True),
        'delete': ('DELETE', True),
        'upsert': ('PUT', False),
        'options': ('OPTIONS', False),
    }

    def __init__(cls, name, bases, dct):
        super(_ViewBuilder, cls).__init__(name, bases, dct)
        venusian.attach(cls, cls.register_views)

    @classmethod
    def register_views(mcs, scanner, name, klass):
        # view_kwargs come from
        # 1. cls_settings (@view_config decorator on class)
        # 2. __view_defaults__ (@view_defaults decorator on class)

        cls_settings = getattr(klass, 'view_config', {})
        view_kwargs = cls_settings.copy()
        view_defaults = getattr(klass, '__view_defaults__', {})
        view_kwargs.update(view_defaults)

        views = mcs.eligible_views(klass)
        # print 'views: %s for %s' % (views, name)

        for method_name, view in views:
            if not (hasattr(view, 'view_config') or method_name in mcs.ops):
                continue

            try:
                verbs, requires_entity = mcs.ops[method_name]
            except KeyError:
                verbs, requires_entity = (('GET', ), True)

            if not isinstance(verbs, (tuple, list)):
                verbs = (verbs,)

            view_kwargs['request_method'] = verbs
            # 3. impl.view_config (@view_config decorator on method)
            overrides = getattr(view, 'view_config', {})
            view_kwargs.update(overrides)
            view_kwargs.update({'view': klass, 'attr': method_name})
            if requires_entity:
                view_kwargs['resource'] = klass.resource
            # print 'view_kwargs: ', view_kwargs
            scanner.config.add_view(**view_kwargs)
            scanner.config.commit()

    @classmethod
    def eligible_views(mcs, klass):
        base_methods = getmembers(Controller, predicate=ismethod)
        to_exclude = [name for name, _ in base_methods]
        methods = getmembers(klass, predicate=ismethod)
        views = [
            (method_name, impl)
            for method_name, impl in methods
            if not method_name.startswith('_')
            and method_name not in to_exclude
        ]
        return views


class NoRouteFound(Exception):
    pass


class Controller(object):

    __metaclass__ = _ViewBuilder

    #: the resource this controller is registered to. it's set by the
    #: the Resource's metaclass during registration
    resource = None

    def __init__(self, context, request):
        self.request = request
        self.context = context

    def route(self, include=None):
        # - find shortest parth to hit all nodes given the graph
        include = include or []
        graph = get_current_registry(self.context).graph
        maze = Maze(graph)
        node = graph.root.find(self.resource.__name__)
        include = [graph.root.find(i.__name__) for i in include]
        path_nodes = maze.route(node, include)
        # - if path is not found, throw
        if not path_nodes:
            raise NoRouteFound()
        # - for each node in path, get the resource_url for the node
        #   from the context that satisfy self/include
        path = [self.context]
        for path_node in reversed(path_nodes[:-1]):
            current_entity = path[-1]
            if not current_entity:
                break
            # assume that each node is nested under some resource that
            # it has a relation to, so it follows that there exists a
            # contract that allows us to query the relation
            parent_entity = current_entity.lookup_parent_entity(path_node)
            path.append(parent_entity)

        paths = map(self.request.resource_url, reversed(path))
        return '/'.join(paths)


# resources start
class Root(Resource):
    """
    The resource root that is the start of the graph's traversal
    """


class CorporationsController(Controller):

    def options(self):
        pass

    def index(self):
        pass

    def create(self):
        pass

    def show(self):
        return render_to_response('string', 'hallo', request=self.request)

    def update(self):
        pass

    def delete(self):
        pass


# def relationship(*args):
#     return
#
#
# class _Corporations(DymamicResource):
#     controller = CorporationsController
#     model = CorporationsModel
#
#     root = relationship('Root')
#     relationships = {
#
#         'root': Root,
#     }
#
#
# relationship(_Corporations, Root)
# relationship(_Corporations, )

@nest_under(Root)
class Corporations(DymamicResource):
    controller = CorporationsController
    model = CorporationsModel


class DepartmentsController(Controller):

    def options(self):
        pass

    def index(self):
        pass

    def create(self):
        pass

    def show(self):
        path = {
            'uri': self.route(),
            'under_corporations_uri': self.route(include=[Corporations])
        }
        return render_to_response('json', path, request=self.request)

    def update(self):
        pass

    def delete(self):
        pass


@nest_under(Corporations)
@nest_under(Root)
class Departments(DymamicResource):
    controller = DepartmentsController

    model = DepartmentsModel


@nest_under(Departments)
@nest_under(Root)
class Employees(DymamicResource):
    pass


def root_factory(request):
    return Root(request)


def make_app(default_settings=None, **overrides):
    """
    This function returns a Pyramid WSGI application.
    """
    default_settings = default_settings or {}
    app_settings = default_settings.copy()
    app_settings.update(overrides)

    config = Configurator(settings=app_settings)
    config.add_view_predicate('resource', ResourcePredicate)
    config.set_root_factory(root_factory)
    config.scan()
    return config.make_wsgi_app()


if __name__ == '__main__':
    Base.metadata.drop_all()
    Base.metadata.create_all()
    corporation = CorporationsModel(pk='CR123', name='acme')
    ses.add(corporation)
    department = DepartmentsModel(
        pk='DP456', name='sales', corporation=corporation
    )
    ses.add(department)
    ses.commit()
