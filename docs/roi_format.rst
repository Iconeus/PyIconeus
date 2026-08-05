The ``.bri`` format
======================

This page is dedicated to the Scan format '.bri'

.. contents:: On this page
   :local:
   :depth: 2

ROI (Region of Interest)
-------------------------

Attributes
+++++++++++

list : list[RoiElement]
	List containing each ROI of the '.bri' file


RoiElement
-----------

Attributes
+++++++++++

label : str
	Name of the ROI

color : RoiColor # to change
	RoiColor element, containing a (R, G, B) vector

vertices : np.ndarray
	(N, 3) array: each row containing the (x, y, z) coordinates of the vertex

faces : np.ndarray
	(N, 3) array: 3 indices per row, each index refers to the 'vertices' array, building the face

RoiColor
--------

Attributes
++++++++++

x, y, z : float
	r, g, b component of the ROI
