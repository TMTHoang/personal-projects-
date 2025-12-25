### **Giai đoạn 1: Thiết lập Môi trường & "Nháp" API**

Mục tiêu là đảm bảo bạn có thể cài đặt và gọi thành công API VnStock.

* `[ ]` Tạo thư mục dự án (ví dụ: `llm_financial_agent`).  
* `[ ]` Mở terminal, đi đến thư mục dự án.  
* `[ ]` Tạo môi trường ảo: `python -m venv venv`.  
* `[ ]` Kích hoạt môi trường ảo:  
  * Windows: `.\venv\Scripts\activate`  
  * macOS/Linux: `source venv/bin/activate`  
* `[ ]` Cài đặt các thư viện cơ bản: `pip install vnstock fastapi uvicorn google-generativeai pandas pandas_ta` (Tôi đề xuất `google-generativeai` cho Gemini, `fastapi` để làm API, và `pandas_ta` cho phần điểm cộng).  
* `[ ]` Tạo file `requirements.txt`: `pip freeze > requirements.txt`.  
* `[ ]` **(Quan trọng)** Tạo file `test_api.py` (file nháp, không phải file test tự động):  
  * Viết code import `vnstock`.  
  * **Thử nghiệm Chức năng 1 (Thông tin cty):**  
    * Gọi `company_overview('HPG')`.  
    * `print()` kết quả ra. Xem cấu trúc dữ liệu (sẽ là 1 pandas DataFrame).  
  * **Thử nghiệm Chức năng 2 (Giá lịch sử):**  
    * Gọi `stock_historical_data('FPT', '2024-01-01', '2024-06-01')`.  
    * `print()` kết quả. Xem cấu trúc dữ liệu (cũng là DataFrame).

---

### **Giai đoạn 2: Xây dựng "Tools" lõi**

Mục tiêu là tạo ra các hàm Python sạch sẽ, độc lập mà LLM có thể gọi.

* `[ ]` Tạo file `tools.py`.  
* `[ ]` Import `vnstock`, `pandas`, `pandas_ta` trong file `tools.py`.  
* `[ ]` **Tool 1: Lấy thông tin công ty:**  
  * Viết hàm `def get_company_info(ticker: str) -> str:`.  
  * Bên trong, gọi `company_overview(ticker)`.  
  * Thêm `try...except` để xử lý lỗi (ví dụ mã không tồn tại).  
  * Chuyển đổi DataFrame kết quả sang JSON: `result_json = df.to_json(orient='records')`.  
  * Trả về (return) `result_json`.  
* `[ ]` **Tool 2: Lấy giá lịch sử:**  
  * Viết hàm `def get_historical_price(ticker: str, start_date: str, end_date: str) -> str:`.  
  * Bên trong, gọi `stock_historical_data(ticker, start_date, end_date)`.  
  * Thêm `try...except` xử lý lỗi.  
  * Chuyển DataFrame sang JSON và trả về.  
* `[ ]` **Tool 3 (Bonus): Tính chỉ báo kỹ thuật:**  
  * Viết hàm `def calculate_technical_indicator(ticker: str, indicator_name: str, window_size: int, start_date: str, end_date: str) -> str:`.  
  * Bên trong, gọi `get_historical_price` (hàm bạn vừa viết) để lấy dữ liệu.  
  * Chuyển đổi JSON dữ liệu giá ngược lại DataFrame: `df = pd.read_json(...)`.  
  * Sử dụng `pandas_ta` để tính toán:  
    * Nếu `indicator_name == 'SMA'`: `df.ta.sma(length=window_size, append=True)`.  
    * Nếu `indicator_name == 'RSI'`: `df.ta.rsi(length=window_size, append=True)`.  
  * Lấy giá trị chỉ báo cuối cùng (`.iloc[-1]`) và trả về một chuỗi tường thuật (ví dụ: "Chỉ số RSI 14 ngày của FPT là 68.5").

---

### **Giai đoạn 3: Tích hợp LLM và Tạo Agent**

Đây là "bộ não" của hệ thống.

* `[ ]` Tạo file `agent.py`.  
* `[ ]` Import thư viện LLM (ví dụ: `import google.generativeai as genai`) và các hàm từ `tools.py`.  
* `[ ]` **Định nghĩa Tools cho LLM (Function Calling):**  
  * Định nghĩa cấu trúc (schema) của 3 hàm `get_company_info`, `get_historical_price`, `calculate_technical_indicator` theo định dạng mà LLM yêu cầu. (Ví dụ: đối với Gemini, bạn tạo các đối tượng `Tool` và `FunctionDeclaration`).  
  * **Rất quan trọng:** Viết mô tả (description) thật rõ ràng cho từng hàm và từng tham số. (Ví dụ: "Sử dụng hàm này để lấy giá lịch sử. Cần mã 'ticker', ngày bắt đầu 'start\_date' và ngày kết thúc 'end\_date'").  
* `[ ]` **Viết System Prompt:**  
  * Tạo một biến `SYSTEM_PROMPT` (chuỗi `str`).  
  * Nội dung: "Bạn là một trợ lý tài chính chuyên nghiệp tại thị trường Việt Nam. Bạn trả lời bằng tiếng Việt. Bạn chỉ được trả lời dựa trên thông tin từ các công cụ (tools) được cung cấp. Nếu người dùng hỏi về giá mà không nói rõ ngày, hãy tự động lấy 3 tháng gần nhất."  
