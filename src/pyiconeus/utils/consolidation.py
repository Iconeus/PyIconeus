"""Functions to consolidate 3D and 3D+t scans."""

import warnings

import numpy as np
import h5py
import numpy.typing as npt
from transforms3d.euler import euler2mat, mat2euler

from .utils import squeeze_trailing, rotation_xyz, translationMatrix


def _fix_multiarray_probe(
    data: npt.NDArray,
    time: npt.NDArray,
    voxels2probe: npt.NDArray,
    probe2lab: npt.NDArray,
    timeOriginal: npt.NDArray,
) -> tuple[npt.NDArray, npt.NDArray, npt.NDArray, npt.NDArray, npt.NDArray]:
    """Fix data and affine transformations acquired using the multi-array probe.

    The multi-array probe consists of 4 independent linear probes stacked along the
    axial dimension and separated by 2.1 mm. However, the IcoScan acquisition software
    outputs data with only one affine transformation per probe pose and voxel dimension
    2.1 mm along the y-axis, resulting in very weird results when resampling the data.

    `_fix_multiarray_probe` performs the following actions:

    * the data is reshaped to move all slices from the y-axis to the pose-axis;
    * the scaling along the y-axis in `voxels2probe` is set to 400 µm;
    * each affine in `probe2lab` is transformed into 4 affines, i.e. one for each probe.
    * the slices are ordered by increasing translation along the y-axis.

    In effect, this results in considering each probe in the multi-array probe as a
    separate pose.

    Parameters
    ----------
    **data** : numpy.ndarray
        Data acquired using the multi-array probe, with shape ``(x, 4, z, r, p, c, e)``.
    **time** : numpy.ndarray
        The time array containing acquisition timings for each probe pose.
    **voxels2probe** : numpy.ndarray
        The affine transformation from voxel space to probe space with shape ``(4, 4)``.
    **probe2lab** : numpy.ndarray
        The affine transformations from probe space to laboratory space with shape ``(p,
        4, 4)``.

    Returns
    -------
**    data** : numpy.ndarray
        The fixed data with shape ``(x, 1, z, r, 4 * p, c, e)``.
    **time** : numpy.ndarray
        The fixed `time` array, with duplicated timings for each probe of the
        multi-array probe at each probe pose.
    **voxels2probe** : numpy.ndarray
        *The* fixed `voxel2probe` affine with ``voxel2probe[1, 1] == 4e-4``.
    **probe2lab** : numpy.ndarray
        The fixed `probe2lab` affines, with ``probe2lab.shape[0] == 4 * p``.
    """
    probe_range = (data.shape[1] - 1) * voxels2probe[1, 1]
    probe_slice_translations = np.linspace(
        -probe_range / 2, probe_range / 2, data.shape[1]
    )

    if time.ndim == 1:
        time = time[:, None]
    time = np.repeat(time, data.shape[1], axis=1)

    if timeOriginal is not None:
        if timeOriginal.ndim == 1:
            timeOriginal = timeOriginal[:, None]
        timeOriginal = np.repeat(timeOriginal, data.shape[1], axis=1)
    # Each probe in the multi-array probe is considered a separate probe pose after
    # reshaping because the probes are separated by 2.1 mm, i.e. way more than the slice
    # width of ~400 µm.
    transposed_axes = [0, 2, 3, 4, 1, 5]
    data = np.transpose(data, axes=transposed_axes[: data.ndim])[:, np.newaxis]
    data = data.reshape(
        data.shape[:4] + (data.shape[4] * data.shape[5],) + data.shape[6:]
    )

    new_probe2lab = np.zeros((data.shape[4], 4, 4))  # ty:ignore[index-out-of-bounds]
    translation_affine = np.eye(4)
    for index, probe_slice_translation in enumerate(probe_slice_translations):
        translation_affine[1, 3] = probe_slice_translation
        new_probe2lab[index :: probe_slice_translations.size] = (
            probe2lab @ translation_affine
        )

    voxels2probe[1, 1] = 4e-4
    voxels2probe[1, 3] = -np.floor(data.shape[1] / 2) * voxels2probe[1, 1]  # ty:ignore[index-out-of-bounds]

    # IcoScan uses a heuristic to speed up probe movements, leading to disordered probe
    # poses. Slices are thus sorted by increasing translation along the y-axis in the
    # voxel space.
    rotations = new_probe2lab.copy()
    rotations[:, :3, 3] = 0
    y_translations = (np.linalg.inv(rotations) @ new_probe2lab)[:, 1, 3]
    sorting_indices = np.argsort(y_translations)
    data = data[:, :, :, :, sorting_indices, ...]
    time = time[:, sorting_indices]
    new_probe2lab = new_probe2lab[sorting_indices, ...]

    if timeOriginal is not None:
        timeOriginal = timeOriginal[:, sorting_indices]

    return data, time, voxels2probe, new_probe2lab, timeOriginal


