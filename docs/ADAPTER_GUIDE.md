# Adapting the project to another printer

This repository verifies one runtime target: a Creality K2. Moonraker is common
across several printer stacks, but the object names, fan mapping, camera routes,
limits, and safe actions are not guaranteed to match.

## Start from evidence

With write access disabled, request the printer objects you want to use and
save a sanitized response. Remove local addresses, filenames, history, camera
data, and every identifying value before sharing it.

Check these areas first:

| Need | K2 source used here | What may differ elsewhere |
| --- | --- | --- |
| Print state | `print_stats` | State labels and extra fields. |
| Progress and layer | `virtual_sdcard` | Some machines use different progress sources. |
| Model fan | `output_pin fan0` | Other printers may expose `fan`, another pin, or no fan. |
| Side fan | `output_pin fan2` | May not exist. |
| Camera | Three K2 routes | Port and endpoint commonly differ. |
| Profiles | Creality Print K2 profile folders | Vendor and file structure differ. |

## Add a profile, not a claim

Create a profile class that declares the exact object names it needs and maps
only fields observed on that printer. Keep missing values as `null`. Do not
fall back to a similar-looking field without a test from the target machine.

Add tests using a sanitized object fixture. Test proxy-free local transport,
read-only status, the fan mapping, and every bound on every physical action.
Document the model and firmware context under a compatibility entry marked
verified only after live read-only testing.

## Choose safety limits per machine

Nozzle, bed, speed, fan, cancellation behavior, and file upload behavior are
hardware-specific. Do not copy K2 values into another machine without checking
its documentation and a safe local test. A new adapter must start with write
access disabled.
