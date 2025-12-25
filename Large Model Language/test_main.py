"""
Pytest test suite cho Vietnamese Financial AI Agent API
Tests bao gồm: API liveness, company info, price queries, và technical indicators
"""

import pytest
import requests
import time


# Cấu hình
API_BASE_URL = "http://127.0.0.1:8000"
API_QUERY_URL = f"{API_BASE_URL}/query"


# Fixture để đảm bảo server đang chạy
@pytest.fixture(scope="session", autouse=True)
def check_server_running():
    """
    Kiểm tra server đang chạy trước khi run tests
    """
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.get(API_BASE_URL, timeout=2)
            if response.status_code == 200:
                print(f"\n✓ Server is running at {API_BASE_URL}")
                return
        except requests.exceptions.ConnectionError:
            if i < max_retries - 1:
                print(f"\n⏳ Waiting for server to start... (attempt {i+1}/{max_retries})")
                time.sleep(2)
            else:
                pytest.fail(
                    f"❌ Server is not running at {API_BASE_URL}. "
                    "Please start the server with: python main.py"
                )


def test_api_liveness():
    """
    Test Case 1: Kiểm tra API server đang hoạt động
    """
    response = requests.get(API_BASE_URL)
    
    assert response.status_code == 200, "Server should return 200 OK"
    
    data = response.json()
    assert data["status"] == "ok", "Server status should be 'ok'"
    assert data["api_key_configured"] == True, "API key should be configured"
    
    print("\n✓ Test 1 passed: API is alive and API key is configured")


def test_company_info_fpt():
    """
    Test Case 2: Test chức năng lấy thông tin công ty
    Kiểm tra agent có thể trả về thông tin về công ty FPT
    """
    payload = {"question": "Thong tin FPT?"}
    response = requests.post(API_QUERY_URL, json=payload)
    
    assert response.status_code == 200, "Request should succeed"
    
    data = response.json()
    assert "answer" in data, "Response should contain 'answer' field"
    
    answer = data["answer"]
    assert len(answer) > 0, "Answer should not be empty"
    assert "FPT" in answer, "Answer should mention FPT"
    
    # Kiểm tra có thông tin công ty
    assert any(keyword in answer for keyword in [
        "Công ty", "công ty", "phần mềm", "công nghệ", "thông tin", 
        "vốn", "niêm yết", "HOSE"
    ]), "Answer should contain company information"
    
    print(f"\n✓ Test 2 passed: Company info working")
    print(f"  Answer preview: {answer[:150]}...")


def test_price_vcb():
    """
    Test Case 3: Test chức năng lấy giá lịch sử
    Kiểm tra agent có thể trả về thông tin giá cổ phiếu VCB
    """
    payload = {"question": "Gia VCB 1 thang qua?"}
    response = requests.post(API_QUERY_URL, json=payload)
    
    assert response.status_code == 200, "Request should succeed"
    
    data = response.json()
    assert "answer" in data, "Response should contain 'answer' field"
    
    answer = data["answer"]
    assert len(answer) > 0, "Answer should not be empty"
    assert "VCB" in answer, "Answer should mention VCB"
    
    # Kiểm tra có thông tin về giá
    assert any(keyword in answer for keyword in [
        "giá", "đóng cửa", "mở cửa", "cao", "thấp", "biến động"
    ]), "Answer should contain price information"
    
    print(f"\n✓ Test 3 passed: Price query working")
    print(f"  Answer preview: {answer[:150]}...")


def test_price_hpg_with_timeframe():
    """
    Test Case 3b: Test với khoảng thời gian cụ thể
    """
    payload = {"question": "Gia co phieu HPG tu dau thang 10 den cuoi thang 10 nam 2024?"}
    response = requests.post(API_QUERY_URL, json=payload)
    
    assert response.status_code == 200, "Request should succeed"
    
    data = response.json()
    assert "answer" in data, "Response should contain 'answer' field"
    
    answer = data["answer"]
    assert "HPG" in answer, "Answer should mention HPG"
    
    print(f"\n✓ Test 3b passed: Price query with timeframe working")
    print(f"  Answer preview: {answer[:150]}...")


def test_indicator_rsi_hpg():
    """
    Test Case 4 (Bonus): Test chức năng tính chỉ báo kỹ thuật RSI
    Kiểm tra agent có thể tính và trả về RSI của HPG
    """
    payload = {"question": "Tinh RSI 14 ngay cua HPG?"}
    response = requests.post(API_QUERY_URL, json=payload)
    
    assert response.status_code == 200, "Request should succeed"
    
    data = response.json()
    assert "answer" in data, "Response should contain 'answer' field"
    
    answer = data["answer"]
    assert len(answer) > 0, "Answer should not be empty"
    assert "HPG" in answer, "Answer should mention HPG"
    assert "RSI" in answer, "Answer should mention RSI"
    
    # Kiểm tra có giá trị số (RSI value)
    import re
    numbers = re.findall(r'\d+\.?\d*', answer)
    assert len(numbers) > 0, "Answer should contain RSI value (a number)"
    
    print(f"\n✓ Test 4 passed: RSI calculation working")
    print(f"  Answer preview: {answer[:150]}...")


def test_indicator_sma_fpt():
    """
    Test Case 4b (Bonus): Test chức năng tính SMA
    """
    payload = {"question": "Tinh SMA 20 ngay cua FPT?"}
    response = requests.post(API_QUERY_URL, json=payload)
    
    assert response.status_code == 200, "Request should succeed"
    
    data = response.json()
    assert "answer" in data, "Response should contain 'answer' field"
    
    answer = data["answer"]
    assert "FPT" in answer, "Answer should mention FPT"
    assert "SMA" in answer, "Answer should mention SMA"
    
    print(f"\n✓ Test 4b passed: SMA calculation working")
    print(f"  Answer preview: {answer[:150]}...")


def test_invalid_empty_question():
    """
    Test Case 5: Test xử lý câu hỏi rỗng
    """
    payload = {"question": ""}
    response = requests.post(API_QUERY_URL, json=payload)
    
    assert response.status_code == 400, "Should return 400 for empty question"
    
    print("\n✓ Test 5 passed: Empty question handling working")


def test_invalid_ticker():
    """
    Test Case 6: Test xử lý mã cổ phiếu không tồn tại
    """
    payload = {"question": "Thong tin INVALID_TICKER?"}
    response = requests.post(API_QUERY_URL, json=payload)
    
    # Server vẫn trả về 200 nhưng answer sẽ chứa thông báo lỗi hoặc không tìm thấy
    assert response.status_code == 200, "Request should succeed even with invalid ticker"
    
    data = response.json()
    assert "answer" in data, "Response should contain 'answer' field"
    
    print("\n✓ Test 6 passed: Invalid ticker handling working")


if __name__ == "__main__":
    # Chạy tests với pytest
    pytest.main([__file__, "-v", "-s"])
