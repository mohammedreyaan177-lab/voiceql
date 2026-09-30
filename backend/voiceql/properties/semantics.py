SEMANTIC_MODEL = {
    "sales" : {
        "table" : "public.voiceql_sales",

        "dimensions" : {
            "product_id"  : {
                "column" : "id",
                "description" : "Unique ID for each product"
            },


            "product_name" : {
                "column" : "products",
                "description" : "Name of the product"
            },


            "product_price" : {
                "column" : "price",
                "description" : "Price of the product"
            }
        }

    }
}