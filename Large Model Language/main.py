"""
FastAPI REST API Server cho Vietnamese Financial AI Agent
Endpoint /query nhận câu hỏi và trả về câu trả lời từ agent
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from agent import run_agent_query


# Khởi tạo FastAPI app
app = FastAPI(
    title="Vietnamese Financial AI Agent API",
    description="API để truy vấn thông tin chứng khoán Việt Nam sử dụng AI Agent",
    version="1.0.0"
)

# Thêm CORS middleware để cho phép gọi API từ browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên giới hạn cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Định nghĩa Models cho Input/Output
class QueryRequest(BaseModel):
    """Request model cho endpoint /query"""
    question: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Thông tin về công ty FPT?"
            }
        }


class QueryResponse(BaseModel):
    """Response model cho endpoint /query"""
    answer: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "FPT là Công ty Cổ phần FPT, hoạt động trong lĩnh vực công nghệ thông tin..."
            }
        }


# Health check endpoint
@app.get("/")
async def root():
    """
    Health check endpoint
    """
    return {
        "status": "ok",
        "message": "Vietnamese Financial AI Agent API is running",
        "api_key_configured": bool(os.getenv("GEMINI_API_KEY"))
    }


# Main query endpoint
@app.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """
    Xử lý câu hỏi về chứng khoán Việt Nam
    
    Args:
        request: QueryRequest chứa câu hỏi của người dùng
    
    Returns:
        QueryResponse chứa câu trả lời từ AI agent
    
    Example:
        POST /query
        {"question": "Thông tin FPT?"}
        
        Response:
        {"answer": "FPT là Công ty Cổ phần..."}
    """
    try:
        # Kiểm tra API key
        if not os.getenv("GEMINI_API_KEY"):
            raise HTTPException(
                status_code=500,
                detail="Chưa cấu hình GEMINI_API_KEY. Vui lòng thiết lập biến môi trường."
            )
        
        # Kiểm tra input
        if not request.question or len(request.question.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Câu hỏi không được để trống"
            )
        
        # Gọi agent để xử lý câu hỏi
        answer_text = run_agent_query(request.question)
        
        # Kiểm tra kết quả
        if not answer_text:
            raise HTTPException(
                status_code=500,
                detail="Agent không trả về kết quả"
            )
        
        # Kiểm tra nếu có lỗi trong response
        if answer_text.startswith("Lỗi:"):
            raise HTTPException(
                status_code=500,
                detail=answer_text
            )
        
        return QueryResponse(answer=answer_text)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi xử lý câu hỏi: {str(e)}"
        )


# Chạy server
if __name__ == "__main__":
    # Kiểm tra API key trước khi chạy
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  CẢNH BÁO: Chưa thiết lập GEMINI_API_KEY")
        print("Vui lòng chạy: $env:GEMINI_API_KEY='your-api-key'")
        print("\nServer vẫn sẽ chạy nhưng không thể xử lý requests.\n")
    else:
        print("✓ GEMINI_API_KEY đã được cấu hình")
    
    print("\n" + "="*60)
    print(" Starting Vietnamese Financial AI Agent API Server")
    print("="*60)
    print(" Server URL: http://127.0.0.1:8000")
    print(" API Docs: http://127.0.0.1:8000/docs")
    print(" ReDoc: http://127.0.0.1:8000/redoc")
    print("="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
