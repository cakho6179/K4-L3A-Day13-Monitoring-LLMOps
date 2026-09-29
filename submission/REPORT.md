# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** NGUYỄN VĂN SƠN
- **MSSV:** 2A202602744
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/cakho6179/K4-L3A-Day13-Monitoring-LLMOps
- **Commit SHA cuối:** 3746de435b10f4c7521346cff90562e37dfe49f3
- **Challenge ID:** day13-k4-l3a-monitoring-llmops-v1 (cohort K4; file `config/challenge.json` đã gitignored, không commit)
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602744`

## 2. Evidence index

| Evidence | Đường dẫn | Trạng thái |
|---|---|---|
| Pytest cuối | `evidence/01-pytest.txt` | xong — 22 passed |
| Log validator | `evidence/02-log-validator.txt` | xong — 100/100 |
| Dashboard validator | `evidence/03-dashboard-validator.txt` | xong — 6/6 |
| Structured log | `evidence/04-structured-log.txt` | xong |
| PII redaction | `evidence/04-structured-log.txt` (dòng `[REDACTED_EMAIL]`) | xong — 0 leak |
| Trace list | `evidence/06-trace-list.txt` + ảnh UI `evidence/06-trace-list.png` | 27 traces (xem file txt); ảnh UI tự chụp |
| Trace waterfall | ảnh UI `evidence/07-trace-waterfall.png` | tự chụp 1 trace có root + retrieval + generation |
| Trace metadata | ảnh UI `evidence/08-trace-metadata.png` | tự chụp: correlation_id, prompt v/label, tokens, cost |
| Prompt versions | ảnh UI `evidence/09-prompt-versions.png` | day13-chat v1 (baseline+production) / v2 (candidate) |
| Prompt rollback | ảnh UI `evidence/10-prompt-rollback.png` | production v1→v2→v1, đã chạy thật |
| Dashboard runtime | `evidence/11-dashboard-overview.png` | xong (60 records) |
| Incident metric | `/metrics` P95 2654ms (xem mục 7) | xong (text) |
| Incident log | `evidence/13-incident-log.txt` (`req-e13fcfaf`, 2654ms, challenge) | xong |
| Incident trace | ảnh UI `evidence/14-incident-trace.png` | tự chụp trace của CID challenge |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | ~50/100 (thiếu CID/enrichment, ước lượng) | 100/100 | 60 records, 29 CID, 0 PII leak |
| `validate_dashboard.py` | 6/6 (contract có sẵn) | 6/6 | giữ nguyên 6 panel |
| `pytest` | 22 passed | 22 passed | không regression |
| Số traces hợp lệ | 0 | 27 (10 baseline v1 + 10 candidate v2 + 5 challenge + promote + rollback) | `evidence/06-trace-list.txt` |
| Số PII leak | n/a | 0 | email/phone/CC/thẻ đều scrubbed |
| Latency P95 / TTFT P95 | ~155ms / ~50ms | baseline ~155ms; challenge P95 2654ms / TTFT 50ms | `rag_slow` sleep 2.5s |
| Retrieval success rate | 100% | 100% (rag_slow chỉ chậm, không lỗi) | error_breakdown rỗng |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** `app/middleware.py` — `clear_contextvars()` đầu request; nhận `x-request-id` nếu khớp `req-[8-hex]`, else sinh `req-<uuid4hex[:8]>`; `bind_contextvars(correlation_id=...)`; trả lại `x-request-id` + `x-response-time-ms` trên response.
- **Các metadata được ghi vào structured log:** `app/main.py` bind trước `request_received`: `user_id_hash` (sha256[:12]), `session_id`, `feature`, `model` (từ `agent.model`), `env`. `response_sent` thêm `latency_ms/ttft_ms/tokens/cost/quality/tool_name/tool_success`.
- **Cách bảo đảm PII được scrub trước khi ghi:** `app/logging_config.py` đăng ký `scrub_event` trước `StackInfoRenderer/JsonlFileProcessor/JSONRenderer`. `scrub_text` che email/phone VN/CCCD/thẻ (+passport) trong cả `payload` và `event`.
- **Cách kiểm chứng kết quả:** `validate_logs.py` 100/100; `grep` log không còn `student@vinuni`, `0987654321`, `4111 1111`; thấy `[REDACTED_EMAIL]` (3 markers).

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** project `day13-k4-l3a-2A202602744`, 27 traces từ các workload của tôi (10 baseline + 10 candidate + 5 challenge + promote + rollback); danh sách trong `evidence/06-trace-list.txt`.
- **Cấu trúc root/retrieval/generation observations:** `app/agent.py` — root `@observe(name="lab-agent-run", as_type="agent")`; child `retrieval` (`as_type="retriever"`, input=query scrubbed, output=doc_count/preview) qua `_child_observation(start_as_current_observation)`; child `llm-generation` (`as_type="generation"`, model/prompt/input scrubbed + `update_current_generation` với usage_details/cost_details). Mọi tracing update bọc try/except nên test mock không có method vẫn pass.
- **Cách nối trace với log:** cùng `correlation_id` trong trace metadata (`propagate_attributes`) và log field.
- **Prompt name:** `day13-chat` (`.env` `LANGFUSE_PROMPT_NAME`).
- **Version/label baseline:** v1 / labels `baseline` + `production` (ban đầu).
- **Version/label candidate:** v2 / label `candidate`.
- **Trace ID của mỗi version:** baseline v1: `92a65b0133270e2ba6fde2640a1cd34e` (session s01); candidate v2: xem `evidence/06-trace-list.txt`; promote production→v2: `39c9abe2fa273e86caa356abad030994` (version=2); rollback production→v1: `0c38c2cd426151222c16371674e32f3f` (version=1).
- **Cách promote và rollback `production`:** `update_prompt(day13-chat, v2, [production])` rồi request `req-2b8bab81` → version 2 (promote); `update_prompt(day13-chat, v1, [production])` rồi request `req-c8ca5099` → version 1 (rollback); verify bằng `get_prompt(label=production)`.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** `config/dashboard.yaml` giữ 6 panel (latency/TTFT, traffic, errors/retrieval, cost, tokens, quality); runtime render bằng `scripts/make_dashboard.py` từ `data/logs.jsonl` → `evidence/11-dashboard-overview.png`.
- **SLO và lý do chọn:** `config/slo.yaml` — 99.5% `response_sent latency<=3000ms` / `request_received` trong 28d. Baseline P95 ~155ms nên 3000ms chỉ kích hoạt khi incident (rag_slow 2.5s).
- **Cách tính error budget:** 0.5% × 28d = 0.005×28×24×60 = **201.6 phút (~3.36 giờ)** request chậm/lỗi mỗi 28 ngày.
- **Ba alert và runbook tương ứng:** `config/alert_rules.yaml` + `docs/alerts.md` — SlowResponsesP95 (critical, 5m), FailedRequestsErrorRate (critical, 5m), QualityDropCostSpike (warning, 15m); đều có severity/duration/owner/`#day13-alerts`/runbook.

