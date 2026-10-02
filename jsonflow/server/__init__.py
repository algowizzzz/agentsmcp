"""jsonflow web product: builder UI, run history, admin, and an MCP endpoint
that exposes published agents as tools.

Two roles only:
  admin        builds, edits, runs and publishes agents; sees all runs
  super_admin  everything an admin can do, plus users, categories, MCP
               servers, LLM settings, API keys and the audit log
"""
