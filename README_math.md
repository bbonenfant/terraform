# River Flow Math

Let the following images be a graphical representation of an example river:
> ![Example River](data/readme_images/example_river.png)

This is a directed graph where each node is a circle (the inner number being it's label) and the arrows indicate
    the directional flow between nodes. Inside each arrow is a label indicating the distance between nodes.

### Assumptions
The following simplifying assumptions are being used:
  * The river has constant width.
  * The river has constant depth.

### Notation
Notationally we define _d<sub>n,m</sub>_ as the distance between adjacent nodes _n_ and _m_. If the nodes 
    _n_ and _m_ are not adjacent or if they are equal, then the distance between them is set to 0 for
    computational ease.

We can then construct a "distance matrix", _**D**_, between nodes. The following is the distance matrix associated with
    the example river:
><img src="https://latex.codecogs.com/png.latex?D&space;=&space;\begin{bmatrix}&space;0&space;&&space;0&space;&&space;4&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;\\&space;0&space;&&space;0&space;&&space;2&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;\\&space;4&space;&&space;2&space;&&space;0&space;&&space;0&space;&&space;1&space;&&space;0&space;&&space;0&space;\\&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;3&space;&&space;0&space;&&space;0&space;\\&space;0&space;&&space;0&space;&&space;1&space;&&space;3&space;&&space;0&space;&&space;2&space;&&space;0&space;\\&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;2&space;&&space;0&space;&&space;1&space;\\&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;1&space;&&space;0&space;\end{bmatrix}" title="D = \begin{bmatrix} 0 & 0 & 4 & 0 & 0 & 0 & 0 \\ 0 & 0 & 2 & 0 & 0 & 0 & 0 \\ 4 & 2 & 0 & 0 & 1 & 0 & 0 \\ 0 & 0 & 0 & 0 & 3 & 0 & 0 \\ 0 & 0 & 1 & 3 & 0 & 2 & 0 \\ 0 & 0 & 0 & 0 & 2 & 0 & 1 \\ 0 & 0 & 0 & 0 & 0 & 1 & 0 \end{bmatrix}" />
Notice that this matrix is symmetric and zero along the diagonal.

Define _**v**<sub>k</sub>_ as the state vector where _(**v**<sub>k</sub>)<sub>j</sub>_ is the "volume" of water associated
    with node _j_ at time step _k_. To construct the initial state, _**v**<sub>0</sub>_ , we define:
><img src="https://latex.codecogs.com/png.latex?(v_0)_j&space;=&space;\frac{1}{2}\sum\limits_{i=1}^{N}&space;d_{i,j}" title="(v_0)_j = \frac{1}{2}\sum\limits_{i=1}^{N} d_{i,j}" />
This will "bin" the river by demarcating the nodes halfway between themselves and their adjacent nodes. The below
    diagram will clarify:
> ![Example River](data/readme_images/example_river_2.png)

Notice that for Node 1, the initial volume is _(**v**<sub>0</sub>)<sub>1</sub>_ = 2 since the only adjacent node is Node 3
    with _d<sub>1,3</sub>_ = 4. For Node 3, since there are several adjacent nodes, we sum over the half distances to
    these nodes and calculate
    
_(**v**<sub>0</sub>)<sub>3</sub>_
    = 0.5 * (_d<sub>3,1</sub>_ + _d<sub>3,2</sub>_ + _d<sub>3,5</sub>_)
    = 0.5 * (4 + 2 + 1)
    = 3.5

This is only an approximation for the "volume" of water at each node using the assumptions of a river of constant
    width and depth.

Finally there is a "step" vector _**u**_ where _(**u**)<sub>n</sub>_ is the distance of the water at Node n has
    travelled in that time step. This will be determined based upon the current gauge level of the node in a
    yet-to-be-determined way. When constructing the flow matrix, we assume the there is a constant
    step, _u_, for simplicity.

### Constructing the Flow Matrix
The flow matrix will be a matrix which depends on step vector _**u**_. We make the assumption that the flow matrix,
    _**F**_, will leave the initial state vector unchanged (when no rain is flowing into the river),
    i.e. _**Fv**<sub>0</sub>_ = **v**<sub>0</sub>. Each element of _**F**_, _F<sub>ij</sub>_, represents the percentage
    of the water in Node _j_ that flows to Node _i_. Therefore for all non-adjacent nodes _i_ and _j_,
    _F<sub>ij</sub>_ = 0.

We construct the flow matrix from upstream nodes to downstream nodes. For the most upstream nodes, there is no water
    flowing into the nodes from other nodes, and so for such a node _n_, the only nonzero element in row vector
    _**F**<sub>n</sub>_ will be _F<sub>n,n</sub>_. If the proportion of water that flows from the source node is 
    _u(**v**<sub>0</sub>)<sub>n</sub><sup>-1</sup>_, then it follows that
    _F<sub>n,n</sub>_ = 1 - _u(**v**<sub>0</sub>)<sub>n</sub><sup>-1</sup>_.

For those nodes, _m_, which are adjacent to the most upstream nodes, _n_, we have
    _F<sub>m,n</sub>_ = _u(**v**<sub>0</sub>)<sub>n</sub><sup>-1</sup>_.
Filling in the flow matrix for the example river with the information we know so far, we have:
><img src="https://latex.codecogs.com/png.latex?F&space;=&space;\begin{bmatrix}&space;1&space;-&space;\frac{u}{2}&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;\\&space;0&space;&&space;1&space;-&space;\frac{u}{1}&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;\\&space;\frac{u}{2}&space;&&space;\frac{u}{1}&space;&&space;*&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;\\&space;0&space;&&space;0&space;&&space;0&space;&&space;1&space;-&space;\frac{u}{1.5}&space;&&space;0&space;&&space;0&space;&&space;0&space;\\&space;0&space;&&space;0&space;&&space;*&space;&&space;\frac{u}{1.5}&space;&&space;*&space;&&space;0&space;&&space;0&space;\\&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;*&space;&&space;*&space;&&space;0&space;\\&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;*&space;&&space;*&space;\end{bmatrix}" title="F = \begin{bmatrix} 1 - \frac{u}{2} & 0 & 0 & 0 & 0 & 0 & 0 \\ 0 & 1 - \frac{u}{1} & 0 & 0 & 0 & 0 & 0 \\ \frac{u}{2} & \frac{u}{1} & * & 0 & 0 & 0 & 0 \\ 0 & 0 & 0 & 1 - \frac{u}{1.5} & 0 & 0 & 0 \\ 0 & 0 & * & \frac{u}{1.5} & * & 0 & 0 \\ 0 & 0 & 0 & 0 & * & * & 0 \\ 0 & 0 & 0 & 0 & 0 & * & * \end{bmatrix}" />
where the starred values are currently undetermined.

We can solve for the starred value in row 3 in the following way:

Since this starred value should be in the form 1 - _u_ _k_ <sup>-1</sup> for some real number _k_. Then,

_**F**<sub>3</sub> &middot; v<sub>0</sub>_
    = 0.5*u(**v**<sub>0</sub>)<sub>1</sub>*
        + *u(**v**<sub>0</sub>)<sub>2</sub>*
        + (1 - _u_ _k_ <sup>-1</sup>)*(**v**<sub>0</sub>)<sub>3</sub>*
    = *(**v**<sub>0</sub>)<sub>3</sub>*

2*u* - 3.5*u**k* <sup>-1</sup> + 3.5 = 3.5

*k* <sup>-1</sup> = 2 / 3.5

and so the undetermined value is 1 - (2*u* / 3.5)

More generally, for any row _j_ with one undetermined or starred value, if we define:
><img src="https://latex.codecogs.com/png.latex?C_j&space;=&space;\sum\limits_{i&space;\neq&space;j}&space;F_{ij}(v_0)_i" title="C_j = \sum\limits_{i \neq j} F_{ij}(v_0)_i" />
then the undetermined value is equal to 1 - (*uC<sub>j</sub>* / *(v<sub>0</sub>)<sub>j</sub>* )

Finally, we notice that the columns of the flow matrix _**F**_ must sum to 1 (no water is lost in the flow). Therefore
    once we have completed a row, we can use this newly determined value to complete the corresponding column and
    iterate through until the matrix until all values are determined. This algorithm will complete since the river
    graph is fully connected and will not cycle since no cycles exist in the river graph.

The fully completed example flow matrix is as follows.
><img src="https://latex.codecogs.com/png.latex?F&space;=&space;\begin{bmatrix}&space;1&space;-&space;\frac{u}{2}&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;\\&space;0&space;&&space;1&space;-&space;u&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;\\&space;\frac{u}{2}&space;&&space;u&space;&&space;1&space;-&space;\frac{4u}{7}&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;\\&space;0&space;&&space;0&space;&&space;0&space;&&space;1&space;-&space;\frac{2u}{3}&space;&&space;0&space;&&space;0&space;&&space;0&space;\\&space;0&space;&&space;0&space;&&space;\frac{4u}{7}&space;&&space;\frac{2u}{3}&space;&&space;1&space;-&space;u&space;&&space;0&space;&&space;0&space;\\&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;u&space;&&space;1&space;-&space;2u&space;&&space;0&space;\\&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;0&space;&&space;2u&space;&&space;1&space;-&space;6u&space;\end{bmatrix}" title="F = \begin{bmatrix} 1 - \frac{u}{2} & 0 & 0 & 0 & 0 & 0 & 0 \\ 0 & 1 - u & 0 & 0 & 0 & 0 & 0 \\ \frac{u}{2} & u & 1 - \frac{4u}{7} & 0 & 0 & 0 & 0 \\ 0 & 0 & 0 & 1 - \frac{2u}{3} & 0 & 0 & 0 \\ 0 & 0 & \frac{4u}{7} & \frac{2u}{3} & 1 - u & 0 & 0 \\ 0 & 0 & 0 & 0 & u & 1 - 2u & 0 \\ 0 & 0 & 0 & 0 & 0 & 2u & 1 - 6u \end{bmatrix}" />

##### Additional Notes about the Flow Matrix
  * If you multiply the initial vector by this flow matrix you will _NOT_ return the initial state vector.
  This is because water is flowing away from the river source nodes without any upstream water flowing back into them.
  However, for all source nodes _k_ we replace row _**F**<sub>k</sub>_ with _**e**<sub>k</sub>_ (the source node remains
  constant), then the initial state vector _is_ an eigenvector with eigenvalue 1, for all values of _u_.
  
    * Rather than changing the Flow Matrix for an actual model, I believe that the better way to do this is to add
    an offset vector to _**Fv**_ to "fill up" these source nodes by a constant amount each time. A proposal
    offset vector is
    _**s**_ = _**Fv**<sub>0</sub>_ - _**v**<sub>0</sub>_ = (_**F**_ - _**I**_ )_**v**<sub>0</sub>_
  
  * As stated above, this flow matrix is mathematically valid for all values of _u_, however, would only physically
  be valid while each matrix element is non-negative. Therefore this puts a upper-bound on the time step of the model.