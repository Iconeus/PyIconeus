Installation
============

The use of a Python virtual environment is recommended to avoid conflicts with
other Python packages.

Create a virtual environment
-----------------------------

Using `uv <https://docs.astral.sh/uv/>`_:

.. code-block:: console

   uv venv
   .venv/Scripts/activate       # Windows
   source .venv/bin/activate    # Linux/macOS

Install PyIconeus
------------------

From PyPI with uv:

.. code-block:: console

   uv pip install pyiconeus

With pip:

.. code-block:: console

   python -m pip install pyiconeus

Or from the sources:

.. code-block:: console

   python -m pip install -e .

The runtime dependencies are installed automatically: NumPy, pytz, h5py and
transforms3d. To install the test dependency as well from a source checkout:

.. code-block:: console

   python -m pip install -e ".[test]"

Check the installation
------------------------

The repository tests use sample files hosted in a Hugging Face bucket. Each
test downloads only the files it needs, on first use, into
``~/.cache/pyiconeus-test-data`` — there is no separate download step, and the
full 3 GB data set is never required.

Set ``PYICONEUS_TEST_BUCKET`` to change the source, or ``PYICONEUS_TEST_DATA``
to change the cache location. The same fixtures are archived on Zenodo at
`10.5281/zenodo.22249523 <https://doi.org/10.5281/zenodo.22249523>`_.

Run the tests:

.. code-block:: console

   pytest

The package itself does not download data at runtime. Running the tests is
optional for an installed package; it is primarily useful when developing
from a source checkout.
