import json
import logging
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    payload = req.get_json()
    batch_id = str(payload.get("batch_id", "unknown"))
    rows = int(payload.get("rows", 0))
    source = str(payload.get("source", "scheduled"))

    logging.info(
        "DataOps batch received | batch_id=%s source=%s rows=%d",
        batch_id,
        source,
        rows,
    )

    if rows > 50000:


        raise RuntimeError("memory pressure detected on large batch")



    processed_rows = rows

    result = {
        "status": "ok",
        "batch_id": batch_id,
        "source": source,
        "processed_rows": processed_rows,
    }

    logging.info(
        "DataOps batch processed | batch_id=%s processed_rows=%d",
        batch_id,
        processed_rows,
    )

    return func.HttpResponse(
        json.dumps(result),
        status_code=200,
        mimetype="application/json",
    )
