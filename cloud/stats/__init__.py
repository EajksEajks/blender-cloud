"""Interesting usage metrics"""

from flask import current_app


def count_nodes(query=None) -> int:
    pipeline = [
        {'$match': {'_deleted': {'$ne': 'true'}}},
        {
            '$lookup':
                {
                    'from': "projects",
                    'localField': "project",
                    'foreignField': "_id",
                    'as': "project",
                }
        },
        {
            '$unwind':
                {
                    'path': '$project',
                }
        },
        {
            '$project':
                {
                    'p.is_private': 1,
                }
        },
        {'$match': {'p.is_private': {'$ne': True}}},
        {'$count': 'tot'}
    ]
    c = current_app.db()['nodes']
    # If we provide a query, we extend the first $match step in the aggregation pipeline with
    # with the extra parameters (for example node_type)
    if query:
        pipeline[0]['$match'].update(query)
    # Return either a list with one item or an empty list
    r = list(c.aggregate(pipeline=pipeline))
    count = 0 if not r else r[0]['tot']
    return count


def count_users() -> int:
    u = current_app.db()['users']
    return u.count()


def count_blender_sync() -> int:
    pipeline = [
        # 0 Find all startups.blend that are not deleted
        {
            '$match': {
                '_deleted': {'$ne': 'true'},
                'name': 'startup.blend',
            }
        },
        # 1 Group them per project (drops any duplicates)
        {'$group': {'_id': '$project'}},
        # 2 Join the project info
        {
            '$lookup':
                {
                    'from': "projects",
                    'localField': "_id",
                    'foreignField': "_id",
                    'as': "project",
                }
        },
        # 3 Unwind the project list (there is always only one project)
        {
            '$unwind':
                {
                    'path': '$project',
                }
        },
        # 4 Find all home projects
        {'$match': {'project.category': 'home'}},
        {'$count': 'tot'}
    ]
    c = current_app.db()['nodes']
    # Return either a list with one item or an empty list
    r = list(c.aggregate(pipeline=pipeline))
    count = 0 if not r else r[0]['tot']
    return count
