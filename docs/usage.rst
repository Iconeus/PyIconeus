Usage
=====

PyIconeus exposes a single entry point, :func:`pyiconeus.open_path`, that
inspects a file and returns the matching object
(:class:`~pyiconeus.models.Scan.Scan`, :class:`~pyiconeus.models.Bps.Bps`,
:class:`~pyiconeus.models.Roi.Roi` or :class:`~pyiconeus.models.Raw.Raw`)
depending on its extension.

.. code-block:: python

   from pyiconeus import open_path, Scan, Bps

   scan: Scan = open_path("my_acquisition.scan")
   print(scan.voxels.shape)

   bps: Bps = open_path("my_acquisition.bps")
   print(bps.data)

   # Associate a Bps with a Scan
   scan.bps = bps

``.raw`` files are paired with a ``.hraw`` header file and must be opened by
passing both paths:

.. code-block:: python

   from pyiconeus import open_path, Raw

   raw: Raw = open_path("acquisition.raw", "acquisition.hraw")

Region of interest (``.bri``) files load a list of
:class:`~pyiconeus.models.Roi.RoiElements`, each carrying a label, a color and
a triangulated mesh (``vertices`` / ``faces``):

.. code-block:: python

   from pyiconeus import open_path, Roi

   roi: Roi = open_path("atlas.bri")
   for element in roi.list:
       print(element.name, element.vertices.shape, element.faces.shape)

More complete, runnable walkthroughs are available as notebooks in the
`examples <https://github.com/Iconeus/PyIconeus/tree/main/examples>`_
directory of the repository:

- ``Scan_Plotting_example.ipynb``
- ``Connectivity example.ipynb``
- ``Roi_usage.ipynb``

See the :doc:`api` for the full reference of every class and function.
