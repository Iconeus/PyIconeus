The ``.bps`` format
======================

This page is dedicated to the BPS format, ``.bps``.

.. contents:: On this page
   :local:
   :depth: 2

BPS
-----

The BPS (Brain Positioning System) is a 4x4 affine transform from Brain space
to Lab space, also called the Brain-to-Lab transform (B2L). Both the HDF5 and
binary variants are supported. Load it with :func:`pyiconeus.open_path` and
access the matrix through ``data``.

Data
++++

data : np.ndarray
    The 4x4 transform matrix.
