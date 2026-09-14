# Safety model

This server connects to a physical machine. Read-only access is the default and
is the recommended normal mode.

## Read-only mode

`K2_ALLOW_WRITE=0` is the default. In this mode the server can inspect printer
status, camera evidence, history, logs, local models, G-code, and local slicer
profiles. It refuses every action that would change the printer or upload a
file.

## Write mode

`K2_ALLOW_WRITE=1` is a conscious local choice. It enables only named actions:
pause, resume, cancel with confirmation, bounded temperature changes, bounded
speed changes, and model fan adjustment.

It does not expose G-code upload or a general-purpose G-code tool. Before the
first physical action, it also verifies the K2 object capabilities through a
read-only query.

## Before enabling write access

1. Confirm the printer address belongs to your own local network.
2. Test read-only status and camera access first.
3. Be physically able to inspect or stop the printer.
4. Check the selected nozzle, filament, build plate, and project settings.
5. Enable write access only for the client and session you trust.

## What not to publish

Never commit or post `.env` files, local addresses, printer histories, camera
images, G-code, 3MF files, models, custom profiles, screenshots, or tokens.
Run `python scripts/audit_public_release.py` before creating a public release.
