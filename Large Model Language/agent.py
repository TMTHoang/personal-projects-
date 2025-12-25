"""
Agent tích hợp LLM (Google Gemini) với function calling
Điều phối giữa LLM và các tools từ tools.py
"""

import os
import google.generativeai as genai
from datetime import datetime, timedelta
from tools import get_company_info, get_historical_price, calculate_technical_indicator


# Cấu hình API key (cần thiết lập biến môi trường GEMINI_API_KEY)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


# System Prompt cho agent
SYSTEM_PROMPT = """Bạn là một trợ lý tài chính chuyên nghiệp tại thị trường chứng khoán Việt Nam.

Nhiệm vụ của bạn:
- Trả lời các câu hỏi về thị trường chứng khoán Việt Nam bằng tiếng Việt
- Chỉ sử dụng thông tin từ các công cụ (tools) được cung cấp
- Không bịa đặt hoặc suy đoán thông tin không có trong dữ liệu

Quy tắc quan trọng:
- Nếu người dùng hỏi về giá mà không nói rõ khoảng thời gian, tự động lấy dữ liệu 3 tháng gần nhất
- Nếu người dùng hỏi về chỉ báo kỹ thuật mà không nói rõ thời gian, tự động lấy 3 tháng gần nhất
- Luôn trả lời bằng tiếng Việt, rõ ràng và chuyên nghiệp
- Khi trả về giá, hãy tóm tắt xu hướng và thông tin quan trọng thay vì liệt kê toàn bộ dữ liệu
"""


# Định nghĩa Tools schema cho Gemini Function Calling
get_company_info_func = genai.protos.FunctionDeclaration(
    name="get_company_info",
    description="Lấy thông tin tổng quan về một công ty niêm yết trên thị trường chứng khoán Việt Nam. Bao gồm các thông tin như tên công ty, ngành nghề, vốn điều lệ, lịch sử hình thành, v.v.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "ticker": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Mã chứng khoán của công ty (ví dụ: 'FPT', 'VCB', 'HPG', 'VNM'). Viết hoa tất cả các ký tự."
            )
        },
        required=["ticker"]
    )
)

get_historical_price_func = genai.protos.FunctionDeclaration(
    name="get_historical_price",
    description="Lấy dữ liệu giá lịch sử của một cổ phiếu trong khoảng thời gian cụ thể. Trả về thông tin giá mở cửa, đóng cửa, cao nhất, thấp nhất và khối lượng giao dịch theo từng ngày.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "ticker": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Mã chứng khoán của công ty (ví dụ: 'FPT', 'VCB', 'HPG')"
            ),
            "start_date": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Ngày bắt đầu lấy dữ liệu, định dạng 'YYYY-MM-DD' (ví dụ: '2024-01-01')"
            ),
            "end_date": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Ngày kết thúc lấy dữ liệu, định dạng 'YYYY-MM-DD' (ví dụ: '2024-12-31')"
            )
        },
        required=["ticker", "start_date", "end_date"]
    )
)

calculate_technical_indicator_func = genai.protos.FunctionDeclaration(
    name="calculate_technical_indicator",
    description="Tính toán các chỉ báo kỹ thuật phân tích cổ phiếu. Hỗ trợ SMA (Simple Moving Average - Đường trung bình động đơn giản) và RSI (Relative Strength Index - Chỉ số sức mạnh tương đối).",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "ticker": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Mã chứng khoán của công ty (ví dụ: 'FPT', 'VCB', 'HPG')"
            ),
            "indicator_name": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Tên chỉ báo cần tính. Chỉ hỗ trợ 'SMA' hoặc 'RSI'"
            ),
            "window_size": genai.protos.Schema(
                type=genai.protos.Type.INTEGER,
                description="Độ dài chu kỳ tính toán (ví dụ: 14 cho RSI 14 ngày, 20 cho SMA 20 ngày)"
            ),
            "start_date": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Ngày bắt đầu lấy dữ liệu, định dạng 'YYYY-MM-DD'"
            ),
            "end_date": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Ngày kết thúc lấy dữ liệu, định dạng 'YYYY-MM-DD'"
            )
        },
        required=["ticker", "indicator_name", "window_size", "start_date", "end_date"]
    )
)

