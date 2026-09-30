METRICS = {
    "total_products" : {
        "field" : "product_id",
        "aggregation" : "COUNT",
        "description" : "Provides count of all the products"
    },

    "max_price" : {
        "field" : "price",
        "aggregation" : "MAX",
        "description" : "Provides the maximum price"
    }


}