# fUS Scan Consolidation — Explanatory Pseudocode

---

## 1. Problem Addressed

A slice-by-slice scan (linear probe or multi-array) is acquired by moving the probe
through a set of *poses*. Each pose produces a volume with its own affine
`voxel → probe → lab`. If the poses are regularly spaced along the *y* axis with a
step close to the slice width, the union of the volumes forms a dense Cartesian
sampling equivalent to that of a static matrix probe.

**Consolidating** = transforming a `(pose, y)` pair into a single continuous
dimension `y'`, *without interpolation* — just a permutation/merging of axes —
provided that the grid is actually regular. If it is not, an error is raised: the
poses are then kept processed separately upstream.

---

## 2. Main Pipeline — `consolidate_scan(dataset, copy)`

```
INPUT : dataset (Iconeus HDF5 file : dataset["Data"], dataset["acqMetaData"])
OUTPUT : (consolidated_data, consolidated_time, translation and rotation matrices, y-size of a voxel after consolidation)

1. data ← flip(dataset["Data"].T, z axis)
   .T : HDF5/MATLAB stores in column-major order; we transpose back to the
        (x, y, z, r, p, c, e) order expected on the Python side.
   flip(z) : inversion to obtain a right-handed frame, cf §4.2

2. n_poses ← data.shape[4] if data has >4 dims, otherwise 1

3. time ← acqMetaData["time"] reshaped (samples, n_poses)
   if n_poses == 1 : time ← time[:, 0]   # collapse back to 1D

4. probe2lab   ← acqMetaData["probeToLab"]     # one 4x4 affine per pose
   voxels2probe ← acqMetaData["voxelsToProbe"]  # single affine (shared across poses)

5. voxels2probe ← FIX_VOXELS2PROBE(voxels2probe, data.shape[2])   # cf §3
   correction for MATLAB (1-based) → Python (0-based) indexing
   + accounting for the z flip from step 1

6. IF multi-array probe (4 stacked elements along y, i.e. shape[1]==4 and ndim>4) :
     (data, time, voxels2probe, probe2lab) ← FIX_MULTIARRAY_PROBE(...)   # cf §4
   each element becomes a fully independent pose in its own right

7. data ← TRANSFORM_7D_TO_6D(data)   # cf §5
   merges the "repetitions" and "cycles" dimensions into a single time dimension

8. (translations, rotations, _) ← DECONVOLVE_PROBE_PATH(probe2lab)   # cf §6
   decomposes the per-pose affines into:
     - a single common center of rotation
     - a set of distinct rotations about z
     - a set of distinct translations along y

9. IF data.ndim < 5 :
   a single pose: nothing to consolidate
   WARN("Scan has only one probe pose.")
   RETURN (data, time)

10. translation_steps ← diff(translations)   # step between successive poses
    median_step ← round(median(translation_steps), 6)

11. pose_order ← argsort(translations)       # sort ascending by y
    translations ← translations[pose_order]

12. IF translation_steps is not ≈ constant (5 µm tolerance, motor precision) :
      RAISE("Poses are irregularly spaced: consolidation is impossible.")
    the grid is not Cartesian → a simple permutation is not possible

13. ELSE IF median_step < 100 µm OR median_step > 1 mm :
      RAISE("... pose-wise affine transformations cannot be collapsed.")
    step too fine (poses nearly coincident) or too coarse (poses too far
    apart to "form a volume") → we prefer to keep the poses separate

14. data ← pad(data, missing dims up to 6D with size-1 axes)

15. data ← transpose(data, axes=(x, p, y, z, t, e))
    data ← reshape merging (p, y) → a single y' axis of size p*y
    ↔ MATLAB : permute then reshape ; this is where the "consolidation" actually
      happens: each pose contributes its y slice, and together they form the
      continuous y' axis.

16. IF reordering is needed (poses not already sorted) OR copy=True :
        data ← data[:, pose_order]     # reindexing ⇒ memory copy

17. time ← time[:, pose_order].copy()   # same reordering applied to time

18. RETURN (data, time, timeIndices, translations, rotations, voxDimDy)
```

---

## 3. `_fix_voxels2probe(voxels2probe, data_shape_z)`

Corrects the *voxel → probe* affine coming from SCAN/ACQ files for use with PyIconeus:

