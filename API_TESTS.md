# API_TESTS.md

> Copy-paste `curl` flows only.

---

## 0) Base URL

```bash
export BASE_URL="http://localhost:8000"
```

---

## 1) Health check

```bash
curl "$BASE_URL/health"
```

---

## 2) Login as Owner

```bash
curl -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@auditcore.local","password":"Owner123!"}'
```

---

## 3) Login as Auditor

```bash
curl -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"auditor@auditcore.local","password":"Auditor123!"}'
```

---

## 4) Login as GM

```bash
curl -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"gm@auditcore.local","password":"Gm123!"}'
```

---

## 5) Login as Manager

```bash
curl -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"manager@auditcore.local","password":"Manager123!"}'
```

---

## 6) Login as System Admin

```bash
curl -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"sysadmin@auditcore.local","password":"Sysadmin123!"}'
```

---

## 7) Login as App Owner

```bash
curl -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"appowner@auditcore.local","password":"Appowner123!"}'
```

---

## 8) Get current user

```bash
curl "$BASE_URL/api/auth/me" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

## 9) Refresh token

```bash
curl -X POST "$BASE_URL/api/auth/refresh" \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token":"<REFRESH_TOKEN>"}'
```

---

## 10) Upload JSON document

```bash
curl -X POST "$BASE_URL/api/documents/upload" \
  -H "Authorization: Bearer <AUDITOR_ACCESS_TOKEN>" \
  -F 'file=@sample-invoice.json'
```

---

## 11) Upload PDF document

```bash
curl -X POST "$BASE_URL/api/documents/upload" \
  -H "Authorization: Bearer <AUDITOR_ACCESS_TOKEN>" \
  -F 'file=@sample-invoice.pdf'
```

---

## 12) Upload JPG image

```bash
curl -X POST "$BASE_URL/api/documents/upload" \
  -H "Authorization: Bearer <AUDITOR_ACCESS_TOKEN>" \
  -F 'file=@sample-invoice.jpg'
```

---

## 13) Reject fake PDF renamed from EXE

```bash
curl -X POST "$BASE_URL/api/documents/upload" \
  -H "Authorization: Bearer <AUDITOR_ACCESS_TOKEN>" \
  -F 'file=@fake.exe;filename=fake.pdf'
```

---

## 14) Get next certification item

```bash
curl "$BASE_URL/api/certification/next" \
  -H "Authorization: Bearer <AUDITOR_ACCESS_TOKEN>"
```

---

## 15) Certify OCR result with corrected fields

```bash
curl -X POST "$BASE_URL/api/certification/<EXTRACTION_ID>/certify" \
  -H "Authorization: Bearer <AUDITOR_ACCESS_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{
    "fields": {
      "invoice_number": "INV-2026-9001",
      "date": "2026-06-28",
      "amount": "12450000",
      "vendor_name": "شركة الرافدين",
      "items_list": ["صنف 1", "صنف 2"]
    }
  }'
```

---

## 16) Try certify without correcting low-confidence field

```bash
curl -X POST "$BASE_URL/api/certification/<EXTRACTION_ID>/certify" \
  -H "Authorization: Bearer <AUDITOR_ACCESS_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{
    "fields": {
      "invoice_number": "INV-2026-9001",
      "date": "2026-06-28",
      "amount": "",
      "vendor_name": "شركة الرافدين",
      "items_list": ["صنف 1", "صنف 2"]
    }
  }'
```

---

## 17) List admin activity feed

```bash
curl "$BASE_URL/api/admin/activity" \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

---

## 18) List branches

```bash
curl "$BASE_URL/api/admin/branches" \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

---

## 19) Create user

```bash
curl -X POST "$BASE_URL/api/admin/users" \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "newuser@auditcore.local",
    "password": "Newuser123!",
    "full_name": "مستخدم جديد",
    "role": "manager",
    "branch_id": null
  }'
