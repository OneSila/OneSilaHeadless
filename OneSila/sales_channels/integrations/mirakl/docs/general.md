# Mirakl API – General Notes

## Backward compatibility information

Mirakl solutions are updated through continuous delivery to provide new features, security fixes, and bug fixes.

New deployed versions are backward compatible, which guarantees the durability of your integration after a Mirakl solution update, on condition that your integration follows these guidelines:

- Your integration must allow for new fields to be added in API responses. From time to time, we add new fields as part of new features.
- Do not expect fields to always have the same order in API calls. The order can change when fields are added to APIs.
- Your integration must allow for new values to be added in enumeration fields. We can add new values in enumeration fields to support new features.
- We advise that you use strings to deserialize enumeration fields. Alternatively, you can configure your deserializer to accept unknown enumeration values.
- While most of our APIs support XML format, we strongly advise you to use JSON format, as our newest APIs are only available in JSON format.

Should you decide to validate our APIs output using XSD files, please note:

- Your XSD should take into account the compatibility guidelines above.
- Mirakl does not provide XSD files for its APIs and does not offer support for writing XSD files.

## Undocumented attributes

Some APIs may return more data than indicated in the documentation. Do not rely on this undocumented data, because there is no guarantee about it.

## Authentication

You can authenticate through the API by sending your API key in the `Authorization` header.

Example:

```http
Authorization: YOUR_API_KEY
```

## HTTPS only

All requests must use the HTTPS protocol.

## API return codes

Mirakl API uses standard HTTP return codes.

When making HTTP requests, you can check the success or failure status of your request by using the HTTP Status Codes (for example `200`). You must not use the HTTP Status Messages or Reason-Phrases (for example `OK`), as they are optional and may not be returned in HTTP responses.

### Success Codes

- `200` — OK: Request succeeded.
- `201` — Created: Request succeeded and resource created.
- `202` — Accepted: Request accepted for processing.
- `204` — No Content: Request succeeded but does not return any content.

### Error Codes

- `400` — Bad Request: Parameter errors or bad method usage. For example, a required parameter is missing, some parameters use an incorrect format, or a data query is not in the expected state.
- `401` — Unauthorized: API call without authentication. Add authentication information or use a valid authentication token.
- `403` — Forbidden: Access to the resource is denied. Current user cannot access the resource.
- `404` — Not Found: The resource does not exist. The resource URI or requested resource do not exist for the current user.
- `405` — Method Not Allowed: The HTTP method (`GET`, `POST`, `PUT`, `DELETE`) is not allowed for this resource.
- `406` — Not Acceptable: The requested response content type is not available for this resource.
- `410` — Gone: The resource is permanently gone. The requested resource is no longer available and will not be available again.
- `415` — Unsupported Media Type: The entity content type sent to the server is not supported.
- `429` — Too Many Requests: Rate limits are exceeded. The user has sent too many requests in the last hour.
- `500` — Internal Server Error: The server encountered an unexpected error.

## Rate limits

Mirakl APIs are protected by rate limits. Each API has a dedicated section displaying its rate limit.

If you make too many calls, you might receive an HTTP `429 Too Many Requests` error. The response will contain a `Retry-After` header that specifies the number of seconds to wait before making a new request.

## Request Content-Type

If an API request supports multiple Content-Types, add a `Content-Type` header to select the format to use in the request. The API documentation lists the formats an API can consume.

## Response Content-Type

If an API response supports multiple Content-Types, add an `Accept` header to select the format accepted in the response. The API documentation lists the formats an API can produce.

## List of values as URL parameters

Array-type fields indicate a list of values as URL parameters. You can add more `parameter=value` elements to the URL.

Example:

```text
?parameter=value1&parameter=value2&parameter=value3
```

## UTF-8 encoding

Text data is encoded in UTF-8.

## Locale

If the API returns internationalized data, you can specify the `locale` parameter.

The locale format is usually `<ISO-639>_<ISO-3166>` (for example `en_US`). There are some exceptions where the locale format can be `<ISO-639>` (for example `en`). The locale returned in a response uses this format.

The APIs only accept locales that are equivalent to the languages activated in the back-office.

## Date formats

APIs can use different date formats compliant with ISO 8601.

### Date-time with timezone

Pattern:

```text
YYYY-MM-DDThh:mm:ss[.SSS]±hh:mm
```

Notes:

- The offset `+00:00` can be replaced by `Z`.
- All APIs provide date-times in UTC, with the trailing `Z`.
- Milliseconds may be omitted if equal to `.000`.

### Date-time without timezone

Pattern:

```text
YYYY-MM-DDThh:mm:ss[.SSS]
```

Notes:

- The timezone does not appear.
- Milliseconds may be omitted if equal to `.000`.

### Time with timezone

Pattern:

```text
hh:mm[:ss][.SSS]±hh:mm
```

Notes:

- Time only, with timezone.
- The offset `+00:00` can be replaced by `Z`.
- Seconds may be omitted if equal to `:00`.
- Milliseconds may be omitted if equal to `.000`.

### Pattern components

- `YYYY` — years (four-digit)
- `MM` — months, `01-12`
- `DD` — days, `01-31`
- `T` — delimiter between the date and time
- `hh` — hours, `00-23`
- `mm` — minutes, `00-59`
- `ss` — seconds, `00-60`
- `SSS` — milliseconds, `000-999`
- `±hh:mm` — offset from UTC

## URL encoding for GET requests

For GET requests, use URL encoding.

Example:

```text
2019-08-29T02:34:00+02:00
```

becomes:

```text
2019-08-29T02%3A34%3A00%2B02%3A00
```

## Shop Selection

When calling APIs as a shop, a request parameter `shop_id` is available. This parameter is useful when a user is associated with multiple shops and should be specified to select the shop to be used by the API.

## Offset pagination and sort

Some APIs support offset pagination. In this case, you can use the `max` and `offset` parameters:

- `max`: indicates the maximum number of items returned per page. Optional. Default is `10`. Maximum is `100`.
- `offset`: indicates the index of the first item among all the results in the returned page. Optional. Default is `0`.

With pagination, the URL of the previous and/or next page can be returned in the response header `Link`.

When a `sort` parameter is available on such an API, it can be used to sort the results.

- `sort`: indicates how the results should be sorted. Optional. Possible values are defined in resources.
- `order`: indicates the sort direction. Optional. Possible values are `asc` (default) or `desc`.

## Seek pagination and sort

For better performance and user experience, some APIs support seek pagination. This means that you cannot go directly to the N-th page.

Use the optional `limit` query parameter to indicate the maximum number of items returned per page.

- Default value: `10`
- Maximum value: `100`

If there are more results to return, the response contains a `next_page_token` field. Pass this value in the `page_token` query parameter to return the next page of results.

The API also returns a `previous_page_token` when the result is not the first page. Use it the same way as `next_page_token`.

Values of `next_page_token` and `previous_page_token` contain all required parameters to access next and previous pages. When using the `page_token` parameter, all other parameters are ignored, regardless of the value given.

When a sort parameter is available, it must follow the format:

```text
sort=criterion,direction
```

Where:

- `criterion` is the name of the criterion to sort by (for example `date_created`, `title`)
- `direction` is the sort direction and can be one of `ASC`, `DESC`

