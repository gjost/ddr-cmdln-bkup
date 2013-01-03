ddr-cmdln
=========

Command-line tools for automating the DDR's various processes.

* kura -- Tools for creating and manipulating repository objects.
* kiroku -- Generates unique identifiers for repository objects.
* validator -- Checks repository objects for compliance with the manual.
* capsule -- Provides a RESTful interface to some/all of the above.


Philosophy
----------

* It should be possible to do all DDR operations using only command line tools.
* Each tool should be able to output in parseable formats (text, JSON, YAML).
* As many of the tools as possible should be exposed through a REST interface.