```

---

## 20) Deactivate user

```bash
curl -X POST "$BASE_URL/api/admin/users/<USER_ID>/deactivate" \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

---

## 21) Grant temporary permission override

```bash
curl -X POST "$BASE_URL/api/admin/permissions/override" \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "<USER_ID>",
    "permission_code": "view_waste_map",
    "action": "grant",
    "reason": "مراجعة مؤقتة لمدة 7 أيام",
    "expires_at": "2026-07-05T10:00:00Z"
  }'
```

---

## 22) Revoke permission override

```bash
curl -X POST "$BASE_URL/api/admin/permissions/override" \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "<USER_ID>",
    "permission_code": "view_waste_map",
    "action": "revoke",
    "reason": "إلغاء الصلاحية"
  }'
```

---

## 23) Attempt forbidden app-owner permission grant

```bash
curl -X POST "$BASE_URL/api/admin/permissions/override" \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "<USER_ID>",
    "permission_code": "app_owner_inventory",
    "action": "grant",
    "reason": "محاولة يجب أن تُرفض"
  }'
```

---

## 24) Owner verifies ledger integrity

```bash
curl "$BASE_URL/api/owner/ledger/verify" \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

---

## 25) Owner checks auditor efficiency

```bash
curl "$BASE_URL/api/owner/auditor-efficiency" \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

---

## 26) Tamper a ledger entry for test

```bash
curl -X POST "$BASE_URL/api/owner/ledger/tamper/<ENTRY_ID>" \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

---

## 27) Re-verify ledger after tamper

```bash
curl "$BASE_URL/api/owner/ledger/verify" \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

---

## 28) Auditor checks current user after certification

```bash
curl "$BASE_URL/api/auth/me" \
  -H "Authorization: Bearer <AUDITOR_ACCESS_TOKEN>"
```

---

## 29) Owner checks current user

```bash
curl "$BASE_URL/api/auth/me" \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

---

## 30) GM checks current user

```bash
curl "$BASE_URL/api/auth/me" \
  -H "Authorization: Bearer <GM_ACCESS_TOKEN>"
```

---

## 31) Manager checks current user

```bash
curl "$BASE_URL/api/auth/me" \
  -H "Authorization: Bearer <MANAGER_ACCESS_TOKEN>"
```

---

## 32) System Admin checks current user

```bash
curl "$BASE_URL/api/auth/me" \
  -H "Authorization: Bearer <SYSADMIN_ACCESS_TOKEN>"
```

---

## 33) App Owner checks current user

```bash
curl "$BASE_URL/api/auth/me" \
  -H "Authorization: Bearer <APPOWNER_ACCESS_TOKEN>"
```

---

## 34) Login failure test

```bash
curl -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"auditor@auditcore.local","password":"WrongPassword123!"}'
```

---

## 35) Repeat failed login test

```bash
curl -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"auditor@auditcore.local","password":"WrongPassword123!"}'
```

---

## 36) Repeat failed login test

```bash
curl -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"auditor@auditcore.local","password":"WrongPassword123!"}'
```

---

## 37) Repeat failed login test

```bash
curl -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"auditor@auditcore.local","password":"WrongPassword123!"}'
```

---

## 38) Fifth failed login should trigger lockout

```bash
curl -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"auditor@auditcore.local","password":"WrongPassword123!"}'
```

---

## 39) Try login during lockout

```bash
curl -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"auditor@auditcore.local","password":"Auditor123!"}'
```

---

## 40) Use cloud tenant header example

```bash
curl "$BASE_URL/api/auth/me" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "X-Tenant-Schema: tenant_a"
```



---

## 41) Trigger local analytics run

```bash
curl -X POST "$BASE_URL/api/analytics/run/<COMPANY_ID>" \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

---

## 42) Owner dashboard

```bash
curl "$BASE_URL/api/owner/dashboard" \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

---

## 43) Owner dashboard layer 2

```bash
curl "$BASE_URL/api/owner/dashboard/layer2" \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