def _fix_voxels2probe(voxels2probe: npt.NDArray, data_shape_z: int) -> npt.NDArray:
    """Fix a `voxels2probe` affine transformation for use in PyfUS.

    The `voxels2probe` affine transformation used by Iconeus software needs to be
    modified in several ways before being used in PyfUS:

    * To avoid using indirect coordinate systems, the scan data is flipped along the
      *z*-axis. This flip needs to be accounted for by inverting the sign of the
      respective scaling in `voxels2probe`, and to translate the origin along the
      *z*-axis so that it stays on the same voxel.
    * MATLAB uses a one-indexed *voxels* coordinate system, while Numpy/SciPy use a
      zero-indexed coordinate system. Therefore, the `voxels2probe` affine
      transformation obtained from SCAN and ACQ files need to be modified to translate
      the origin from ``(1, 1, 1)`` to ``(0, 0, 0)``.

    Parameters
    ----------
    **voxels2probe** : numpy.ndarray
        A (4, 4) affine transformation from MATLAB's *voxels* to fUSlab's *probe*
        coordinate systems.
    **data_shape_z** : int
        Size of the scan data's *z*-axis.

    Returns
    -------
    numpy.ndarray
        The modified affine transformation, from Numpy/SciPy's *voxels* to fUSlab's
        *probe* coordinate systems.
    """
    voxels2probe = voxels2probe.copy()

    # The voxels space in the SCAN format is defined following MATLAB's one-indexed
    # convention. We need to add a one-voxel translation to get a zero-indexed voxels
    # space.
    for i in range(3):
        voxels2probe[i, 3] += voxels2probe[i, i]

    # PyfUS flips data from SCAN files along the z-axis to get closer to an RAS+
    # oriented volume.
    voxels2probe[2, 2] *= -1
    voxels2probe[2, 3] -= (data_shape_z - 1) * voxels2probe[2, 2]

    return voxels2probe


def _transform_data_7d_to_6d(data: npt.NDArray) -> npt.NDArray:
    """Transform a 7D data array (ACQ/SCAN format) to a 6D data array (PyfUS).

    The 7D data format used by Iconeus has shape ``(x, y, z, r, p, c, e)``:

    - ``(x, y, z)``: spatial dimensions;
    - ``r``: number of repeated volumes at each probe pose, before moving to the next
      probe pose;
    - ``p``: number of probe poses;
    - ``c``: number of cycles of probe poses;
    - ``e``: extra dimension, e.g. for statistics.

    The 6D data format used by PyfUS has shape ``(x, y, z, t, p, e)``:

    - ``(x, y, z)``: spatial dimensions;
    - ``t``: time;
    - ``p``: number of probe poses;
    - ``e``: extra dimension, e.g. for statistics.

    Going from the 7D to the 6D format consists in merging the 7D's ``r`` and ``c``
    dimensions into a single time dimension.

    Parameters
    ----------
    **data** : numpy.ndarray
        The `data` array to transform from 7D format to 6D format.

    Returns
    -------
    **data** : numpy.ndarray
        The transformed `data` array.
    """
    if data.ndim > 5:
        data = np.moveaxis(data, 5, 3)
        data = data.reshape(
            data.shape[:3] + (data.shape[3] * data.shape[4],) + data.shape[5:]
        )

    return data


