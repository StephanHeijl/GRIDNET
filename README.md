GRIDNET
=======
Repository for the GRIDNET cluster interaction project.

==About GRIDNET==
GRIDNET is a Python-driven utility that allows grid computing networks to communicate
with each other through GRIDNET servers. it consists of two separate modules, both
cross-platform and written in Python. In principle GRIDNET is grid-software agnostic,
but currently only Condor networks are supported through CondorMasterRequestHandler.

* MasterRequestHandler serves as an interface between the grid and the servers.
* The GRIDNET interface is deployed on HAN's Cytosine.nl Server and serves as an
interface between the grids and the user.
