import os
import logging
from django.db import connection
from groq import Groq
from dotenv import load_dotenv
from ..properties.metrics import METRICS
from ..properties.semantics import SEMANTIC_MODEL

load_dotenv()

logger = logging.getLogger("voiceql")


def find_metric(user_query):

    metrics = "\n".join(
        f"{name}: {metric['description']}"
        for name, metric in METRICS.items()
    )

    prompt = f"""
You are a metric classifier.

Available metrics:
{metrics}

User request:
{user_query}

Rules:
- Determine whether the user is asking for one of the available metrics.
- Understand the meaning of the user's request, not just exact keywords.
- Return only the metric name if the request is a metric request.
- If the request is not a metric request, return NONE.
- Do not create a new metric.
- Do not return any explanation.

Answer:
"""

    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        metric_name = response.choices[0].message.content.strip()

        metric_name = metric_name.replace("```", "").strip()

    except Exception as e:
        logger.error(f"Metric search failed: {e}")
        return None

    if metric_name not in METRICS:
        return None

    return metric_name


def calculate_metric(metric_name):
    try:
        metric = METRICS[metric_name]

        field_name = metric['field']
        aggregation = metric['aggregation']
        table = SEMANTIC_MODEL["sales"]["table"]

        if field_name not in SEMANTIC_MODEL["sales"]["dimensions"]:
            logger.error(f"Field {field_name} missing from SEMANTIC_MODEL")
            raise ValueError(f"The field {field_name} does not exist in SEMANTIC_MODEL")

        column = SEMANTIC_MODEL["sales"]["dimensions"][field_name]["column"]

        query = f"""
        SELECT {aggregation}({column}) FROM {table}
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchone()

        logger.info(f"Calculated metric: {metric_name}")
        return results[0]
    except Exception as e:
        logger.error(f"Metric calculation failed: {e}")
        raise