```
FOR i IN {x, y, z} :
    voxels2probe[i, 3] += voxels2probe[i, i]
    half-voxel translation: conversion from MATLAB
    1-based indexing to Numpy 0-based indexing (equivalent : origin(0) = origin(1) - step)

voxels2probe[z, z]  *= -1
voxels2probe[z, off] -= (data_shape_z - 1) * voxels2probe[z, z]
    flip of the z axis (cf step 1 of the main pipeline): we invert the direction
    of the scale AND retranslate the origin so that it still points to the same
    physical voxel after the flip (not just a sign change)
```

---

## 4. `_fix_multiarray_probe(data, time, voxels2probe, probe2lab)`

**Hardware context**: the multi-array probe = 4 independent linear elements stacked
along the axial axis, 2.1 mm apart. The IcoScan acquisition software only provides
**a single affine per pose**, with a coarse voxel step of 2.1 mm along y, whereas each
element actually samples at ~400 µm. Without correction, resampling would give a
completely wrong result (the 4 elements would be treated as 4 contiguous voxels
instead of 4 distinct sub-volumes).

```
1. probe_slice_translations ← relative positions of the 4 elements around the
   pose center (symmetric linspace, step = original voxels2probe[y,y])

2. time ← duplicated 4× (one timestamp per element, inherited from the common pose)

3. data : (x, 4, z, r, p, c, e) → rearranged so that the "element" axis
   (size 4) becomes a full pose axis, merged with the existing p axis
   ↔ MATLAB : permute + reshape, similar to step 17 of the main pipeline,
     but here at the intra-pose level rather than inter-pose

4. FOR each pose AND each element (index 0..3) :
       new_probe2lab[element::4] ← probe2lab[pose] @ translation(y = element position)
   generates 4 "probe→lab" affines per original pose, one per element,
   by composing the pose affine with a pure translation along y

5. voxels2probe[y, y] ← 400 µm   # true inter-element step
   voxels2probe[y, off] ← recentering of the origin on the y axis

6. Sorting of slices by increasing y translation :
   - the "pure translation" part of each affine is isolated
     (the rotation component is cancelled by zeroing the linear part of the
     translation, then the inverse is reapplied to isolate y)
   - argsort on this y component → sorting_indices
   - data, time, new_probe2lab reordered according to sorting_indices
   necessary because IcoScan optimizes its probe movements and therefore does
   not guarantee an ascending order of poses in the output

RETURN (data, time, voxels2probe, new_probe2lab)
```

---

## 5. `_transform_data_7d_to_6d(data)`

```
ACQ/SCAN format (7D) : (x, y, z, r, p, c, e)
    r = repetitions at the same pose, p = poses, c = pose cycles, e = extra

PyIconeus format (6D) : (x, y, z, t, p, e)
    t = time (merge of r and c)

IF ndim > 5 :
    data ← moveaxis(c, position 5 → position 3)   # bring c closer to r
    data ← reshape merging (r, c) → t
    equivalent to MATLAB : permute then reshape, with no additional temporal
      reordering — r and c remain contiguous within the new t axis
RETURN data
```

---

## 6. `_deconvolve_probe_path(tforms)`

Decomposes a set of `voxel → lab` affines (one per pose) into three factored
components, under the assumption that the poses share **a common center**, **a
finite set of rotations** (about z), and **a finite set of translations** (along
y) — like a regular 2D sweep in (rotation, translation) around a fixed center.

```
1. center ← average of the translations (column 3) of all affines
   translation_to_center ← pure translation affine toward this center

2. rotations ← Euler angles about z, UNIQUE values among all poses
   ↔ rotation/translation decomposition similar to `decompose44`, but only
     the z angle (in-plane rotation of the sweep) is kept

3. FOR each rotation AND each translation candidate associated with that rotation :
       residual_tform ← inv(rotation) @ inv(translation_to_center) @ original_affine
       "removing" in turn the rotation and the recentering: what remains
       is a pure translation along y
       translations[index] ← residual_tform[y, off]

4. translations ← round(6 decimal places)   # avoids false duplicates due to numerical noise
   translations ← unique values, in order of first appearance (not sorted)

5. CONSISTENCY CHECK :
   IF len(translations) * len(rotations) != total number of poses :
       RAISE("Could not decompose probe tforms into center, translations and rotations.")
   otherwise, numerical instability has made too many distinct values "visible"
   → the assumed grid structure (rotation × translation) is not respected

RETURN (translations, rotations, center)
```
