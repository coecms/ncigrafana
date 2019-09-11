ncigrafana
==========

Extended usage information for the NCI system raijin.

.. image:: https://travis-ci.org/coecms/ncigrafana.svg?branch=master
   :target: https://travis-ci.org/coecms/ncigrafana
.. image:: https://circleci.com/gh/coecms/ncigrafana.svg?style=shield
  :target: https://circleci.com/gh/coecms/ncigrafana

This repository contains programs to parse the output of NCI resource
monitoring programs and upload usage statistics to the grafana postgres 
database.

There are two main programs, ``parse_account_usage_data`` which parses the output
from ``nci_account``, and ``parse_user_storage_data`` which parses the output from
the programs that report usage on the various file systems, e.g. ``gdata3_files_report``.
