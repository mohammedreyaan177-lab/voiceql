METRICS = {
    "total_products": {
        "field": "product_id",
        "aggregation": "COUNT",
        "description": "Provides count of all the products",
        "keywords": [
            "total products",
            "number of products",
            "count of products",
            "how many products",
            "product count"
        ]
    },

    "max_price": {
        "field": "product_price",
        "aggregation": "MAX",
        "description": "Provides the maximum price",
        "keywords": [
            "maximum price",
            "max price",
            "highest price",
            "most expensive",
            "maximum product price",
            "highest product price"
        ]
    },

    "min_price": {
        "field": "product_price",
        "aggregation": "MIN",
        "description": "Provides the minimum price",
        "keywords": [
            "minimum price",
            "min price",
            "lowest price",
            "smallest price",
            "minimum product price",
            "lowest product price"
        ]
    },


    "avg_price": {
        "field": "product_price",
        "aggregation": "AVG",
        "description": "Provides the average price",
        "keywords": [
            "average price",
            "average"
        ]
    },

    "total_cost": {
        "field": "product_price",
        "aggregation": "SUM",
        "description": "Provides the total cost",
        "keywords": [
            "total cost",
            "total",
            "full cost",
            "sum cost"
        ]
    }
}