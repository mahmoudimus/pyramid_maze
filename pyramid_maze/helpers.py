from cStringIO import StringIO
from collections import Iterable
import re


def traverse(start, on_visit):
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

        assert isinstance(getattr(path, 'children'), Iterable), (
            "Path %s must have a iterable attribute 'children'" % path
        )

        for child in path.children:
            paths_to_explore.append(child)


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


def breadth_first_search(graph):
    targets = [graph.root]
    seen = {graph.root}

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


def convert_to_snake_case(text):
    return re.sub("(?<=[a-z])([A-Z])", "_\\1", text).lower()