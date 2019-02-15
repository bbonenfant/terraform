# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestObject.test_parse_file 1'] = [
    '''Face(
\tvertices=\\
[[-2. -2.  0.]
 [-2. -1.  0.]
 [-1. -1.  0.]
 [-1. -2.  0.]],
\tnormal=[0. 0. 1.]
\tpolygon=POLYGON Z ((-2 -2 0, -2 -1 0, -1 -1 0, -1 -2 0, -2 -2 0))
\tindex=0
)''',
    '''Face(
\tvertices=\\
[[-2. -1.  0.]
 [-2.  0.  0.]
 [-1.  0.  0.]
 [-1. -1.  0.]],
\tnormal=[0. 0. 1.]
\tpolygon=POLYGON Z ((-2 -1 0, -2 0 0, -1 0 0, -1 -1 0, -2 -1 0))
\tindex=1
)''',
    '''Face(
\tvertices=\\
[[-2.  0.  0.]
 [-2.  1.  0.]
 [-1.  1.  0.]
 [-1.  0.  0.]],
\tnormal=[0. 0. 1.]
\tpolygon=POLYGON Z ((-2 0 0, -2 1 0, -1 1 0, -1 0 0, -2 0 0))
\tindex=2
)''',
    '''Face(
\tvertices=\\
[[-2.  1.  0.]
 [-2.  2.  0.]
 [-1.  2.  0.]
 [-1.  1.  0.]],
\tnormal=[0. 0. 1.]
\tpolygon=POLYGON Z ((-2 1 0, -2 2 0, -1 2 0, -1 1 0, -2 1 0))
\tindex=3
)''',
    '''Face(
\tvertices=\\
[[-1. -2.  0.]
 [-1. -1.  0.]
 [ 0. -1.  0.]
 [ 0. -2.  0.]],
\tnormal=[0. 0. 1.]
\tpolygon=POLYGON Z ((-1 -2 0, -1 -1 0, 0 -1 0, 0 -2 0, -1 -2 0))
\tindex=4
)''',
    '''Face(
\tvertices=\\
[[-1. -1.  0.]
 [-1.  0.  0.]
 [ 0.  0.  0.]
 [ 0. -1.  0.]],
\tnormal=[0. 0. 1.]
\tpolygon=POLYGON Z ((-1 -1 0, -1 0 0, 0 0 0, 0 -1 0, -1 -1 0))
\tindex=5
)''',
    '''Face(
\tvertices=\\
[[-1.  0.  0.]
 [-1.  1.  0.]
 [ 0.  1.  0.]
 [ 0.  0.  0.]],
\tnormal=[0. 0. 1.]
\tpolygon=POLYGON Z ((-1 0 0, -1 1 0, 0 1 0, 0 0 0, -1 0 0))
\tindex=6
)''',
    '''Face(
\tvertices=\\
[[-1.  1.  0.]
 [-1.  2.  0.]
 [ 0.  2.  0.]
 [ 0.  1.  0.]],
\tnormal=[0. 0. 1.]
\tpolygon=POLYGON Z ((-1 1 0, -1 2 0, 0 2 0, 0 1 0, -1 1 0))
\tindex=7
)''',
    '''Face(
\tvertices=\\
[[ 0. -2.  0.]
 [ 0. -1.  0.]
 [ 1. -1.  0.]
 [ 1. -2.  0.]],
\tnormal=[0. 0. 1.]
\tpolygon=POLYGON Z ((0 -2 0, 0 -1 0, 1 -1 0, 1 -2 0, 0 -2 0))
\tindex=8
)''',
    '''Face(
\tvertices=\\
[[ 0. -1.  0.]
 [ 0.  0.  0.]
 [ 1.  0.  0.]
 [ 1. -1.  0.]],
\tnormal=[0. 0. 1.]
\tpolygon=POLYGON Z ((0 -1 0, 0 0 0, 1 0 0, 1 -1 0, 0 -1 0))
\tindex=9
)''',
    '''Face(
\tvertices=\\
[[0. 0. 0.]
 [0. 1. 0.]
 [1. 1. 0.]
 [1. 0. 0.]],
\tnormal=[0. 0. 1.]
\tpolygon=POLYGON Z ((0 0 0, 0 1 0, 1 1 0, 1 0 0, 0 0 0))
\tindex=10
)''',
    '''Face(
\tvertices=\\
[[0. 1. 0.]
 [0. 2. 0.]
 [1. 2. 0.]
 [1. 1. 0.]],
\tnormal=[0. 0. 1.]
\tpolygon=POLYGON Z ((0 1 0, 0 2 0, 1 2 0, 1 1 0, 0 1 0))
\tindex=11
)''',
    '''Face(
\tvertices=\\
[[ 1. -2.  0.]
 [ 1. -1.  0.]
 [ 2. -1.  0.]
 [ 2. -2.  0.]],
\tnormal=[0. 0. 1.]
\tpolygon=POLYGON Z ((1 -2 0, 1 -1 0, 2 -1 0, 2 -2 0, 1 -2 0))
\tindex=12
)''',
    '''Face(
\tvertices=\\
[[ 1. -1.  0.]
 [ 1.  0.  0.]
 [ 2.  0.  0.]
 [ 2. -1.  0.]],
\tnormal=[0. 0. 1.]
\tpolygon=POLYGON Z ((1 -1 0, 1 0 0, 2 0 0, 2 -1 0, 1 -1 0))
\tindex=13
)''',
    '''Face(
\tvertices=\\
[[1. 0. 0.]
 [1. 1. 0.]
 [2. 1. 0.]
 [2. 0. 0.]],
\tnormal=[0. 0. 1.]
\tpolygon=POLYGON Z ((1 0 0, 1 1 0, 2 1 0, 2 0 0, 1 0 0))
\tindex=14
)''',
    '''Face(
\tvertices=\\
[[1. 1. 0.]
 [1. 2. 0.]
 [2. 2. 0.]
 [2. 1. 0.]],
\tnormal=[0. 0. 1.]
\tpolygon=POLYGON Z ((1 1 0, 1 2 0, 2 2 0, 2 1 0, 1 1 0))
\tindex=15
)'''
]
