import pandas as pd

def build_aggregation_pipeline():
    return [
        {"$match": {"listeners": {"$gt": 0}}},
        {"$group": {"_id": "$source_collection", "avg_listeners": {"$avg": "$listeners"}}},
        {"$sort": {"avg_listeners": -1}},
        {"$project": {"source_collection": "$_id", "avg_listeners": 1, "_id": 0}}
    ]

def run_pipeline(collection, pipeline):
    return pd.DataFrame(list(collection.aggregate(pipeline)))