## 7. Điều tra challenge (day13-k4-l3a-monitoring-llmops-v1, incident `rag_slow`)

- **Challenge ID:** day13-k4-l3a-monitoring-llmops-v1 (cohort K4, seed 1311, 5 queries feature `monitoring`).
- **Khoảng thời gian điều tra:** ngay sau `python scripts/inject_incident.py` (đọc `config/challenge.json`) + `python scripts/load_test.py --challenge --concurrency 5`.
- **Triệu chứng từ metrics:** 5/5 request ~13.3s client-side; `/metrics` latency_p95 **2654ms** (baseline ~155ms), p50 152ms; TTFT p95 vẫn ~50ms → chậm ở retrieval, không phải first-token; error rỗng (không lỗi, chỉ chậm).
- **Log line và correlation ID liên quan:** `evidence/13-incident-log.txt` — 5 CID challenge, ví dụ `req-e13fcfaf` (`k4-l3a-challenge-s04`, latency 2654ms), `tool_success=true`.
- **Trace ID và span gây ảnh hưởng:** 5 traces challenge trên Langfuse (sessions `k4-l3a-challenge-s01..s05`, version=2); span `retrieval` (RETRIEVER) kéo dài ~2.5s, generation (~150ms) bình thường — xem `evidence/06-trace-list.txt` + ảnh `14-incident-trace.png` (tự chụp).
- **Root cause:** incident `rag_slow` làm `retrieve()` trong `app/mock_rag.py` `time.sleep(2.5)` mọi request.
- **Fix action:** `python scripts/inject_incident.py --disable` (đã chạy, incidents về False); kiểm tra vector store/timeout.
- **Preventive measure:** timeout + cache retrieval, alert SlowResponsesP95 (5m), dashboard theo dõi P95/TTFT.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** bọc mọi Langfuse update trong try/except + `_child_observation` fallback noop — app chạy được khi chưa có key (local-fallback) mà vẫn tạo child spans khi có key thật; giữ 22/22 tests pass.
- **Một lỗi/blocker đã gặp:** `load_test.py` báo connection refused vì `Start-Job` không persist giữa các lệnh; chuyển sang `Start-Process -WindowStyle Hidden` thì API sống và validator lên 100/100.
- **Cách tìm nguyên nhân và xử lý:** kiểm tra job/process + `/health`; thấy 1 dòng `app_started` duy nhất trong log → API đã chết trước load test.
- **Cách hiểu luồng Metrics → Logs → Traces:** metrics (P95 2654ms) chỉ triệu chứng + khoảng thời gian; logs lọc theo khoảng đó cho CID cụ thể (`req-e13fcfaf`, 2654ms); trace cùng CID cho biết span nào (retrieval) gây chậm.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** prompt version + label cho phép đổi hành vi không sửa code và rollback khi quality/cost xấu; token/cost theo dõi trong generation span; SLO/error budget biến latency/quality thành cam kết đo được.
- **Điều quan trọng nhất đã học:** redaction phải đứng trước serialize/ghi file, và correlation ID là cầu nối duy nhất giữa 3 tín hiệu.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** ảnh chụp UI Langfuse (06,07,08,09,10,14 PNG) phải tự chụp trong browser; observation metadata/usage qua public v2 API bị trễ vài phút nên report dùng version + session + log CID để đối chiếu, ảnh UI sẽ thấy đủ metadata.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối. (cần điền SHA sau commit)
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace. (chờ trace Langfuse)
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
