# Architecture

Grok Bot (xAI, Aug 2026) sells a finished teammate on a persistent cloud VM. Multiple named Bots share that VM: files, browser sessions, logins. Each Bot gets a screen, not a security boundary.

Hermes Bot Mode (Nous, Aug 2026) sells the parts. A Bot is a profile at `~/.hermes/profiles/<name>/` with its own SOUL.md, memory, skills, credentials, and chat.

This repo maps the factory onto Hermes primitives and fakes the shared computer with a workspace directory.

Human gate: awaiting_human. Packaging requires APPROVE:<job_id>:<account>. press cannot set auto_post true.
