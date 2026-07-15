# Consolidation de scans fUS — Pseudocode explicatif

---

## 1. Problème traité

Un scan slice-by-slice (sonde linéaire ou multi-array) est acquis en déplaçant la sonde
selon un ensemble de *poses*. Chaque pose produit un volume avec sa propre affine
`voxel → probe → lab`. Si les poses sont régulièrement espacées le long de l'axe *y*
d'un pas proche de la largeur de tranche, l'union des volumes forme un
échantillonnage cartésien dense équivalent à celui d'une sonde matricielle statique.

**Consolider** = transformer un jeu `(pose, y)` en une seule dimension `y'` continue,
*sans interpolation* — juste une permutation/fusion d'axes — à condition que la grille
soit effectivement régulière. Si elle ne l'est pas, on lève une erreur : les poses
restent alors traitées séparément en amont.

---

## 2. Pipeline principal — `consolidate_scan(dataset, copy)`

```
ENTRÉE : dataset (fichier HDF5 Iconeus : dataset["Data"], dataset["acqMetaData"])
SORTIE : (data_consolidée, time_consolidé, matrices de translations et de rotations, taille en y d'un voxel après consolidation)

1. data ← flip(dataset["Data"].T, axe z)
   .T : HDF5/MATLAB stocke en column-major, on retranspose vers l'ordre
        (x, y, z, r, p, c, e) attendu côté Python.
   flip(z) : inversion pour obtenir un repère direct, cf §4.2

2. n_poses ← data.shape[4] si data a >4 dims, sinon 1

3. time ← acqMetaData["time"] reshape (échantillons, n_poses)
   si n_poses == 1 : time ← time[:, 0]   # on retombe en 1D

4. probe2lab   ← acqMetaData["probeToLab"]     # une affine 4x4 par pose
   voxels2probe ← acqMetaData["voxelsToProbe"]  # affine unique (partagée par les poses)

5. voxels2probe ← FIX_VOXELS2PROBE(voxels2probe, data.shape[2])   # cf §3
   correction indexation MATLAB (1-based) → Python (0-based)
   + prise en compte du flip z de l'étape 1

6. SI sonde multi-array (4 barrettes empilées selon y, i.e. shape[1]==4 et ndim>4) :
     (data, time, voxels2probe, probe2lab) ← FIX_MULTIARRAY_PROBE(...)   # cf §4
   chaque barrette devient une pose indépendante à part entière

7. data ← TRANSFORM_7D_TO_6D(data)   # cf §5
   fusion des dimensions "répétitions" et "cycles" en une unique dimension temps

8. (translations, rotations, _) ← DECONVOLVE_PROBE_PATH(probe2lab)   # cf §6
   décompose les affines par pose en :
     - un unique centre de rotation commun
     - un ensemble de rotations distinctes autour de z
     - un ensemble de translations distinctes le long de y

9. SI data.ndim < 5 :
   une seule pose : rien à consolider
   WARN("Scan has only one probe pose.")
   RETOURNER (data, time)

10. translation_steps ← diff(translations)   # pas entre poses successives
    median_step ← round(median(translation_steps), 6)

11. pose_order ← argsort(translations)       # tri croissant selon y
    translations ← translations[pose_order]

12. SI translation_steps n'est pas ≈ constant (tolérance 5 µm, précision moteur) :
      RAISE("Poses are irregularly spaced: consolidation is impossible.")
    la grille n'est pas cartésienne → pas de simple permutation possible

13. SINON SI median_step < 100 µm OU median_step > 1 mm :
      RAISE("... pose-wise affine transformations cannot be collapsed.")
    pas trop fin (poses quasi confondues) ou trop grossier (poses trop
    espacées pour "faire volume") → on préfère garder les poses séparées

14. data ← pad(data, dims manquantes jusqu'à 6D avec des axes de taille 1)

15. data ← transpose(data, axes=(x, p, y, z, t, e))
    data ← reshape en fusionnant (p, y) → un seul axe y' de taille p*y
    ↔ MATLAB : permute puis reshape ; c'est que se fait la "consolidation" :
      chaque pose apporte sa tranche y, l'ensemble forme l'axe y' continu.

16. SI un réordonnancement est nécessaire (poses non déjà triées) OU copy=True :
        data ← data[:, pose_order]     # réindexation ⇒ copie mémoire

17. time ← time[:, pose_order].copy()   # même réordonnancement appliqué au temps

18. data ← SQUEEZE_TRAILING(data, initial=4)
    # supprime les axes de taille 1 en fin de tableau, en gardant
    # au minimum les 3 dimensions spatiales (x, y, z)

19. RETOURNER (data, time, timeIndices, translations, rotations, voxDimDy)
```

---

## 3. `_fix_voxels2probe(voxels2probe, data_shape_z)`

Corrige l'affine *voxel → probe* issue des fichiers SCAN/ACQ pour l'usage PyIconeus :

