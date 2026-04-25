import os
import json
import tempfile
import hashlib
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.constructor.ignore_aliases = True


def _str_constructor(loader, node):
    if node.tag == 'tag:yaml.org,2002:bool' and node.value == 'y':
        return 'y'
    return loader.construct_scalar(node)


# Prevent yaml from parsing "y" as True
yaml.constructor.add_constructor('tag:yaml.org,2002:bool', _str_constructor)

temp_folder_path = os.path.join(tempfile.gettempdir(), 'unity_animation_player_python')
os.makedirs(temp_folder_path, exist_ok=True)


def _get_file_sha256(file_path):
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read file in chunks to avoid memory issues with large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None


def _save_cache_metadata(json_path, sha256_hash):
    metadata_path = json_path + '.metadata'
    try:
        with open(metadata_path, 'w') as f:
            json.dump({'sha256': sha256_hash}, f)
    except Exception as e:
        print(f"[Warning]Failed to save cache metadata: {e}")


def _load_cache_metadata(json_path):
    metadata_path = json_path + '.metadata'
    try:
        with open(metadata_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def load_yaml(path: str, cache=True):
    json_path = os.path.join(temp_folder_path, path.rsplit('.', 1)[0] + '.json')

    source_sha256 = _get_file_sha256(path)
    if source_sha256 is None:
        raise FileNotFoundError(f"Source file not found: {path}")

    try:
        metadata = _load_cache_metadata(json_path)

        if (metadata and
            metadata.get('sha256') == source_sha256 and
            os.path.exists(json_path)):

            # Cache is valid
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"[DEBUG]Loaded cached data for: {path}")
            return data
        else:
            # Cache is invalid
            print(f"[WARNING]Cache invalid or missing, regenerating for: {path}")
            raise FileNotFoundError("Cache needs regeneration")

    except (FileNotFoundError, json.JSONDecodeError):
        # regenerate
        with open(path, 'r', encoding='utf-8') as y:
            data = yaml.load(y)

        if cache:
            os.makedirs(os.path.dirname(json_path), exist_ok=True)

            with open(json_path, 'w', encoding='utf-8') as j:
                json_data = json.dumps(data, ensure_ascii=False, indent=2)
                j.write(json_data)

            _save_cache_metadata(json_path, source_sha256)
            print(f"[DEBUG]Cached data regenerated for: {path}")

        return json.loads(json.dumps(data))