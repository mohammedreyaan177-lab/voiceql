from django.db import connection
from ..properties.metrics import METRICS
from ..properties.semantics import SEMANTIC_MODEL


#Calculate Metric Function:

def calculate_metric(metric_name):

    metric = METRICS[metric_name]

    field_name = metric['field']
    aggregation = metric['aggregation']
    table = SEMANTIC_MODEL["sales"]["table"]

    if field_name not in SEMANTIC_MODEL["sales"]["dimensions"]:
        raise ValueError(f"The field {field_name} does not exist in SEMANTIC_MODEL")


    column = SEMANTIC_MODEL["sales"]["dimensions"][field_name]["column"]



    query = f"""
    SELECT {aggregation}({column}) FROM {table}
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchone()

    return results[0]


def find_metric(user_query):

    user_query = user_query.lower()

    if "total products" in user_query:
        return "total_products"

    if "number of products" in user_query:
        return "total_products"

    if "count of products" in user_query:
        return "total_products"

    if "how many products" in user_query:
        return "total_products"

    if "maximum price" in user_query:
        return "max_price"

    if "max price" in user_query:
        return "max_price"

    if "highest price" in user_query:
        return "max_price"

    if "lowest price" in user_query:
        return "min_price"

    if "low price" in user_query:
        return "min_price"

    if "smallest price" in user_query:
        return "min_price"

    if "minimum product price" in user_query:
        return "min_price"

    if "lowest product price" in user_query:
        return "min_price"

    if "average" in user_query:
        return "average_price"


    if "average price" in user_query:
        return "average_price"


    if "total_cost" in user_query:
        return "total_cost"

    if "total" in user_query:
        return "total_cost"

    if "full cost" in user_query:
        return "full_cost"

    if "sum cost" in user_query:
        return "sum_cost"


    return None