* `[ ]` **Viết Hàm Chạy Agent (Vòng lặp Function Calling):**  
  * Viết hàm `def run_agent_query(question: str) -> str:`.  
  * Bên trong hàm:  
    1. Khởi tạo model (ví dụ: Gemini) với `system_prompt` và danh sách `tools`.  
    2. Bắt đầu chat: `chat = model.start_chat()`.  
    3. Gửi câu hỏi của người dùng: `response = chat.send_message(question)`.  
    4. Viết một vòng lặp `while` để xử lý function calling:  
       * Kiểm tra xem `response` có yêu cầu gọi hàm không.  
       * Nếu có: Lấy tên hàm (ví dụ: `get_historical_price`) và các tham số (ví dụ: `{'ticker': 'FPT', ...}`).  
       * Gọi hàm Python tương ứng từ `tools.py`: `result = get_historical_price(**args)`.  
       * Gửi kết quả `result` này ngược lại cho LLM (với `role='function'`).  
       * Lấy `response` mới.  
       * Nếu không (LLM đã sẵn sàng trả lời): Thoát vòng lặp.  
    5. Trả về câu trả lời cuối cùng: `return response.text`.

---

### **Giai đoạn 4: Triển khai REST API**

"Bọc" Agent của bạn lại để thế giới bên ngoài có thể gọi.

* `[ ]` Tạo file `main.py`.  
* `[ ]` Import `FastAPI`, `uvicorn` và các class `BaseModel` từ `pydantic`.  
* `[ ]` Import hàm `run_agent_query` từ `agent.py`.  
* `[ ]` Khởi tạo app: `app = FastAPI()`.  
* `[ ]` **Định nghĩa Models (Input/Output):**  
  * `class QueryRequest(BaseModel): question: str`  
  * `class QueryResponse(BaseModel): answer: str`  
* `[ ]` **Tạo Endpoint API:**  
  * Viết `@app.post("/query", response_model=QueryResponse)`  
  * Viết hàm `async def handle_query(request: QueryRequest):`  
  * Bên trong:  
    * Gọi agent: `answer_text = run_agent_query(request.question)` (Lưu ý: Nếu `run_agent_query` tốn thời gian, bạn nên chạy nó bất đồng bộ).  
    * Trả về theo đúng format: `return QueryResponse(answer=answer_text)`.  
* `[ ]` **Chạy Server:**  
  * Thêm vào cuối `main.py`: `if __name__ == "__main__": uvicorn.run(app, host="0.0.0.0", port=8000)`.  
  * Chạy server từ terminal: `python main.py`.  
* `[ ]` **Thử nghiệm thủ công:** Dùng Postman hoặc `curl` để gửi 1 request POST đến `http://127.0.0.1:8000/query` với JSON `{"question": "Thông tin mã VCB?"}` và xem kết quả.

---

### **Giai đoạn 5: Xây dựng Test Tự động**

Đảm bảo Agent chạy đúng và đáp ứng yêu cầu đánh giá.

* `[ ]` Cài đặt `pytest` và `requests`: `pip install pytest requests`.  
* `[ ]` Tạo file `test_main.py` (pytest sẽ tự động nhận diện file này).  
* `[ ]` Import `pytest`, `requests`.  
* `[ ]` Định nghĩa `API_URL = "http://127.0.0.1:8000/query"`.  
* `[ ]` Lấy danh sách câu hỏi test từ file "AI Intern test questions".  
* `[ ]` **Viết Test Case 1 (Test API hoạt động):**  
  * `def test_api_liveness():`  
  * Gửi một request đơn giản.  
  * `assert response.status_code == 200`.  
* `[ ]` **Viết Test Case 2 (Test chức năng Info):**  
  * `def test_company_info_fpt():`  
  * `payload = {"question": "Thông tin FPT?"}`  
  * `response = requests.post(API_URL, json=payload)`  
  * `data = response.json()`  
  * `assert "answer" in data`  
  * `assert "FPT" in data["answer"]` (Kiểm tra từ khóa cơ bản).  
* `[ ]` **Viết Test Case 3 (Test chức năng Giá):**  
  * `def test_price_vcb():`  
  * `payload = {"question": "Giá VCB 1 tháng qua?"}`  
  * `response = requests.post(API_URL, json=payload)`  
  * `data = response.json()`  
  * `assert "VCB" in data["answer"]`.  
* `[ ]` **Viết Test Case 4 (Test Bonus RSI):**  
  * `def test_indicator_rsi_hpg():`  
  * `payload = {"question": "Tính RSI 14 ngày của HPG?"}`  
  * `response = requests.post(API_URL, json=payload)`  
  * `data = response.json()`  
  * `assert "RSI" in data["answer"] and "HPG" in data["answer"]`.  
* `[ ]` **Chạy Test:**  
  * Mở terminal 1: Chạy API của bạn: `python main.py`.  
  * Mở terminal 2: Chạy test: `pytest`.

