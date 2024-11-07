:layout: landing
:description: py2app creates application and plugin bundles for Python scripts on macOS

.. rst-class:: lead

   Py2app packages Python GUI applications as standalone macOS application or
   plugin bundles.

   This allows distributing such application to others that don't have
   Python installed on their system.

.. container:: buttons

   `GitHub <https://github.com/ronaldoussoren/py2app>`_ `License <license.html>`_

.. grid:: 1 1 2 3
   :gutter: 2
   :padding:  0
   :class-row: surface

   .. grid-item-card:: Release Info
      :link: changelog
      :link-type: doc

      py2app 2.0 was released on 2024-XX-XX.  See the :doc:`changelog <changelog>` for more information.


   .. grid-item-card:: Supported Platforms
      :link: supported-platforms
      :link-type: doc

      - macOS 10.9 and later
      - Python 3.7 and later
      - x86_64 and arm64

   .. grid-item-card:: Installing py2app
      :link: install
      :link-type: doc

      .. sourcecode:: sh

         $ python3 -mpip \
           install -U py2app

.. toctree::
   :hidden:
   :maxdepth: 1

   install
   changelog
   supported-platforms
   license

.. toctree::
   :maxdepth: 1
   :caption: Introduction

   tutorial
   examples

.. toctree::
   :caption: Usage
   :maxdepth: 1

   command-line
   pyproject
   setuptools

.. toctree::
   :caption: Finetuning
   :maxdepth: 1

   debugging
   environment
   tweaking
   faq

.. toctree::
   :caption: Internals
   :maxdepth: 1

   bundle-structure
   recipes
