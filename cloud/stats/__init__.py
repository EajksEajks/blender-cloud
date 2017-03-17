"""Interesting usage metrics"""

from flask import current_app

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


def count_nodes(query=None) -> int:
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
