Usage
=====

PyIconeus exposes a single public entry point, :func:`pyiconeus.open_path`,
that checks the path and returns the matching object
(:class:`~pyiconeus.models.Scan.Scan`, :class:`~pyiconeus.models.Bps.Bps`,
:class:`~pyiconeus.models.Roi.Roi` or :class:`~pyiconeus.models.Raw.Raw`)
based on its lowercase extension. The file content is also checked when the
format has a magic header (``.scan``, ``.bps`` and ``.bri``).

.. code-block:: python

   from pyiconeus import open_path, Scan, Bps

   scan: Scan = open_path("my_acquisition.scan")
    print(scan.voxels.shape)  # (sizeX, sizeY, sizeZ, nTime, nPose, dim6)

   bps: Bps = open_path("my_acquisition.bps")
   print(bps.data)

   # Associate a Bps with a Scan
   scan.bps = bps

``.raw`` files are paired with a ``.hraw`` header file and must be opened by
passing both paths. ``blockStart`` and ``blockEnd`` are one-based, inclusive
block numbers. By default only block 1 is loaded.

.. code-block:: python

   from pyiconeus import open_path, Raw

    raw: Raw = open_path("acquisition.raw", "acquisition.hraw")
    raw_subset: Raw = open_path(
        "acquisition.raw", "acquisition.hraw", blockStart=2, blockEnd=4
    )

Region of interest (``.bri``) files load a list of
:class:`~pyiconeus.models.Roi.RoiElements`, each carrying a name, an RGB
color tuple and a triangulated mesh (``vertices`` / ``faces``). Colors are
normalized to the range 0..1. Face indices are zero-based, including for
HDF5 files that store MATLAB-style one-based indices:

.. code-block:: python

   from pyiconeus import open_path, Roi

   roi: Roi = open_path("atlas.bri")
   for element in roi.list:
        print(element.name, element.color)
        print(element.vertices.shape, element.faces.shape)

``.bps`` files expose their 4x4 Brain-to-Lab transform as ``bps.data``. A BPS
object is not automatically associated with a scan; assign it explicitly as
shown above.

Errors
------

``open_path`` raises ``FileNotFoundError`` when either path does not exist,
``ValueError`` for an unsupported extension, a missing/invalid ``.hraw``
header, or an invalid block range, and ``OSError`` when a file cannot be read.

More complete, runnable walkthroughs are available as notebooks in the
`examples <https://github.com/Iconeus/PyIconeus/tree/main/examples>`_
directory of the repository:

- ``Scan_Plotting_example.ipynb``
- ``Connectivity example.ipynb``
- ``Roi_usage.ipynb``
- ``IQ Data loading.ipynb``

See the :doc:`api` for the full reference of every class and function.
