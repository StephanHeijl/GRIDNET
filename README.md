GRIDNET
=======
Repository for the GRIDNET cluster interaction project.

About GRIDNET
-------------
GRIDNET is a Python-driven utility that allows grid computing networks to communicate
with each other through GRIDNET servers. it consists of three separate modules, all
cross-platform and written in Python. In principle GRIDNET is grid-software agnostic,
but currently only Condor networks are supported through CondorMasterRequestHandler
and PyCondor.

* PyCondor interfaces with Condor grid software in order to generate appropiate
submit files, manage and monitor jobs.
* MasterRequestHandler serves as an interface between the grid and the servers.
* The GRIDNET interface is deployed on HAN's Cytosine.nl Server and serves as an
interface between the grids and the user.

Author/ownership information
----------------------------
GRIDNET is being developed by Stephan Heijl and is owned by the BioCOMP project.
Currently all GRIDNET software is released under the MIT license, except where noted
otherwise. Code contributed by others is denoted as such.