# Tạo Tool object
financial_tool = genai.protos.Tool(
    function_declarations=[
        get_company_info_func,
        get_historical_price_func,
        calculate_technical_indicator_func
    ]
)


# Map tên hàm đến function thực tế
AVAILABLE_FUNCTIONS = {
    "get_company_info": get_company_info,
    "get_historical_price": get_historical_price,
    "calculate_technical_indicator": calculate_technical_indicator
}


def run_agent_query(question: str) -> str:
    """
    Chạy agent với câu hỏi từ người dùng
    
    Args:
        question: Câu hỏi của người dùng
    
    Returns:
        Câu trả lời từ agent
    """
    if not GEMINI_API_KEY:
        return "Lỗi: Chưa cấu hình GEMINI_API_KEY. Vui lòng thiết lập biến môi trường GEMINI_API_KEY với API key của bạn."
    
    try:
        # Khởi tạo model với tools
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            tools=[financial_tool],
            system_instruction=SYSTEM_PROMPT
        )
        
        # Bắt đầu chat session
        chat = model.start_chat(enable_automatic_function_calling=False)
        
        # Gửi câu hỏi người dùng
        response = chat.send_message(question)
        
        # Vòng lặp xử lý function calling
        max_iterations = 10  # Giới hạn số lần gọi để tránh vòng lặp vô hạn
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Kiểm tra xem có function call không
            if not response.candidates:
                return "Lỗi: Không nhận được phản hồi từ model"
            
            candidate = response.candidates[0]
            
            # Nếu model trả về text (không có function call), trả về kết quả
            if candidate.content.parts and candidate.content.parts[0].text:
                return candidate.content.parts[0].text
            
            # Nếu có function call
            if candidate.content.parts and hasattr(candidate.content.parts[0], 'function_call'):
                function_call = candidate.content.parts[0].function_call
                function_name = function_call.name
                function_args = dict(function_call.args)
                
                print(f"[DEBUG] Gọi function: {function_name} với args: {function_args}")
                
                # Gọi function tương ứng
                if function_name in AVAILABLE_FUNCTIONS:
                    function_to_call = AVAILABLE_FUNCTIONS[function_name]
                    function_result = function_to_call(**function_args)
                    
                    print(f"[DEBUG] Kết quả function: {function_result[:200]}...")
                    
                    # Gửi kết quả về cho model
                    response = chat.send_message(
                        genai.protos.Content(
                            parts=[genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=function_name,
                                    response={'result': function_result}
                                )
                            )]
                        )
                    )
                else:
                    return f"Lỗi: Function '{function_name}' không được hỗ trợ"
            else:
                # Không có function call và không có text
                break
        
        # Nếu vượt quá số lần lặp
        if iteration >= max_iterations:
            return "Lỗi: Đã vượt quá số lần gọi function tối đa"
        
        return "Lỗi: Không thể xử lý câu hỏi"
        
    except Exception as e:
        return f"Lỗi khi chạy agent: {str(e)}"


# Test agent
if __name__ == "__main__":
    print("=" * 60)
    print("TEST AGENT - Vietnamese Financial AI")
    print("=" * 60)
    
    # Kiểm tra API key
    if not GEMINI_API_KEY:
        print("\n⚠️  CẢNH BÁO: Chưa có GEMINI_API_KEY")
        print("Vui lòng thiết lập biến môi trường:")
        print('$env:GEMINI_API_KEY="your-api-key-here"')
        print("\nHoặc trong code:")
        print('os.environ["GEMINI_API_KEY"] = "your-api-key-here"')
    else:
        print(f"\n✓ API Key đã được cấu hình: {GEMINI_API_KEY[:10]}...")
        
        # Test với câu hỏi mẫu
        test_questions = [
            "Thông tin về công ty FPT?",
            "Giá cổ phiếu VCB 1 tháng gần nhất?",
            "Tính RSI 14 ngày của HPG?"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n{'='*60}")
            print(f"Test {i}: {question}")
            print('='*60)
            answer = run_agent_query(question)
            print(f"Trả lời: {answer}")
