import sys
import builtins

original_import = builtins.__import__

def custom_import(name, globals=None, locals=None, fromlist=(), level=0):
    print(f"Importing {name} ...", flush=True)
    res = original_import(name, globals, locals, fromlist, level)
    return res

builtins.__import__ = custom_import

print("Starting debug import", flush=True)
import main
print("Finished importing main", flush=True)