---

## 44) Owner dashboard layer 3

```bash
curl "$BASE_URL/api/owner/dashboard/layer3" \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

---

## 45) Owner dashboard layer 4

```bash
curl "$BASE_URL/api/owner/dashboard/layer4/<DOCUMENT_ID>" \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

---

## 46) Manager dashboard

```bash
curl "$BASE_URL/api/manager/dashboard" \
  -H "Authorization: Bearer <MANAGER_ACCESS_TOKEN>"
```

---

## 47) Auditor tries owner dashboard and should get 403

```bash
curl "$BASE_URL/api/owner/dashboard" \
  -H "Authorization: Bearer <AUDITOR_ACCESS_TOKEN>"
```


---

## 48) App Owner list clients

```bash
curl "$BASE_URL/api/appowner/clients" \
  -H "Authorization: Bearer <APPOWNER_ACCESS_TOKEN>"
```

---

## 49) App Owner tier change

```bash
curl -X POST "$BASE_URL/api/appowner/clients/<CLIENT_ID>/tier" \
  -H "Authorization: Bearer <APPOWNER_ACCESS_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{"tier":"elite"}'
```

---

## 50) App Owner list presets

```bash
curl "$BASE_URL/api/appowner/templates/presets" \
  -H "Authorization: Bearer <APPOWNER_ACCESS_TOKEN>"
```

---

## 51) App Owner create template

```bash
curl -X POST "$BASE_URL/api/appowner/templates" \
  -H "Authorization: Bearer <APPOWNER_ACCESS_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Trading Pro","sector":"Trading","widgets":["waste_map","risk_map"]}'
```

---

## 52) App Owner push template

```bash
curl -X POST "$BASE_URL/api/appowner/templates/<TEMPLATE_ID>/push" \
  -H "Authorization: Bearer <APPOWNER_ACCESS_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{"client_name":"مجموعة النخيل التجارية","deployment_mode":"cloud"}'
```

---

## 53) App Owner rollback template

```bash
curl -X POST "$BASE_URL/api/appowner/templates/<TEMPLATE_ID>/rollback" \
  -H "Authorization: Bearer <APPOWNER_ACCESS_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{"previous_payload":"{"name":"Trading Pro","sector":"Trading","widgets":["waste_map"]}"}'
```

---

## 54) App Owner CRaaS queue

```bash
curl "$BASE_URL/api/appowner/craas" \
  -H "Authorization: Bearer <APPOWNER_ACCESS_TOKEN>"
```

---

## 55) App Owner create CRaaS request

```bash
curl -X POST "$BASE_URL/api/appowner/craas" \
  -H "Authorization: Bearer <APPOWNER_ACCESS_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{"client_name":"مجموعة النخيل التجارية","title":"تقرير فرص خاص","quoted_price_iqd":400000,"deployment_mode":"cloud"}'
```

---

## 56) App Owner maintenance log

```bash
curl "$BASE_URL/api/appowner/maintenance" \
  -H "Authorization: Bearer <APPOWNER_ACCESS_TOKEN>"
```

---

## 57) App Owner inventory-only health scan

```bash
curl -X POST "$BASE_URL/api/appowner/clients/health-scan" \
  -H "Authorization: Bearer <APPOWNER_ACCESS_TOKEN>"
```

---

## 58) Run What-If simulator

```bash
curl -X POST "$BASE_URL/api/what-if/run" \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{"waste_map_item_id":"<WASTE_MAP_ITEM_ID>","recovery_percent":50,"implementation_months":3,"manual_cost":100000,"horizon_months":6}'
```

---

## 59) Export What-If result to PDF

```bash
curl -X POST "$BASE_URL/api/what-if/export" \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{"waste_map_item_id":"<WASTE_MAP_ITEM_ID>","recovery_percent":50,"implementation_months":3,"manual_cost":100000,"horizon_months":6}'
```
