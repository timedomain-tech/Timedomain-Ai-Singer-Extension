import os

import omni.client

A2F_SERVER_TYPE = "omniverse:"


def is_ov_path(path):
    return A2F_SERVER_TYPE in path


def path_join(root, fname):
    if A2F_SERVER_TYPE in root:
        return f"{root}/{fname}"
    else:
        return os.path.normpath(os.path.join(root, fname))


def is_folder(path):
    result, entry = omni.client.stat(path)
    # bitewise operation, folder flags is 4
    return entry.flags & omni.client.ItemFlags.CAN_HAVE_CHILDREN


def is_valid_path(path):
    result, entry = omni.client.stat(path)
    return result == omni.client.Result.OK


def list_folder(path):
    items = []
    path = path.rstrip("/")
    result, entries = omni.client.list(path)
    if result != omni.client.Result.OK:
        return items
    for en in entries:
        # Skip if it is a folder
        if en.flags & omni.client.ItemFlags.CAN_HAVE_CHILDREN:
            continue
        name = en.relative_path
        items.append(name)
    return items


def read_file(fpath):
    result, _str, bytes_data = omni.client.read_file(fpath)
    if result != omni.client.Result.OK:
        raise RuntimeError("Unable to read file: {}".format(fpath))
    return bytes_data


def write_file(fpath, bytes_data):
    result = omni.client.write_file(fpath, bytes_data)
    if result != omni.client.Result.OK:
        raise RuntimeError("Unable to write file: {}".format(fpath))
