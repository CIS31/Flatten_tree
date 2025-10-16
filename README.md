
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
  - **Branche YES** : crée une branche par condition disjonctif (`A ∨ B ⇒ branches séparées avec `A`, avec `B`).  
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


