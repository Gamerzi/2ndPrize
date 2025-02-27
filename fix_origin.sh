#!/bin/bash

git filter-branch --force --tree-filter 'for f in $(git ls-files); do sed -i "s/AC[A-Za-z0-9]\{32\}/REMOVED/g; sed -i "s/hf_[A-Za-z0-9]\{40\}/REMOVED/g" "$f"; done' -- --all
