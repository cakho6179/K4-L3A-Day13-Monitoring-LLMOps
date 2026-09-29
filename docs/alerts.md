# Alert Runbook — Day 13 Monitoring & LLMOps

Mỗi alert dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.
Kênh thông báo chung: Slack `#day13-alerts`.

## Alert 1 — SlowResponsesP95

- Tên: SlowResponsesP95
- Severity: critical
- Duration: 5m
- Kênh thông báo: Slack `#day13-alerts`
- SLI/SLO liên quan: `fast_successful_requests` — 99.5% request `response_sent` có `latency_ms <= 3000` trong 28 ngày.
- Điều kiện và thời gian duy trì: `percentile(latency_ms, 95) > 3000ms` trên `event == "response_sent"` liên tục 5 phút.
- Ảnh hưởng tới người dùng: người dùng chờ lâu, tail latency tăng, trải nghiệm chat chậm rõ rệt.
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard panel Latency, xác nhận P95/P99 và TTFT P95 tăng trong cùng cửa sổ 60 phút.
  2. Lọc `data/logs.jsonl` theo khoảng thời gian đó, tìm các `response_sent` có `latency_ms > 3000`, lấy một `correlation_id`.
  3. Mở trace có cùng `correlation_id` trên Langfuse, so sánh thời gian span `retrieval` vs `llm-generation`.
- Mitigation tạm thời: giảm timeout retrieval, bật cache prompt, scale API; nếu span retrieval chậm thì tắt incident `rag_slow` sau khi xác minh.
- Owner: backend-oncall

## Alert 2 — FailedRequestsErrorRate

- Tên: FailedRequestsErrorRate
- Severity: critical
- Duration: 5m
- Kênh thông báo: Slack `#day13-alerts`
- SLI/SLO liên quan: `fast_successful_requests` + guardrail `error_rate <= 2%`, `retrieval_success_rate >= 90%`.
- Điều kiện và thời gian duy trì: `error_rate > 2%` hoặc `retrieval_success_rate < 90%` liên tục 5 phút.
- Ảnh hưởng tới người dùng: request lỗi 500, không nhận được câu trả lời hoặc fallback rỗng.
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard panel Errors, xem `error_rate_pct`, `count_by(error_type)` và `tool_success_rate_pct`.
  2. Lọc `data/logs.jsonl` lấy `request_failed` trong cửa sổ alert, ghi `correlation_id`, `error_type`, `tool_name`.
  3. Mở trace cùng `correlation_id`, kiểm tra span `retrieval` có `status ERROR` hay `tool_success=false` không.
- Mitigation tạm thời: tắt incident `tool_fail`, kiểm tra vector store, retry với backoff; công bố sự cố trên Slack.
- Owner: backend-oncall

## Alert 3 — QualityDropCostSpike

- Tên: QualityDropCostSpike
- Severity: warning
- Duration: 15m
- Kênh thông báo: Slack `#day13-alerts`
- SLI/SLO liên quan: guardrail `quality_score_avg >= 0.75`, `daily_cost_usd <= 2.5`.
- Điều kiện và thời gian duy trì: `mean(quality_score) < 0.75` liên tục 15 phút HOẶC `sum(cost_usd) > 2.5` trong ngày.
- Ảnh hưởng tới người dùng: câu trả lời kém liên quan/dài dòng, chi phí token tăng bất thường.
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard panel Quality + Cost + Tokens, đối chiếu `mean(quality_score)`, `sum(cost_usd)`, `sum(tokens_out)`.
  2. Lọc `data/logs.jsonl` tìm `response_sent` có `quality_score < 0.75` hoặc `tokens_out` cao bất thường, lấy `correlation_id`.
  3. Mở trace cùng `correlation_id`, kiểm tra metadata `prompt_name/version/label`, `tokens`, `cost` ở generation span.
- Mitigation tạm thời: rollback label `production` về prompt version ổn định trước đó, giới hạn `max_tokens`, tắt incident `cost_spike` sau khi xác minh.
- Owner: llmops-oncall
