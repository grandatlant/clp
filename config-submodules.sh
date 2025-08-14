#!/bin/sh
git config submodule.recurse true
git config push.recurseSubmodules on-demand
git config status.submodulesummary 1

