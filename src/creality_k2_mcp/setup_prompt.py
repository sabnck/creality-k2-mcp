"""A paste-ready setup prompt for people who do not write code."""

SETUP_PROMPT = """You are helping me connect a local Creality printer to an MCP client.

Ask for the printer model and its local network address. Do not enable any
physical control by default. First verify only read-only status access. Explain
each configuration value in plain language, generate the client configuration,
then ask me to restart the client and test printer status. Offer write controls
only after I explicitly say I want them, and make me confirm that I understand
they can affect a real printer.
"""
