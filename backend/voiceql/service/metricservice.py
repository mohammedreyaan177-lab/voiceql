from django.db import connection
from ..properties.metrics import METRICS
from ..properties.semantics import SEMANTIC_MODEL


#Calculate Metric Function:

def calculate_metric(metric_name):

    metric = METRICS[metric_name]

    field_name = metric['field_name']
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