```
POUR i DANS {x, y, z} :
    voxels2probe[i, 3] += voxels2probe[i, i]
    translation d'un demi-voxel : passage de l'indexation MATLAB
    1-based à l'indexation Numpy 0-based (équivalent : origin(0) = origin(1) - pas)

voxels2probe[z, z]  *= -1
voxels2probe[z, off] -= (data_shape_z - 1) * voxels2probe[z, z]
    flip de l'axe z (cf étape 1 du pipeline principal) : on inverse le sens
    de l'échelle ET on retranslate l'origine pour qu'elle pointe toujours
    sur le même voxel physique après le flip (pas juste un changement de signe)
```

---

## 4. `_fix_multiarray_probe(data, time, voxels2probe, probe2lab)`

**Contexte matériel** : la sonde multi-array = 4 barrettes linéaires indépendantes
empilées selon l'axe axial, séparées de 2.1 mm. Le logiciel d'acquisition IcoScan ne
fournit qu'**une seule affine par pose** avec un pas de voxel grossier de 2.1 mm selon y,
alors que chaque barrette échantillonne en réalité à ~400 µm. Sans correction,
rééchantillonner donnerait un résultat totalement faux (les 4 barrettes seraient
traitées comme 4 voxels contigus au lieu de 4 sous-volumes distincts).

```
1. probe_slice_translations ← positions relatives des 4 barrettes autour du
   centre de la pose (linspace symétrique, pas = voxels2probe[y,y] d'origine)

2. time ← dupliqué 4× (une timestamp par barrette, héritée de la pose commune)

3. data : (x, 4, z, r, p, c, e) → réarrangé pour faire de l'axe "barrette"
   (taille 4) un axe de pose à part entière, fusionné avec l'axe p existant
   ↔ MATLAB : permute + reshape, comme à l'étape 17 du pipeline principal,
     mais ici au niveau intra-pose plutôt qu'inter-pose

4. POUR chaque pose ET chaque barrette (index 0..3) :
       new_probe2lab[barrette::4] ← probe2lab[pose] @ translation(y = position barrette)
   génère 4 affines "probe→lab" par pose originale, une par barrette,
   en composant l'affine de pose avec une translation pure selon y

5. voxels2probe[y, y] ← 400 µm   # vrai pas inter-barrette
   voxels2probe[y, off] ← recentrage de l'origine sur l'axe y

6. Tri des tranches par translation y croissante :
   - on isole la partie "translation pure" de chaque affine
     (on annule la composante rotation en mettant la partie linéaire de la
     translation à zéro, puis on ré-applique l'inverse pour isoler y)
   - argsort sur cette composante y → sorting_indices
   - data, time, new_probe2lab réordonnés selon sorting_indices
   nécessaire car IcoScan optimise ses déplacements de sonde et ne
   garantit donc pas un ordre croissant des poses en sortie

RETOURNER (data, time, voxels2probe, new_probe2lab)
```

---

## 5. `_transform_data_7d_to_6d(data)`

```
Format ACQ/SCAN (7D) : (x, y, z, r, p, c, e)
    r = répétitions à une même pose, p = poses, c = cycles de poses, e = extra

Format PyIconeus (6D) : (x, y, z, t, p, e)
    t = temps (fusion de r et c)

SI ndim > 5 :
    data ← moveaxis(c, position 5 → position 3)   # rapproche c de r
    data ← reshape fusionnant (r, c) → t
    équivalent MATLAB : permute puis reshape, sans réordonnancement
      temporel supplémentaire — r et c restent contigus dans le nouvel axe t
RETOURNER data
```

---

## 6. `_deconvolve_probe_path(tforms)`

Décompose un ensemble d'affines `voxel → lab` (une par pose) en trois composantes
factorisées, sous l'hypothèse que les poses partagent **un centre commun**, **un jeu
fini de rotations** (autour de z) et **un jeu fini de translations** (selon y) — comme
un balayage 2D régulier en (rotation, translation) autour d'un centre fixe.

```
1. center ← moyenne des translations (colonne 3) de toutes les affines
   translation_to_center ← affine de translation pure vers ce centre

2. rotations ← angles d'Euler autour de z, valeurs UNIQUES parmi toutes les poses
   ↔ décomposition rotation/translation façon `decompose44`, mais on ne
     garde que l'angle z (rotation plane du balayage)

3. POUR chaque rotation ET chaque translation candidate associée à cette rotation :
       tform_résiduelle ← inv(rotation) @ inv(translation_to_center) @ affine_originale
       "on retire" au tour à tour la rotation et le recentrage : ce qui reste
       est une translation pure selon y
       translations[index] ← tform_résiduelle[y, off]

4. translations ← round(6 décimales)   # évite les faux doublons dus au bruit numérique
   translations ← valeurs uniques, ordre de première apparition (pas trié)

5. VÉRIFICATION DE COHÉRENCE :
   SI len(translations) * len(rotations) != nombre total de poses :
       RAISE("Could not decompose probe tforms into center, translations and rotations.")
   sinon, une instabilité numérique a fait "voir" trop de valeurs distinctes
   → la structure en grille (rotation × translation) supposée n'est pas respectée

RETOURNER (translations, rotations, center)
```
