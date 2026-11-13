# Báo cáo cá nhân — Day 6

## Dữ liệu và pipeline

- Chủ đề: tạo kho tri thức truy xuất được từ sách *Introduction to Computer Science*.
- Nguồn: OpenStax/Rice University, [trang sách](https://openstax.org/books/introduction-computer-science) và PDF được lưu tại `starter/data/openstax_computer_science.pdf`.
- Quyền: CC BY-NC-SA 4.0; repo giữ attribution và link nguồn, không đưa API key vào repo.
- Quy mô: 939 trang vật lý; ingestion đọc được 937 trang có text, 2 trang rỗng (physical pages 1 và 2), không có trang lỗi. Phạm vi nội dung chốt là pages 19-920, gồm Chapters 1-14 và chapter review, tổng 902 trang; pages 1-18 là bìa/thông tin đầu sách/mục lục/preface, pages 921-939 là appendix/index.
- Chuẩn hóa: Unicode NFKC, chuẩn hóa xuống dòng và khoảng trắng, giữ paragraph boundary. Mỗi `DocumentPage` giữ `document_id`, `source`, `page`, `chapter`, `language`, `category` và trạng thái trích xuất.
- Embedding: OpenAI `text-embedding-3-small`, 1536 chiều, API thật; query và document dùng cùng model. Chi phí được tính theo token đầu vào; lần chạy này chưa ghi usage token từ response nên không khẳng định số tiền chính xác. Cần đối chiếu API billing nếu giảng viên yêu cầu số tiền tuyệt đối.
- Vector store: PostgreSQL 16.16 + pgvector 0.8.7, Docker image `pgvector/pgvector:0.8.7-pg16`, cosine distance, lưu bền vững trong database local. Thời gian chạy ingest/embed/store A+B+C: 473.69 giây.
- Metadata bắt buộc: `document_id`, `source`, `page`. Metadata bổ sung: `chapter`, `category`, `language`, `chunking` và tham số chunk. `chapter` được suy ra từ mục lục OpenStax và physical-page ranges; dùng làm filter vì có 14 giá trị phân biệt được.

## Cấu hình và benchmark

| Strategy | Chunking | Tham số | Truy xuất |
|---|---|---|---|
| A | Fixed-size | 500 ký tự, overlap 50 | Không filter |
| B | Paragraph-aware | Gom đoạn, tối đa 800 ký tự | Không filter |
| C | Giống B | Tối đa 800 ký tự | Chỉ áp dụng filter `chapter` khi câu hỏi cung cấp filter |

A và B thay đổi đúng cách chia chunk. B và C giữ nguyên corpus, chunk, model và vector; C chỉ thay đổi việc áp dụng metadata filter.

Benchmark có 20 câu, gồm 15 dev và 5 test. Có 3 câu filter (`q07`, `q11`, `q19`), trong đó `q19` thuộc test. Evidence của 20/20 câu đã được kiểm tra trực tiếp trong PDF trước khi chạy. Tập test được cố định trước benchmark.

Tiêu chí chọn trước khi xem test: ưu tiên Evidence Hit@3 trên dev; nếu gần nhau thì ưu tiên grounding, coherence và cuối cùng là tài nguyên. Không dùng test để tinh chỉnh.

## Kết quả retrieval

| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian | Chi phí |
|---|---|---:|---:|---:|---:|---|
| A | Dev | 2/15 | 5/15 | 5953 | Trong tổng run 473.69s | Chưa capture exact API usage |
| A | Test | 1/5 | 2/5 | 5953 | Trong tổng run 473.69s | Chưa capture exact API usage |
| B | Dev | 2/15 | 7/15 | 3628 | Trong tổng run 473.69s | Chưa capture exact API usage |
| B | Test | 3/5 | 3/5 | 3628 | Trong tổng run 473.69s | Chưa capture exact API usage |
| C | Dev | 2/15 | 7/15 | 3628 | Trong tổng run 473.69s | Chưa capture exact API usage |
| C | Test | 3/5 | 3/5 | 3628 | Trong tổng run 473.69s | Chưa capture exact API usage |

## Audit thủ công

| Strategy | Coherence trung bình /2 (n=10) | Metadata đủ và đúng | Filter tuân thủ | Grounding 0/1/2, trung bình /2 |
|---|---:|---:|---:|---|
| A | 1.3/2 | 15/15 | N/A | 0/2, 1/2, 2/3; trung bình 1.6/2 |
| B | 1.8/2 | 15/15 | N/A | 0/0, 1/0, 2/5; trung bình 2.0/2 |
| C | 1.8/2 | 15/15 | 3/3 cho q19 | 0/0, 1/0, 2/5; trung bình 2.0/2 |

Chi tiết nhãn, mẫu trang và lý do nằm trong [results/manual_audit.md](../../starter/results/manual_audit.md). Trace đầy đủ nằm trong [benchmark_traces.jsonl](../../starter/results/benchmark_traces.jsonl), summary nằm trong [benchmark_summary.json](../../starter/results/benchmark_summary.json).

## Phân tích và kết luận

### A so với B

B giảm số chunk từ 5953 xuống 3628 và cải thiện Evidence Hit@3 test từ 2/5 lên 3/5. Coherence tăng từ 1.3 lên 1.8 và grounding tăng từ 1.6 lên 2.0. Kết quả phù hợp với giả thuyết rằng giữ paragraph giúp bảo toàn ngữ cảnh. Tuy nhiên, B vẫn có lỗi ở q18 và q20 theo định nghĩa evidence match nghiêm ngặt.

### B so với C

C giữ nguyên chunk và embedding của B, chỉ lọc theo `chapter` khi câu hỏi có filter. Với q19, cả 3 kết quả đều tuân thủ `chapter=12`. Các chỉ số tổng thể không đổi vì benchmark chỉ có một câu test filter và B vốn đã trả về đúng chapter. Do đó chưa thể kết luận filter luôn làm tăng accuracy; bằng chứng hiện tại chứng minh filter hoạt động đúng.

### Ví dụ lỗi

1. q18: Strategy A trả về pages 588, 601 và 600; phần giải thích Bootstrap bị chia giữa các chunk. B/C đưa page 600 lên đầu nhưng strict evidence quote vẫn không khớp đầy đủ trong một chunk.
2. q20: B/C trả về page 800 với ngữ cảnh về kích thước nanotechnology, nhưng evidence quote strict không match vì nội dung bị chia/biến đổi bởi ranh giới chunk và cách trích xuất PDF.

### Hạn chế

- Test chỉ có 5 câu nên không đại diện cho toàn bộ sách.
- Chỉ có một test filter nên so sánh B–C còn yếu.
- Gold evidence dùng exact normalized substring, có thể đánh trượt trường hợp evidence đúng về nghĩa nhưng bị tách qua chunk.
- Coherence và grounding là nhãn thủ công, có nguy cơ thiên lệch người chấm.
- API usage token chưa được lưu trong trace; thời gian 473.69 giây là tổng run A+B+C, không phải thời gian tách riêng từng strategy.

### Nếu làm lại

- Thêm nhiều câu filter ở nhiều chapter và tăng test holdout.
- Lưu `usage.total_tokens` từ mỗi embedding response để báo chi phí chính xác.
- Dùng chunk overlap hoặc parent-context retrieval để giảm lỗi evidence bị chia.
- Tách thời gian ingest, embedding và database write cho từng strategy.

## Lệnh tái lập

Từ thư mục `starter/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
docker compose -p day6_student_starter up -d --wait
python scripts/check_setup.py
python -m scripts.run_benchmark
```

Pipeline ingestion/indexing đầy đủ đã được chạy bằng script tương tác trong lịch sử thực nghiệm; các index A/B/C và trace hiện có được lưu trong `results/`.
