#!/usr/bin/env bash
# Create or update the FusionSpace issue labels in a repo: ./apply-labels.sh owner/repo   (needs the GitHub CLI, gh)
set -euo pipefail
REPO="$1"
gh label create "bug" --repo "$REPO" --color B34F0C --description "Something is broken" --force
gh label create "feature" --repo "$REPO" --color 3350D6 --description "New capability" --force
gh label create "enhancement" --repo "$REPO" --color 768DF5 --description "Improve something that works" --force
gh label create "docs" --repo "$REPO" --color A188CB --description "Documentation" --force
gh label create "hardware" --repo "$REPO" --color DA7C30 --description "PCBs, wiring, mechanical, machining" --force
gh label create "firmware" --repo "$REPO" --color D07D7A --description "Embedded and flight software" --force
gh label create "test" --repo "$REPO" --color 566079 --description "Tests, verification, CI" --force
gh label create "question" --repo "$REPO" --color 98A1B8 --description "Needs an answer" --force
gh label create "blocked" --repo "$REPO" --color 0B0F1C --description "Waiting on something else" --force
gh label create "good first issue" --repo "$REPO" --color D6DAE4 --description "Small and well-scoped" --force
gh label create "wontfix" --repo "$REPO" --color 2A3248 --description "Decided against" --force
