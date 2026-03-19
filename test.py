from src.core_cac.treeList_upserter import TreeListUpserter

items = [
    {"sys_type": "POINT", "value": {"sys_name":"POINT1", "k1": "v1", "k2": "v2"}},
    {"sys_type": "LINE",  "value": {"sys_name":"LINE1",  "k3": "v3", "k4": "v4"}},
    {"sys_type": "MESH",  "value": {"sys_name":"MESH1",  "k7": "v7", "k8": "v8"}},
    {"sys_type": "PORT",  "value": {"sys_name":"PORT1",  "k5": "v5", "k6": "v6"}}
]

tree = {
    "Geometry": {
        "POINT": [],
        "LINE": []
    },
    "MESH": [],
    "boundary": {
        "PORT": []
    }
}

inserter = TreeListUpserter()
inserter.upsert_many(tree, items)

print(tree)

print(inserter.list_tags(tree))