def _deconvolve_probe_path(
    tforms: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Decompose transforms from probe poses into translations, rotations and center.

    Parameters
    ----------
    **tforms** : numpy.ndarray
        Array of homogeneous transformations from voxel coordinates to laboratory space
        with size ``(pose, 4, 4)``.

    Returns
    -------
    **translations** : numpy.ndarray
        Array of :math:`y`-axis translations.
    **rotations** : numpy.ndarray
        Array of :math:`z`-axis translations.
    **center** : numpy.ndarray
        Array of center coordinates :math:`(x, y, z)`.
    """
    # Transformation center is defined as the "average" translation.

    center = tforms[:, :3, 3].sum(axis=0) / tforms.shape[0]
    translation_to_center_tform = np.eye(4)
    translation_to_center_tform[:3, 3] = center

    rotations = np.degrees(np.unique([mat2euler(m)[2] for m in tforms]))

    # Translations are what's left after "removing" the translation to center
    # and the rotations from the original affine transformations.
    translations = np.zeros((len(tforms),))
    for rotation_index, rotation in enumerate(rotations):
        rotation_tform = np.eye(4)
        rotation_tform[:3, :3] = euler2mat(0, 0, np.radians(rotation))

        n_translations = len(tforms) // len(rotations)
        for translation_index in range(n_translations):
            tform_index = translation_index + n_translations * rotation_index
            translation_tform = (
                np.linalg.inv(rotation_tform)
                @ np.linalg.inv(translation_to_center_tform)
                @ tforms[tform_index]
            )
            translations[tform_index] = translation_tform[1, 3]

    # Round to 6 decimal places to prevent numerical instabilities: under 1e-6,
    # we consider two translations to be the same.
    translations = translations.round(decimals=6)
    # After rounding, we keep unique values without sorting them (np.unique sorts
    # values).
    translations = translations[np.sort(np.unique(translations, return_index=True)[1])]

    # Check if the decomposition makes sense: some numerical instabilities could lead to
    # more translations and/or rotations retrieved.
    if len(translations) * len(rotations) != len(tforms):
        raise RuntimeError(
            "Could not decompose probe tforms into center, translations and rotations."
        )

    return (translations, rotations, translation_to_center_tform)


def consolidate_scan(
    dataset: h5py.Group, copy: bool = True
) -> tuple[npt.NDArray, npt.NDArray, npt.NDArray, npt.NDArray, npt.NDArray, float | None]:
    """Consolidate a scan acquired using regular probe poses.

    Using linear or multi-array probes, whole volumes are generally acquired
    slice-by-slice by moving the ultrasound probe using a motorized setup. Volumes
    acquired at each probe pose share the same voxel dimensions, but each one is
    described by its own origin and orientation in physical space. When the sum of all
    probe poses create a densely sampled volume, the data may be interpolated on a new
    cartesian grid to get a volume equivalent to what would have been acquired using a
    single stationary matrix probe. This interpolation step is commonly called
    *consolidation*. Note that slice-by-slice acquisitions are generally performed such
    that probe poses are regularly spaced along the `y`-axis by intervals close to the
    probe elevation width. In this case, data consolidation simply involves a
    permutation of the `p`- and `y`-axes.

    However, when probe poses do not sample a regular volume, consolidation is not
    possible and poses are thus kept separate in the `p`-axis.

    .. note::
        Consolidation will be performed using the `qform` affine. Probe poses will be
        reordered according to increasing *y*-axis translations.

    Parameters
    ----------
    **scan** : pyfus.scan.Scan
        A scan to be consolidated.
    **copy** : bool, optional
        Whether or not the consolidated scan data is copied. Note that when poses are
        reordered, a copy is always performed. Default is ``True``.

    Returns
    -------
        Consolidated values of the scan:
        **data**, **time**, **theoretical_time_indices**, **probe2labTranslation**, **probe2labRotation**, **voxDimDy**
    """

    data: npt.NDArray = dataset["Data"][:].T

    n_poses: int = data.shape[4] if len(data.shape) > 4 else 1

    smeta: npt.NDArray = dataset["acqMetaData"]

    time: npt.NDArray = smeta["time"][()].reshape((-1, n_poses))

    if n_poses == 1:
        time = time[:, 0]

    timeOriginalRaw: npt.NDArray = smeta["timeOriginal"][()]
    integrationTime: float = smeta["voxDim"]["dt"][()][0][0]  # ty:ignore[invalid-assignment]

    sorted_time_original: npt.NDArray = np.sort(timeOriginalRaw, axis=None)
    dt: float = (
        sorted_time_original[1] - sorted_time_original[0]
        if sorted_time_original.size > 1
        else sorted_time_original[0]
    )

    timeOriginal: npt.NDArray = timeOriginalRaw.reshape((-1, n_poses))
    if n_poses == 1:
        timeOriginal = timeOriginal[:, 0]

    probe2lab: npt.NDArray = smeta["probeToLab"][()]
    voxels2probe: npt.NDArray = smeta["voxelsToProbe"][()]

    voxels2probe: npt.NDArray = _fix_voxels2probe(voxels2probe, data.shape[2])

    # Is multiarray
    if data.shape[1] == 4 and data.ndim > 4:
        data, time, voxels2probe, probe2lab, timeOriginal = _fix_multiarray_probe(
            data, time, voxels2probe, probe2lab, timeOriginal
        )

    data = _transform_data_7d_to_6d(data)

    


    if data.ndim < 5:
        warnings.warn(
            RuntimeWarning("consolidation warn", "Scan has only one probe pose.")
        )
        return data, time, timeOriginal, np.array([probe2lab.T[3][:3]]), np.array([mat2euler(probe2lab)]), None
    
    translations, rotations, translation_to_center_tform = _deconvolve_probe_path(probe2lab)

    voxDimDy = float(np.mean(np.diff(translations)))
    probe2labTranslation = np.ndarray(shape=(len(rotations), 3))
    probe2labRotation: npt.NDArray = np.ndarray(shape=(len(rotations), 3))
    for rotation_index, rotation in enumerate(rotations):
        translation_same_rotation = probe2lab[
            rotation_index * len(rotations) : rotation_index * len(rotations)
            + len(rotations)
        ]
        tformTranslation = translationMatrix(0, np.mean(translations), 0)
        tformRotation = rotation_xyz(np.array([0.0, 0.0, np.radians(rotation)]))
        translation_tform = translation_to_center_tform @ tformRotation @ tformTranslation
        probe2labTranslation[rotation_index] = translation_tform.T[3][:3]
        probe2labRotation[rotation_index] = np.array([0.0, 0.0, np.radians(rotation)])

    translation_steps: npt.NDArray = np.diff(translations)
    # Rounding is necessary to avoid numerical errors when computing the consolidated
    # affine.
    median_translation_step: npt.NDArray = np.round(
        np.median(translation_steps), decimals=6
    )

    # Sort poses by increasing translation along the y-axis.
    pose_order: npt.NDArray = np.argsort(translations)
    translations = translations[pose_order]

    # The precision of the motors is ~5 µm.
    if not np.allclose(translation_steps, median_translation_step, atol=5e-6, rtol=0):
        # If poses aren't regularly spaced, consolidation is impossible.
        raise RuntimeError("Poses are irregularly spaced: consolidation is impossible.")
    elif median_translation_step < 1e-4 or median_translation_step > 1e-3:
        # If the space separating poses is lower than 100 µm or larger than 1 mm, then
        # it is safer to consider them independent.
        raise RuntimeError(
            f"Poses are regularly spaced, but with interval {median_translation_step} "
            "meters: pose-wise affine transformations cannot be collapsed."
        )
    data = data[(slice(None),) * data.ndim + (None,) * (6 - data.ndim)]

    # can consider them as a single volume.
    data = np.transpose(data, axes=(0, 4, 1, 2, 3, 5))
    new_shape = (
        data.shape[0],
        data.shape[1] * data.shape[2],
        data.shape[3],
        data.shape[4],
        1,
        data.shape[5],
    )
    data = data.reshape(new_shape)

    # Reordering by fancy indexing using the pose_order array will always lead to a
    # copy.
    reordering_needed: bool = not all(pose_order == np.arange(len(translations)))
    if reordering_needed or copy:
        data = data[:, pose_order]

    time: npt.NDArray = time[:, pose_order].copy()

    timeOriginal = timeOriginal[:, pose_order].copy()
    theoretical_time_indices: npt.NDArray = np.round(
        (timeOriginal - integrationTime) / dt
    )

    data = squeeze_trailing(data, initial=4)

    return data, time, theoretical_time_indices, probe2labTranslation, probe2labRotation, voxDimDy
