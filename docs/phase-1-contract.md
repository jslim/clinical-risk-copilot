## Phase 1 patient scope

For the hackathon MVP, patient data is handled through a static in-code registry.

### Patient registry
- No database is required in Phase 1.
- Patient metadata is stored in code.
- Unknown patient IDs must return `404`.

### Canonical product endpoint
- `GET /api/patients/{patient_id}/summary`

This is the frontend-facing endpoint for patient detail views.

### Data mode by patient
For the hackathon:
- `demo-1` may use live VytalLink data when available, or fall back to stub data
- `demo-2` uses stub data
- `demo-3` uses stub data

### Purpose
This allows the MVP to:
- support a patient list
- show multiple patient states
- preserve the live integration path
- continue working even when device data is incomplete

### Phase 1 constraints
- No auth
- No database
- No multi-tenant logic
- No production persistence
- Static registry only