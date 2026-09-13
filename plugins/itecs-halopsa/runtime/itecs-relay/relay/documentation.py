"""Select verified client documentation and describe its Codex read permissions."""

import json
from pathlib import Path


def documentation_roots(config, ticket):
    root = Path(config["documentation_root"]).resolve(strict=True)
    clients = root / "clients"
    if not clients.resolve().is_relative_to(root):
        raise ValueError("documentation clients directory escapes documentation_root")
    scopes = []
    shared = clients / "_global-kb"
    if shared.is_dir():
        if shared.resolve() != clients.resolve() / "_global-kb":
            raise ValueError("shared documentation directory redirects to another scope")
        scopes.append(shared.resolve())
    mapping = config.get("documentation_clients", {})
    key = str(ticket.get("client_id"))
    if key in mapping:
        slug = mapping[key]
        if not isinstance(slug, str) or not slug or slug in (".", "..") or Path(slug).name != slug:
            raise ValueError("documentation client mapping must name one directory")
        client = (clients / slug).resolve(strict=True)
        if client != clients.resolve() / slug:
            raise ValueError("client documentation directory redirects to another scope")
        if not client.is_dir():
            raise ValueError("mapped client documentation is not a directory")
        scopes.append(client)
    if any(not path.is_relative_to(clients.resolve()) for path in scopes):
        raise ValueError("documentation scope escapes the clients directory")
    return scopes


def permission_arguments(config, ticket):
    filesystem = {":root": "deny", ":minimal": "read",
                  str(Path(config["skill_path"]).resolve(strict=True)): "read"}
    filesystem.update({str(path): "read" for path in documentation_roots(config, ticket)})
    fields = ", ".join(json.dumps(key) + " = " + json.dumps(value)
                       for key, value in filesystem.items())
    return ["-c", 'default_permissions="relay-client"',
            "-c", "permissions.relay-client.filesystem={" + fields + "}",
            "-c", "permissions.relay-client.network.enabled=false",
            "-c", "approval_policy=\"never\"", "-c", "allow_login_shell=false",
            "-c", "project_doc_max_bytes=0", "-c", "features.memories=false",
            "-c", "features.skip_host_skill_discovery=true", "-c", 'web_search="disabled"']
