# v1.1.0 (2020-05-07)

This release adds new analysis operators, as well as some bugfixes and minor
changes.

### New analysis operations

* Add GraphFrame reindex operator
* Query hatchet module version

### Changes to existing APIs changes

* Add depth parameter to tree printout

### Bugfixes

* Fix pandas SettingwithCopyWarning in unify's _missing_nodes
* Handle MultiIndex for pandas 1.0.0 and newer vs older pandas versions

# v1.0.1 (2020-03-11)

This release adds a new division operator and graph markups, as well as
bugfixes and minor changes.

### New analysis operations

* Add markups to identify nodes that exist in only one of two graphs (from unify)
* Add GraphFrame division operator

### Changes to existing APIs

* Add precision parameter (of metrics) in tree printout
* Tree printout to show nodes with negative values higher than threshold

### Bugfixes

* Fix HPCToolkit reader bug for statement nodes
* Downgrade pandas version for python 3.6 and later (incompatible versions)
* Fix unify by adding missing rows for math operations on GraphFrames
* Fix squash by restoring index in self's dataframe
* Do not sort nodes by frame in Graph union
* Fix phase timer to aggregate times for duplicate phases
* Remove node callpath calculation from HPCToolkit reader
* Remove unnecessary setting of _hatchet_nid in dataframe

# v1.0.0 (2019-11-18)

`v1.0.0` marks the first release of Hatchet!

### Analysis operations

* File formats supported: HPCToolkit, Caliper, DOT, string literal, list
* Graph visualization formats: terminal output, DOT, flamegraph
* Analysis operations: filter, squash, add, subtract, unify, copy

### Testing and Documentation

* Hatchet added to PyPI repository
* Unit tests using `pytest`
* Initial documentation on [hatchet.readthedocs.io](http://hatchet.readthedocs.io)
