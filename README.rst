pyramid_maze
============

A `Pyramid <http://docs.pylonsproject.org/en/latest/docs/pyramid.html>`_ plugin
that uses traditional graph traversal algorithms to generate appropriate
routes for resources.

One of its main features is that it respects sub-resources.

.. image:: https://travis-ci.org/mahmoudimus/pyramid_maze.png?branch=master
   :target: https://travis-ci.org/mahmoudimus/pyramid_maze

.. image:: https://coveralls.io/repos/mahmoudimus/pyramid_maze/badge.png?branch=master
   :target: https://coveralls.io/r/mahmoudimus/pyramid_maze?branch=master


Install
-------

.. code::

   pip install pyramid_maze


Tests
-----

First, clone repository and change into the directory. ``setup.py`` should be located in the directory. Then type:

.. code::

   pip install -e '.[tests]'
   tox


License
-------

``pyramid_maze`` is an MIT/BSD dual-Licensed library.


Contribute
----------

- Check for open issues or open a fresh issue to start a discussion around a
  feature idea or a bug.
- Fork the repository on GitHub to start making your changes to the master
  branch (or branch off of it).
- Write a test which shows that the bug was fixed or that the feature
  works as expected.
- Send a pull request and bug the maintainer until it gets merged and
  published.
- Make sure to add yourself to the author's file in ``setup.py`` and the
  ``Contributors`` section below :)


Contributors
------------

- `@mahmoudimus <https://github.com/mahmoudimus>`_
