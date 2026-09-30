METRICS = {
    "total_products": {
        "field": "product_id",
        "aggregation": "COUNT",
        "description": "Count the total number of products"
    },

    "max_price": {
        "field": "product_price",
        "aggregation": "MAX",
        "description": "Find the highest or maximum product price"
    },

    "min_price": {
        "field": "product_price",
        "aggregation": "MIN",
        "description": "Find the lowest or minimum product price"
    },

    "avg_price": {
        "field": "product_price",
        "aggregation": "AVG",
        "description": "Find the average or mean product price"
    },

    "total_cost": {
        "field": "product_price",
        "aggregation": "SUM",
        "description": "Calculate the combined or total price of all products"
    }
}