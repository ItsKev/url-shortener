import json
import logging
import os

import azure.functions as func

from additional_functions import (
    UrlItem,
    db_client,
    generate_short_code,
    validate_short_code,
    validate_url,
)

app = func.FunctionApp()


@app.route(route="shorten", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def shorten_url(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing URL shortening request")

    try:
        req_body = req.get_json()
        if not req_body or "url" not in req_body:
            return func.HttpResponse(
                json.dumps({"error": "Missing 'url' in request body"}),
                status_code=400,
                mimetype="application/json",
            )

        original_url = req_body["url"].strip()

        validation_error = validate_url(original_url)
        if validation_error:
            return func.HttpResponse(
                json.dumps({"error": validation_error}),
                status_code=400,
                mimetype="application/json",
            )

        while True:
            short_code = generate_short_code()

            try:
                if not db_client.check_short_code_exists(short_code):
                    break
            except Exception as e:
                logging.error(f"Error checking short code uniqueness: {str(e)}")
                return func.HttpResponse(
                    json.dumps({"error": "Database error while generating short code"}),
                    status_code=500,
                    mimetype="application/json",
                )

        db_client.create_url_item(
            UrlItem(id=short_code, short_code=short_code, original_url=original_url)
        )

        return func.HttpResponse(
            json.dumps(
                {
                    "short_code": short_code,
                    "original_url": original_url,
                    "short_url": f"{os.getenv('BASE_URL', 'http://localhost:7071')}/api/r/{short_code}",
                }
            ),
            status_code=201,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Error shortening URL: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


@app.route(route="r/{short_code}", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def redirect_url(req: func.HttpRequest) -> func.HttpResponse:
    logging.info(
        f'Processing redirect request for short code: {req.route_params.get("short_code", "unknown")}'
    )

    try:
        short_code = req.route_params.get("short_code")

        if not short_code:
            return func.HttpResponse("Short code not provided", status_code=400)

        validation_error = validate_short_code(short_code)
        if validation_error:
            return func.HttpResponse(validation_error, status_code=400)

        try:
            url_item = db_client.get_url_item(short_code)
            if url_item is None:
                return func.HttpResponse("Short URL not found", status_code=404)

            return func.HttpResponse(
                "", status_code=302, headers={"Location": url_item.original_url}
            )

        except Exception as e:
            logging.error(
                f"Error retrieving URL for short code '{short_code}': {str(e)}"
            )
            return func.HttpResponse("Database error", status_code=500)

    except Exception as e:
        logging.error(f"Error redirecting URL: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)
