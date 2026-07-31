Installation
============

The use of a Python virtual environment is recommended to avoid conflicts with
other Python packages.

Create a virtual environment
-----------------------------

Using `uv <https://docs.astral.sh/uv/>`_:

.. code-block:: console

   uv venv
   .venv/Scripts/activate

Install PyIconeus
------------------

With uv:

.. code-block:: console

   uv add pyiconeus

With pip:

.. code-block:: console

   pip install pyiconeus

Or from the sources:

.. code-block:: console

   pip install -e .

Check the installation
------------------------

.. code-block:: console

   pytest
