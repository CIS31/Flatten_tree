
🇫🇷 [Version française](#version-française)  
🇬🇧 [English version](#english-version)

## Version française

Le script lit un arbre de décision décrit dans un fichier texte et l'aplatit en une liste de stratégies conjonctives menant à chaque feuille.  
Chaque ligne de sortie représente une combinaison de contraintes aboutissant à une feuille, au format :  `feature1=val & feature2!=val2 : leaf_value`.

## Points clés

- **Parsing**  
  Gère :
  - les nœuds conditionnels au format : `id:[cond1 ||or|| cond2 ||or|| ...] yes=X,no=Y`
  - les feuilles : `id:leaf=0.12345`
  - les opérateurs `=` et `!=`.
  - le séparateur d’OR : `||or||`.

- **Parcours DFS avec sémantique correcte des OR**  
  - **Branche YES** : crée une branche par condition disjonctif (`A ∨ B ⇒ branches séparées avec A, avec B`).  
  - **Branche NO** : ajoute la conjonction des négations de toutes les contions (`A ∧ B`) via la loi de De Morgan.

- **Pruning & simplification automatiques**  
  - Élimine les contradictions comme : `x=4` avec `x!=4`, `x=4` avec `x=5`.  
  - Simplifie les contraintes : si `x=4` est posé, on supprime les `x!=` accumulés pour `x`.

- **Empreinte mémoire faible**  
  - Le lecteur `LazyTreeFileScanner` ne charge pas l’arbre en mémoire.  
  - Chaque recherche d’un nœud se fait à la volée en parcourant le fichier : O(1) mémoire, O(N) temps par lookup.  
  - Option d’optimisation possible : index d’offsets `id → position` pour accélérer les lectures.

## Format de sortie

Chaque ligne est une stratégie complète et les conditions sont jointes par ` & `.

```
<feature_conds_joined_with_&> : <leaf_value>
```


## Fonctionnement de l’algorithme

1. **Parsing**
   - Expressions régulières pour détecter nœuds/feuilles.
   - Découpe des conditions d’un nœud sur `||or||`.
   - Nettoyage des `feature` et `value`.

2. **Représentation des contraintes en cours**
   - Par **feature** :
     - `eq`: valeur d’égalité si connue (sinon `None`),
     - `neq`: ensemble des valeurs interdites.
   - **Simplification** : poser `eq` efface `neq` pour la même feature.
   - **Pruning** immédiat si contradiction.

3. **DFS itérative**
   - Pile de `(node_id, state)` démarrant à l’ID 0.
   - **YES** : pour chaque condition disjonctive, on clone l’état et ajoute cette condition.  
   - **NO** : on clone l’état et ajoute toutes les négations (conjonction).
   - À une feuille, on formate l’état en stratégie et on écrit la ligne.

4. **Formatage de la stratégie**
   - Jointure avec ` & `, puis `: leaf_value`.


## Complexité & performances

- **Mémoire** : O(1) pour la lecture + O(profondeur) pour l’état DFS, en dessous de la taille du fichier d’entrée.
- **Temps** : Avec `LazyTreeFileScanner` : chaque `get_node_by_id` est linéaire dans la taille du fichier → au total O(M·N) avec M nœuds visités, N lignes dans le fichier.

## Utilisation

### Prérequis

- Python **3.8+**
  
### Exécution

```bash
python script.py tree_to_convert.txt strategies.txt
```

## Limitations actuelles

- **Only OR** : le format supporte uniquement des nœuds avec des disjonctions.
- **Opérateurs** limités à `=` et `!=`.

Voici la **traduction anglaise fidèle et naturelle** de ton texte, à ajouter sous la version française dans ton README :


## English version

The script reads a decision tree described in a text file and flattens it into a list of conjunctive strategies leading to each leaf.
Each output line represents a combination of constraints leading to a leaf, in the format:
`feature1=val & feature2!=val2 : leaf_value`.

## Key Points

- **Parsing**
  Handles:

  - Conditional nodes in the format: `id:[cond1 ||or|| cond2 ||or|| ...] yes=X,no=Y`
  - Leaf nodes: `id:leaf=0.12345`
  - Operators `=` and `!=`
  - OR separator: `||or||`

- **DFS traversal with correct OR semantics**

  - **YES branch:** creates one branch per disjunctive condition (`A ∨ B ⇒ separate branches with A, with B`).
  - **NO branch:** adds the conjunction of all negated conditions (`A ∧ B`) following De Morgan’s law.

- **Automatic pruning & simplification**

  - Removes contradictions such as `x=4` with `x!=4`, or `x=4` with `x=5`.
  - Simplifies constraints: if `x=4` is set, all accumulated `x!=` conditions for `x` are removed.

- **Low memory footprint**

  - The `LazyTreeFileScanner` does not load the full tree into memory.
  - Each node lookup is done on the fly by scanning the file: O(1) memory, O(N) time per lookup.
  - Optional optimization: an index mapping `id → position` can be built to speed up lookups.

## Output Format

Each line is a complete strategy, with conditions joined by `&`.

```
<feature_conds_joined_with_&> : <leaf_value>
```

## Algorithm Overview

1. **Parsing**

   - Regular expressions detect nodes and leaves.
   - Node conditions are split on `||or||`.
   - Features and values are cleaned and normalized.

2. **Representation of the current constraint state**

   - By **feature**:

     - `eq`: equality value if known (otherwise `None`),
     - `neq`: set of forbidden values.
   - **Simplification:** setting `eq` clears all `neq` for that feature.
   - **Immediate pruning** on contradiction.

3. **Iterative DFS**

   - Stack of `(node_id, state)` starting at ID 0.
   - **YES:** for each disjunctive condition, clone the state and add that condition.
   - **NO:** clone the state and add all negations (conjunction).
   - At a leaf, format the state into a strategy and write the line.

4. **Strategy formatting**

   - Join with `&`, then append `: leaf_value`.

## Complexity & Performance

- **Memory:** O(1) for reading + O(depth) for the DFS state, well below input file size.
- **Time:** With `LazyTreeFileScanner`, each `get_node_by_id` is linear in file size → total O(M·N) with M visited nodes and N lines in the file.

## Usage

### Requirements

- Python **3.8+**

### Execution

```bash
python script.py tree_to_convert.txt strategies.txt
```

## Current Limitations

- **Only OR:** the format currently supports only disjunctive nodes.
- **Operators:** limited to `=` and `!=`.


