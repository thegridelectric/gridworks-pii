"""gwpii: the GridWorks private customer store.

The only place a person is linked to a house. Every record hangs off the
house's TerminalAsset GNodeId; nothing else in the system names a
customer. The shapes here never become sema words: their instances never
travel on the wire, never enter the persistent store, and are never
published. The store is private data held by the party that owns it, with
deletability and access control instead of immutability.
"""
