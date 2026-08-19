The ``.bri`` format
======================

This page is dedicated to the ROI format ``.bri``.

.. contents:: On this page
   :local:
   :depth: 2

ROI (Region of Interest)
-------------------------

Attributes
+++++++++++

list : list[RoiElements]
    List containing each ROI of the ``.bri`` file. The order follows the file.


RoiElements
-----------

Attributes
+++++++++++

name : str
    Name of the ROI

color : tuple[float, float, float]
    Normalized (R, G, B) vector with three components in the range 0..1.

vertices : np.ndarray
	(N, 3) array: each row containing the (x, y, z) coordinates of the vertex

faces : np.ndarray
    (N, 3) array: three zero-based indices per row, each referring to
    ``vertices`` and defining one triangular face.
