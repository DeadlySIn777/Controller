# Unpublished interrupted review build

The first builder run stopped after writing the MC native study because the KiCad Python track collection is a list, not an object exposing `.size()`. The builder was corrected to use `len()`. This partial directory was moved aside before a successful fresh `20260930-01` build. It has never been included in the published viewer's revision history. Do not use it as an engineering release.
