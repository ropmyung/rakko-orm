.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Rakko ORM
=========

.. raw:: html

   <section class="rakko-hero" aria-label="About Rakko ORM">
     <div>
       <p class="rakko-eyebrow">Async Python · MySQL · Typed fields</p>
       <p class="rakko-headline">Write Python.<br>Query with clarity.</p>
       <p class="rakko-intro">A sea otter's home in Python: natural conditions,
       precise field types and an async database foundation.</p>
       <nav class="rakko-actions" aria-label="Start here">
         <a href="getting_started.html">Get started</a>
         <a href="examples/basic.html">Run an example</a>
       </nav>
     </div>
     <img src="_static/rakko-logo.png" alt="A sea otter resting inside a blue ocean wave" width="250" height="250">
   </section>

.. code-block:: python

    members = await Member.filter(
        (Member.age >= 18) & (Member.guild == guild)
    ).order_by(-Member.age).values(Member.name, Member.age)

Built around your model
-----------------------

``Member.age`` is a typed query expression; ``member.age`` is a Python value.
Use field references for selection, sorting, grouping, relations and bulk
operations. Constructor parameters remain visible across query chains and upserts.

Python 3.12+ is required. MySQL async access is a first-class requirement;
SQLite powers runnable examples. Pooling and transactions remain in the backend foundation.

An independent direction
------------------------

Rakko began as a fork of Tortoise ORM and is developed as a separate project.
Its model and query APIs have changed substantially. :doc:`about` records
origins and credits; :doc:`migration_guide` explains the API changes.

.. toctree::
   :hidden:
   :maxdepth: 2

   getting_started
   reference
   examples
   migration_guide
   contrib
   about
   CHANGELOG
   roadmap
   CONTRIBUTING
   releasing
   CONTRIBUTORS
   toc
