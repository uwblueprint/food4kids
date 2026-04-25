# Feature: Location Validation and Ingestion Pipeline

## Goal

Build an admin UI that walks users through uploading an Excel/CSV file of delivery locations, mapping its columns to canonical fields, validating the data, and ingesting confirmed entries into the database.

---

## Out of Scope (Separate Prompt)

- **Step 4 — Review** (`POST /locations/review`, not yet implemented): net-new vs. stale comparison, duplicate approval/denial. Will be implemented separately.

---

## Steps

### Step 1 — File Upload

Allow admins to upload an Excel (`.xlsx`) file via drag-and-drop or file picker.

- Reject unsupported file types **before** uploading by checking the file extension on the client.
- Show a red `Banner` above the import card on invalid format (see Figma).
- The backend also validates file type/size and returns `HTTP 400` with a message — surface server errors with the same banner pattern.
- Use the existing `Input` component (`type="file"`) or drag-and-drop wrapper. Follow the multipart/form-data pattern in `TestImageUpload.tsx`.

### Step 2 — Column Mapping

After a valid file is selected (but before validation), allow the user to map their file's column headers to canonical system fields.

**UI:** Use the existing `DropdownTable` component. Each row = one canonical field. The dropdown options = the parsed column headers from the uploaded file. Required fields are marked with `*`.

**Canonical fields for `LocationImportEntry`:**

| System Field (canonical) | Display Label     | Required |
| ------------------------ | ----------------- | -------- |
| `contact_name`           | Guardian Name     | ✓        |
| `address`                | Address           | ✓        |
| `phone_number`           | Phone Number      | ✓        |
| `delivery_group`         | Delivery Group    | —        |
| `num_boxes`              | Number of Boxes   | —        |
| `halal`                  | Halal?            | —        |
| `dietary_restrictions`   | Food Restrictions | —        |

> **Note:** `num_children` exists on the `Location` DB model but is not in `LocationImportEntry` — treat as unsupported for now.

**Persisting the mapping (per `admin_id`):**

Store the column mapping some table keyed by admin ID. Load it as the default on subsequent visits by admin - store in localStorage upon login.

**Backend change needed:** `POST /locations/validate` currently uses a hardcoded `DEFAULT_COLUMN_MAP`. Modify the endpoint to accept an optional `column_map` form field (JSON string) alongside the file upload. Fall back to `DEFAULT_COLUMN_MAP` if not provided. The service already has `_parse_row(row, column_map)` parameterized — just wire it through the route.

```python
# location_routes.py change (rough sketch)
@router.post("/validate")
async def validate_locations(
    file: UploadFile = File(...),
    column_map: str | None = Form(None),  # JSON-encoded dict
    ...
)
```

### Step 3 — Validation

Hit `POST /locations/validate` with the file and column map. Display results in a `DataTable`.

**API contract (already implemented):**

```
POST /locations/validate
Content-Type: multipart/form-data

Request:  file (UploadFile), column_map? (Form JSON string)
Response: LocationImportResponse
```

**TypeScript types** — add to `frontend/src/types/location.ts`:

```typescript
export type AlertType = "WARNING" | "ERROR";
export type AlertCode =
  | "MISSING_FIELDS"
  | "INVALID_FORMAT"
  | "LOCAL_DUPLICATE"
  | "MISSING_DELIVERY_GROUP"
  | "PARTIAL_DUPLICATE";

export interface LocationImportAlert {
  type: AlertType;
  code: AlertCode;
  message: string;
}

export interface LocationImportEntry {
  contact_name: string | null;
  address: string | null;
  delivery_group: string | null;
  phone_number: string | null;
  num_boxes: number | null;
  halal: boolean | null;
  dietary_restrictions: string | null;
}

export interface LocationImportRow {
  row: number;
  location: LocationImportEntry;
  alerts: LocationImportAlert[];
}

export type LocationImportStatus = "SUCCESS" | "WARNING" | "ERROR";

export interface LocationImportResponse {
  status: LocationImportStatus;
  total_rows: number;
  rows: LocationImportRow[];
}
```

**Validation table columns:** Row #, Guardian Name, Address, Phone Number, Delivery Group, Status (alert icon + message). Use `AlertCell` from `DataTable.tsx` for the status column. Use `getCellClassName` to highlight rows.

- `ERROR` rows: red row highlight — block proceeding to ingest
- `WARNING` rows: yellow row highlight — allow proceeding
- `SUCCESS`: all rows clean — proceed to ingest

### Step 5 — Ingest

Once validation passes (status `SUCCESS` or `WARNING`), allow the admin to confirm and hit `POST /locations/ingest`.

**API contract (already implemented):**

```
POST /locations/ingest
Content-Type: application/json

Request:  LocationIngestRequest { net_new: ValidatedLocationImportEntry[], stale: LocationRead[] }
Response: LocationIngestResponse { created: LocationRead[], archived: LocationRead[] }
```

For this step, pass `stale: []` — stale detection is part of the Review step (Step 4, separate prompt). Only include rows with no `ERROR` alerts in `net_new` (warning rows are okay).

Show a success state with counts: `{created.length} locations added`.

---

## Designs

Figma: https://www.figma.com/design/aoBkDdARkmaUc9Cc2OMicR/F4K-Designs?node-id=1170-4999&t=JTOAQqlyq9t9NxRR-1

Screens to reference:

- **Route Generation - Uploading** (file upload)
- **Route Generation - Wrong File Type** (wrong file type)

- **Route Generation - Mapping** (column mapping with `DropdownTable`)
- **Route Generation - DropdownMenu** (dropdown options)

- **Route Generation - Validation** (validation results table)
- **Route Generation - Review Changes** (review changes tables for net new/stale/duplicate)

---

## Technical Notes

**Frontend:**

- TypeScript types → create `frontend/src/types/location.ts`
- Use Tanstack Query `useMutation` for `POST /locations/validate` and `POST /locations/ingest`
- Reuse existing components:
  - `Banner` — format error / server error messages
  - `Card` — page section container
  - `DropdownTable` — column mapping
  - `DataTable` + `AlertCell` — validation results (`frontend/src/common/components/DataTable.tsx`)
  - `Button` — primary/secondary actions
- Add any new components to `StyleGuidePage`
- Column mapping localStorage key: `location_column_map:{admin_id}`

**Backend:**

- Modify `POST /locations/validate` in `location_routes.py` to accept an optional `column_map: str | None = Form(None)` field; parse JSON and pass to `validate_locations()` in `location_service.py` instead of `DEFAULT_COLUMN_MAP`
- No other backend changes needed for Steps 1–3 and 5

**Key files:**

- `frontend/src/common/components/DataTable.tsx` — DataTable + AlertCell
- `frontend/src/common/components/DropdownTable.tsx` — column mapping UI
- `frontend/src/lib/axiosClient.ts` — Axios API client
- `frontend/src/pages/TestImageUpload.tsx` — multipart upload pattern reference
- `backend/python/app/routers/location_routes.py` — validate + ingest routes
- `backend/python/app/services/implementations/location_service.py` — validation logic, DEFAULT_COLUMN_MAP, \_parse_row
- `backend/python/app/models/location.py` — LocationImportResponse, AlertType, AlertCode, LocationImportEntry
