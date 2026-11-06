"""Resolve local paths and SMB URLs using existing mounts; standard library only."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SmbLocation:
    host: str
    share: str
    parts: tuple[str, ...] = ()
    user: str = ""
    port: int = 445

    @property
    def uri(self):
        from urllib.parse import quote
        host = f"[{self.host}]" if ':' in self.host else self.host
        authority = (quote(self.user, safe=';') + '@' if self.user else '') + host
        if self.port != 445:
            authority += f":{self.port}"
        return 'smb://' + authority + '/' + '/'.join(
            quote(part, safe='') for part in (self.share, *self.parts))


def parse_smb(value):
    from urllib.parse import unquote, urlsplit
    parsed = urlsplit(str(value))
    if parsed.scheme.lower() != 'smb' or not parsed.hostname:
        raise ValueError("Expected smb://[user@]server/share/folder")
    if parsed.password is not None:
        raise ValueError("Use the existing logged-in share; omit passwords from SMB URLs.")
    if parsed.query or parsed.fragment:
        raise ValueError("Encode literal ? or # in SMB folder names as %3F or %23.")
    parts = tuple(unquote(part) for part in parsed.path.split('/') if part)
    user = unquote(parsed.username or '')
    if not parts or any(part in ('.', '..') or any(c in part for c in ('/', '\\', '\0')) for part in parts):
        raise ValueError("SMB URLs need a share name and cannot contain . or .. path components.")
    if '\0' in user or any(c in parsed.hostname for c in ('/', '\\', '\0')):
        raise ValueError("Invalid SMB server or user")
    port = parsed.port or 445
    return SmbLocation(parsed.hostname.lower(), parts[0].lower(), parts[1:], user, port)


def _unescape_mount(value):
    # mountinfo escapes whitespace and backslashes as octal sequences.
    import re
    return re.sub(r'\\([0-7]{3})', lambda match: chr(int(match[1], 8)), value)


def linux_smb_mounts(mountinfo=None):
    """Yield (remote root, native mountpoint), including CIFS subdirectory binds."""
    from pathlib import Path
    mountinfo = Path('/proc/self/mountinfo') if mountinfo is None else mountinfo
    try:
        lines = Path(mountinfo).read_text().splitlines()
    except OSError:
        return
    for line in lines:
        try:
            before, after = line.split(' - ', 1)
            fields, fs = before.split(), after.split()
            if fs[0] not in ('cifs', 'smb3') or not fs[1].startswith('//'):
                continue
            options = dict(option.split('=', 1) for option in fs[2].split(',') if '=' in option)
            # These are filesystem paths, not URLs: quote literal %, #, spaces.
            source = _unescape_mount(fs[1])
            host, share, *prefix = source[2:].split('/')
            bind = tuple(part for part in _unescape_mount(fields[3]).split('/') if part)
            if not prefix and options.get('prefixpath'):
                prefix = _unescape_mount(options['prefixpath']).strip('/').split('/')
            remote = SmbLocation(host.lower(), share.lower(), tuple(p for p in prefix if p) + bind,
                                 _unescape_mount(options.get('username', '')),
                                 int(options.get('port', 445)))
            yield remote, Path(_unescape_mount(fields[4]))
        except (ValueError, IndexError):
            continue


def gvfs_roots():
    import os
    from pathlib import Path
    runtime = os.environ.get('XDG_RUNTIME_DIR')
    roots = [Path(runtime) / 'gvfs'] if runtime else []
    if hasattr(os, 'getuid'):
        roots.append(Path('/run/user') / str(os.getuid()) / 'gvfs')
    roots.append(Path.home() / '.gvfs')
    return dict.fromkeys(roots)


def gvfs_smb_mounts():
    from urllib.parse import unquote
    for root in gvfs_roots():
        try:
            entries = list(root.iterdir())
        except OSError:
            continue
        for entry in entries:
            if not entry.name.startswith('smb-share:'):
                continue
            try:
                options = dict(part.split('=', 1) for part in entry.name[len('smb-share:'):].split(','))
                remote = SmbLocation(unquote(options['server']).lower(), unquote(options['share']).lower(),
                                     user=unquote(options.get('user', '')), port=int(options.get('port', 445)))
                yield remote, entry
            except (KeyError, ValueError):
                continue


def kio_fuse_roots(mountinfo=None):
    """Discover KIOFuse without depending on its changing per-session suffix."""
    import os
    from pathlib import Path
    mountinfo = Path('/proc/self/mountinfo') if mountinfo is None else mountinfo
    roots = []
    try:
        for line in Path(mountinfo).read_text().splitlines():
            before, after = line.split(' - ', 1)
            fs = after.split()
            if fs[0] == 'fuse.kio-fuse' or (fs[0] == 'fuse' and fs[1] == 'kio-fuse'):
                roots.append(Path(_unescape_mount(before.split()[4])))
    except (OSError, ValueError, IndexError):
        pass
    runtime = os.environ.get('XDG_RUNTIME_DIR')
    runtimes = [Path(runtime)] if runtime else []
    if hasattr(os, 'getuid'):
        runtimes.append(Path('/run/user') / str(os.getuid()))
    for directory in dict.fromkeys(runtimes):
        try:
            roots.extend(directory.glob('kio-fuse-*'))
        except OSError:
            continue
    return dict.fromkeys(roots)


def kio_smb_mounts(target):
    from urllib.parse import quote
    # KIOFuse uses smb/[user@]host/share/path, unlike GVfs's smb-share:... .
    # Enumerate only existing local origin nodes, not the remote server's
    # shares or library. Only the requested server/share is ever checked.
    for root in kio_fuse_roots():
        try:
            servers = list((root / 'smb').iterdir())
        except OSError:
            continue
        for server in servers:
            try:
                remote = parse_smb('smb://' + server.name + '/' + quote(target.share, safe=''))
                if _matches(target, remote):
                    yield remote, server / target.share
            except ValueError:
                continue


def mounted_smb_locations(target=None):
    yield from linux_smb_mounts()
    yield from gvfs_smb_mounts()
    if target is not None:
        yield from kio_smb_mounts(target)


def _matches(target, mounted):
    return (target.host == mounted.host and target.share == mounted.share
            and target.port == mounted.port
            and (not target.user or not mounted.user or target.user.casefold() == mounted.user.casefold())
            and target.parts[:len(mounted.parts)] == mounted.parts)


def resolve_file_location(value, mount_path=None, *, require_directory=False):
    """Return (native Path, stable SMB URI or None) for an existing location.

    Accepts local files/directories, native network paths, and SMB URLs. On
    Linux, existing CIFS, GVfs and KIOFuse mounts are detected. On Windows, SMB
    URLs map to native UNC paths using the current operating-system session.
    mount_path explicitly maps the whole supplied URL to a native path; this
    also supports macOS and mount systems not automatically discovered.

    require_directory=True rejects files (useful for collection scan roots).
    No shell interpolation, mounting, credential lookup, DNS or SMB client is used.
    """
    import os
    from pathlib import Path
    def accessible(path):
        return path.is_dir() if require_directory else path.exists()
    kind = 'directory' if require_directory else 'file or directory'
    raw = os.fspath(value)
    if not raw.lower().startswith('smb:'):
        if mount_path is not None:
            raise ValueError("mount_path is only used with an SMB URL.")
        if '://' in raw:
            raise ValueError("Use a local path, mounted network path, or smb:// URL.")
        path = Path(raw).expanduser().resolve()
        if not accessible(path):
            raise ValueError(f"Not an accessible {kind}: {path}")
        return path, None
    target = parse_smb(raw)
    if mount_path is not None:
        path = Path(mount_path).expanduser().resolve()
        if not accessible(path):
            raise ValueError(f"mount_path is not an accessible {kind}: {path}")
        return path, target.uri
    if os.name == 'nt':
        if target.port != 445:
            raise ValueError("Use mount_path for SMB URLs with a custom port on Windows.")
        path = Path('\\\\' + target.host + '\\' + '\\'.join((target.share, *target.parts)))
        if accessible(path):
            return path.resolve(), target.uri
    else:
        candidates = sorted((pair for pair in mounted_smb_locations(target) if _matches(target, pair[0])),
                            key=lambda pair: len(pair[0].parts), reverse=True)
        # Prefer the most specific mount; a nested bind may be the only visible path.
        for remote, mount in candidates:
            path = (mount / Path(*target.parts[len(remote.parts):])).resolve()
            if accessible(path):
                return path, target.uri
    raise ValueError(
        "No accessible existing mount matches this SMB location. Run from the same user/session "
        "that opened the share, or supply mount_path (CLI: --mount-path) pointing to the "
        "complete already-mounted target path, not just the share root.")


def resolve_location(value, mount_path=None):
    """Directory-only alias retained for existing collection-scanner callers."""
    return resolve_file_location(value, mount_path, require_directory=True)
