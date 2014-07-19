from inspect import getmembers, ismethod

from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.threadlocal import get_current_registry

import venusian

from pyramid_maze import Node, Graph


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
        self.val = val

    def text(self):
        return 'val=%s' % (self.val,)

    phash = text

    def __call__(self, context, request):
        return context.entity and isinstance(context.entity, self.val)


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

    def __init__(self, request, parent=None, name=None, entity=None, **kwargs):
        self.__name__ = name or 'root'
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
        # print 'Created: ', rv
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

    def lookup(self, key):
        return None

    def __repr__(self):
        attributes = dict(
            (key, value)
            for key, value in self.__dict__.iteritems()
            if key != '__name__' and value
        )
        return '<{name}({__name__}): {attributes}>'.format(
            attributes=attributes,
            name=self.__class__.__name__,
            **self.__dict__
        )


class DymamicResource(Resource):

    def lookup(self, key):
        return self


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


class Controller(object):

    __metaclass__ = _ViewBuilder

    #: the resource this controller is registered to. it's set by the
    #: the Resource's metaclass during registration
    resource = None

    def __init__(self, context, request):
        self.request = request
        self.context = context


# resources start
class Root(Resource):
    pass


class CorporationsController(Controller):

    def options(self):
        pass

    def index(self):
        pass

    def create(self):
        pass

    def show(self):
        return Response('hallo')

    def update(self):
        pass

    def delete(self):
        pass


@nest_under(Root)
class Corporations(DymamicResource):
    controller = CorporationsController


class DepartmentsController(Controller):

    def options(self):
        pass

    def index(self):
        pass

    def create(self):
        pass

    def show(self):
        return Response('hallo thar!')

    def update(self):
        pass

    def delete(self):
        pass


@nest_under(Corporations)
@nest_under(Root)
class Departments(DymamicResource):
    controller = DepartmentsController


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