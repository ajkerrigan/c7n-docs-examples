# Cloud Custodian Example Policies

## Overview

This repository contains example Cloud Custodian policies extracted from
the [official documentation](https://cloudcustodian.io/docs/).

The Cloud Custodian documentation has many example policies embedded inside
reStructuredText code blocks. A script in this repo walks a parent directory
in search of example documentation, and extracts valid policies from code blocks.

Extracted policies are written to a path under the current directory,
derived from the name of the policy and its location in the documentation.

## Usage

The script can be run from a Python environment with Cloud Custodian
[installed](https://cloudcustodian.io/docs/developer/installing.html#developer-installing).

```bash
$ python extract_example_policies.py /path/to/cloud-custodian/docs/source
```
