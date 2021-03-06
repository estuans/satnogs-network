Contribute
==========

Thank you for your interest in contributing to SatNOGS! There are always bugs to file; bugs to fix in code; improvements to be made to the documentation; and more.

The below instructions are for software developers who want to work on `satnogs-network code <http://gitlab.com/librespacefoundation/satnogs/satnogs-network>`_.

Git workflow
------------
When you want to start contributing, you should :doc:`follow the installation instructions </netwok/installation>`, then...

#.  (Optional) Set your cloned fork to track upstream changes (changes to the main repository), then fetch and merge changes from the upstream branch::

    $ git remote add --track master upstream git://gitlab.com/librespacefoundation/satnogs/satnogs-network
    $ git fetch upstream
    $ git merge upstream/master

#. Set up a branch for a particular set of changes and switch to it::

    $ git branch my_branch
    $ git checkout my_branch

#. Commit changes to the code!

#. Code!

#. Lint the code::

    $ flake8 network

   and fix any errors.

#. Commit changes to the code!

#. When you're done, figure out how many commits you've made::

    $ git log

#. Squash all those commits into a single commit that has a `good git commit message <http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html>`_. (Example assumes you made 4 commits)::

    $ git rebase -i HEAD~4

#. Use the interactive editor that pops up to pick/squash your commits::

    pick 01d1239 [fix bug 893291] Make it go to 11
    squash 32as32p added the library and made some minor changes
    squash 30ame3z build the template
    squash 91pcla8 ugh fix a semicolon bug in that last commit

#. Push your changes to your fork::

    $ git push origin my_branch

#. Issue a pull request on Gitlab

#. Wait to hear from one of the core developers

If you're asked to change your commit message, you can amend the message and force commit::

  $ git commit --amend
  $ git push -f origin my_branch

If you're asked to make changes on your code you can stage them and amend the commit::

  $ git add my_changed_files
  $ git commit --amend
  $ git push -f origin my_branch

If you need more Git expertise, a good resource is the `Git book <http://git-scm.com/book>`_.

Templates
---------

satnogs-network uses `Django's template engine <https://docs.djangoproject.com/en/dev/topics/templates/>`_ templates.

Frontend development
--------------------

To be able to manage the required javascript libraries, install the development dependencies with npm::

  $ npm install

Development tasks like the download of assets, code linting and tests are managed with gulp::

  $ gulp

Frontend dependencies are stored in packages.json, handled by yarn. To add a new dependency, e.g. satellite.js, call::

  $ yarn add satellite.js

Manually add the new required files to the list of "assets" in packages.json, then start the download with::

  $ gulp assets

The assets are stored in the repository, thus don't forget to create a commit after you add/update/remove dependencies.

Coding Style
------------

#. Four space indentation (no tabs), two whitespace on html documents.
#. Use single quotes for strings. Double quotes used only for html attributes.
#. Keep lines shorter than 100 characters when possible (especially at python code)

Follow the `PEP8 <http://www.python.org/dev/peps/pep-0008/>`_ and `PEP257 <http://www.python.org/dev/peps/pep-0257/#multi-line-docstrings>`_ Style Guides.

Most important things:

#. Separate top-level function and class definitions with two blank lines.
#. Method definitions inside a class are separated by a single blank line.
#. Use whitespace between comma seperated values.
#. Use white space between assignments and expressions (except parameter values).
#. Don't use whitespace before or after parentheses, brackets or braces.
#. Classes should use CamelCase naming.
#. Functions should use lowercase naming.


What to work on
---------------
You can check `opened issues <https://gitlab.com/librespacefoundation/satnogs/satnogs-network/issues>`_. We regurarly open issues for tracking new features. You pick one and start coding.
